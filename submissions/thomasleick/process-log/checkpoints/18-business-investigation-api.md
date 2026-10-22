CHECKPOINT: 18 — Business investigation API
STATUS: PASS
OBJECTIVE: Expose the generated business-driver findings through a validated API contract while retaining the existing analysis and scenario endpoints.
WORK COMPLETED: Added `/api/business-investigation`; added a Pydantic response model; packaged the generated JSON artifact in the API image; added endpoint coverage for label totals, cohort non-identifiability, interval usage, duplicate sensitivity, account candidates and UNKNOWN revenue.
FILES CREATED: This checkpoint.
FILES MODIFIED: `solution/apps/api/src/main.py`; `solution/apps/api/src/schemas/contracts.py`; `solution/apps/api/Dockerfile`; `solution/apps/api/tests/test_api.py`.
COMMANDS EXECUTED: `docker build --target test -t ravenstack-remediation-api-test:local -f apps/api/Dockerfile .`; `docker run --rm --entrypoint pytest ravenstack-remediation-api-test:local -q`.
TESTS EXECUTED: API tests inside the Python 3.12 test image, including scenario validation and new business endpoint contract.
TEST RESULTS: API image built successfully; 13 tests passed, 1 upstream Starlette/AnyIO deprecation warning. This is a test-image result, not yet integrated Docker Compose runtime proof.
EVIDENCE LEVEL: UNIT / SYNTHETIC CONTRACT, INTEGRATION (FastAPI TestClient in container).
BUSINESS FINDINGS: API serves values from the reproducibly generated source-data artifact. Cohort status is NOT_IDENTIFIABLE and financial exposure is null/UNKNOWN; no placeholder figures are returned.
UNKNOWN: Live Compose API currently still reflects the existing build until the authorized project-only rebuild later in the mission.
BLOCKERS: None.
RISKS: The API artifact is generated during analysis and copied into the image; evaluators changing raw CSVs must rerun the documented analysis command before rebuilding. No out-of-band data store is used.
NEXT STEP: Render acquisition, support, usage, cohort, account and recommendation evidence within the four existing frontend chapters.
