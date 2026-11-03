"""Calculation, coverage, input-integrity and CSV regression tests for D01."""

from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"solution/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


audit = load_module("audit_data")
acquisition = load_module("acquire_data")


class AuditTests(unittest.TestCase):
    def test_quantiles_have_known_values_and_empty_population(self):
        self.assertEqual(audit.quantile([4, 1, 3, 2], .5), 2.5)
        self.assertEqual(audit.quantile([4, 1, 3, 2], .95), 3.85)
        self.assertIsNone(audit.quantile([], .5))
        self.assertEqual(audit.quantile([3], .95), 3)

    def test_coverage_and_negative_intervals_keep_correct_denominators(self):
        def row(status, first="", resolution="", rating=""):
            return {**dict.fromkeys(audit.CUSTOMER_COLUMNS, ""),
                    "Ticket ID": str(first), "Ticket Status": status,
                    "First Response Time": first, "Time to Resolution": resolution,
                    "Customer Satisfaction Rating": rating}
        rows = [row("Closed", "2023-01-01 12:00:00", "2023-01-01 13:00:00", "4"),
                row("Closed", "2023-01-01 12:00:00", "2023-01-01 11:00:00"), row("Open")]
        result = audit.customer_audit(rows)
        self.assertEqual(result["satisfaction"]["observed"], 1)
        self.assertEqual(result["satisfaction"]["closed_rows"], 2)
        self.assertEqual(result["satisfaction"]["total_rows"], 3)
        self.assertEqual(result["time_fields"]["paired_rows"], 2)
        self.assertEqual(result["time_fields"]["resolution_before_first_response"], 1)
        self.assertEqual(result["time_fields"]["response_to_resolution_hours_all_pairs"]["median"], 0)
        self.assertEqual(result["time_fields"]["response_to_resolution_hours_nonnegative_only"]["n"], 1)
        self.assertFalse(result["time_fields"]["full_resolution_duration_identifiable"])

    def test_normalized_duplicates_detect_label_conflicts_and_ignore_blanks(self):
        rows = [{"Document": "Ａ  test", "Topic_group": "Hardware"},
                {"Document": "a test", "Topic_group": "Access"},
                {"Document": "another", "Topic_group": "Hardware"},
                {"Document": " \t", "Topic_group": "Access"}]
        result = audit.text_profile(rows, "Document", "Topic_group")
        self.assertEqual(result["nonempty_rows"], 3)
        self.assertEqual(result["normalized_duplicate_excess_rows"], 1)
        self.assertEqual(result["conflicting_label_groups"], 1)
        self.assertEqual(result["rows_in_conflicting_label_groups"], 2)

    def test_invalid_timestamp_nonfinite_number_and_rating_are_counted(self):
        self.assertIsNone(audit.timestamp("2023-02-30 12:00:00"))
        self.assertIsNone(audit.number("NaN"))
        self.assertIsNone(audit.number("inf"))
        rows = [{**dict.fromkeys(audit.CUSTOMER_COLUMNS, ""),
                 "Ticket Status": "Closed", "Customer Satisfaction Rating": "6.5"}]
        self.assertEqual(audit.customer_audit(rows)["satisfaction"]["outside_integer_1_to_5_or_invalid"], 1)

    def test_malformed_csv_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "data.csv"
            path.write_text("Document,Topic_group\nhello,Hardware,extra\n")
            with self.assertRaisesRegex(ValueError, "Malformed CSV"):
                audit.read_csv(path, ["Document", "Topic_group"])

    def test_audit_refuses_changed_raw_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "data").mkdir()
            path = root / "data/tickets.csv"
            path.write_text("Document,Topic_group\nhello,Hardware\n")
            manifest = {"datasets": {"customer_support": {
                "file": {"path": "data/tickets.csv", "sha256": audit.sha256(path)}}}}
            (root / "data/manifest.json").write_text(json.dumps(manifest))
            path.write_text("Document,Topic_group\nchanged,Hardware\n")
            with self.assertRaisesRegex(ValueError, "hash differs"):
                audit.audit(root)


class AcquisitionTests(unittest.TestCase):
    def test_existing_raw_csv_is_never_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = root / "data/raw"
            raw.mkdir(parents=True)
            archive = raw / "customer_support-v1.zip"
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr("source.csv", "original\n")
            path = raw / "customer_support-v1.csv"
            path.write_text("modified raw data\n")
            reference = root / "reference.csv"
            reference.write_text("original\n")
            manifest_path = root / "data/manifest.json"
            manifest_path.write_text(json.dumps({"schema_version": 1, "datasets": {"customer_support": {
                "version": 1,
                "archive": {"sha256": acquisition.sha256(archive)},
                "file": {"zip_member": "source.csv", "sha256": acquisition.sha256(reference)}}}}))
            with patch.object(acquisition, "ROOT", root), patch.object(acquisition, "MANIFEST", manifest_path), \
                    patch.object(acquisition, "SOURCES", {"customer_support": acquisition.SOURCES["customer_support"]}):
                with self.assertRaisesRegex(ValueError, "refusing to overwrite"), redirect_stdout(io.StringIO()):
                    acquisition.acquire()
            self.assertEqual(path.read_text(), "modified raw data\n")

    def test_incomplete_manifest_is_rejected_before_downloading(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest = Path(temporary) / "manifest.json"
            manifest.write_text(json.dumps({"schema_version": 1, "datasets": {}}))
            with patch.object(acquisition, "MANIFEST", manifest), patch.object(acquisition, "download") as download:
                with self.assertRaisesRegex(ValueError, "must lock both"):
                    acquisition.acquire()
                download.assert_not_called()


if __name__ == "__main__":
    unittest.main()
