"""Tests para ganchos de venda e next best action."""
from __future__ import annotations

import unittest

from sales_hooks import get_next_best_action, get_sales_hooks


class SalesHooksTests(unittest.TestCase):
    def test_hooks_contract_and_priority(self) -> None:
        profile = {"disc_profile": "C", "owner": "Ana", "deal_stage": "Prospecting"}
        hooks = get_sales_hooks(profile)

        self.assertGreaterEqual(len(hooks), 3)
        self.assertLessEqual(len(hooks), 5)

        priorities = [h["priority"] for h in hooks]
        self.assertEqual(priorities, sorted(priorities))

        for hook in hooks:
            self.assertIn("hook", hook)
            self.assertIn("why_it_works", hook)
            self.assertIn("opening_question", hook)
            self.assertIn("risk_if_badly_used", hook)

    def test_next_best_action_never_empty(self) -> None:
        profile = {"disc_profile": "indefinido", "owner": "Ana", "deal_stage": "Engaging"}
        hooks = get_sales_hooks(profile)
        action = get_next_best_action(profile, hooks)
        self.assertTrue(action.strip())


if __name__ == "__main__":
    unittest.main()
