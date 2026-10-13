import unittest
from datetime import date, timedelta


class ReminderHistoryTests(unittest.TestCase):
    def test_successful_launch_increments_once_and_keeps_three_distinct_dates(self):
        from reminder_policy import record_successful_launch

        state = {}
        days = [date(2026, 10, 1), date(2026, 10, 1), date(2026, 10, 2), date(2026, 10, 3), date(2026, 10, 4)]
        for today in days:
            state = record_successful_launch(state, today)
        self.assertEqual(state["launch_count"], 5)
        self.assertEqual(state["distinct_dates"], ["2026-10-02", "2026-10-03", "2026-10-04"])
        self.assertEqual(state["next_rating_launch"], 5)
        self.assertEqual(state["next_support_launch"], 11)

    def test_malformed_state_is_normalised_without_mutating_input(self):
        from reminder_policy import record_successful_launch

        original = {"launch_count": "bad", "distinct_dates": 42, "rating_disabled": "yes", "extra": "keep outside"}
        result = record_successful_launch(original, date(2026, 10, 13))
        self.assertEqual(result["launch_count"], 1)
        self.assertEqual(result["distinct_dates"], ["2026-10-13"])
        self.assertTrue(result["rating_disabled"])
        self.assertEqual(original["launch_count"], "bad")


class ReminderPolicyTests(unittest.TestCase):
    def state(self, launches=0, dates=(), **changes):
        value = {
            "launch_count": launches,
            "distinct_dates": list(dates),
            "next_rating_launch": 5,
            "rating_disabled": False,
            "next_support_launch": 11,
            "support_disabled": False,
        }
        value.update(changes)
        return value

    def test_rating_requires_five_launches_and_three_days(self):
        from reminder_policy import eligible_reminder

        self.assertIsNone(eligible_reminder(self.state(5, ("2026-10-01", "2026-10-02"))))
        self.assertIsNone(eligible_reminder(self.state(4, ("2026-10-01", "2026-10-02", "2026-10-03"))))
        self.assertEqual(eligible_reminder(self.state(5, ("2026-10-01", "2026-10-02", "2026-10-03"))), "rating")

    def test_support_begins_at_eleven_and_rating_has_priority(self):
        from reminder_policy import eligible_reminder

        self.assertEqual(eligible_reminder(self.state(11, ("2026-10-01",))), "support")
        both = self.state(11, ("2026-10-01", "2026-10-02", "2026-10-03"))
        self.assertEqual(eligible_reminder(both), "rating")
        self.assertEqual(both["next_support_launch"], 11)

    def test_postpone_and_close_use_exact_intervals(self):
        from reminder_policy import apply_reminder_choice

        rating = apply_reminder_choice(self.state(7), "rating", "later")
        self.assertEqual(rating["next_rating_launch"], 17)
        rating_closed = apply_reminder_choice(self.state(8), "rating", "close")
        self.assertEqual(rating_closed["next_rating_launch"], 18)
        support = apply_reminder_choice(self.state(11), "support", "later")
        self.assertEqual(support["next_support_launch"], 22)
        support_closed = apply_reminder_choice(self.state(12), "support", "close")
        self.assertEqual(support_closed["next_support_launch"], 23)

    def test_open_or_never_permanently_disables_automatic_prompt(self):
        from reminder_policy import apply_reminder_choice, eligible_reminder

        for reminder, choice in (("rating", "rate"), ("rating", "never"), ("support", "open"), ("support", "never")):
            with self.subTest(reminder=reminder, choice=choice):
                state = apply_reminder_choice(self.state(30, ("2026-10-01", "2026-10-02", "2026-10-03")), reminder, choice)
                self.assertTrue(state[f"{reminder}_disabled"])
                if reminder == "rating":
                    state["support_disabled"] = True
                else:
                    state["rating_disabled"] = True
                self.assertIsNone(eligible_reminder(state))

    def test_reenable_schedules_from_current_launch_without_fabricating_dates(self):
        from reminder_policy import set_reminder_enabled

        start = self.state(20, ("2026-10-01",), rating_disabled=True, support_disabled=True)
        rating = set_reminder_enabled(start, "rating", True)
        self.assertFalse(rating["rating_disabled"])
        self.assertEqual(rating["next_rating_launch"], 30)
        self.assertEqual(rating["distinct_dates"], ["2026-10-01"])
        support = set_reminder_enabled(start, "support", True)
        self.assertFalse(support["support_disabled"])
        self.assertEqual(support["next_support_launch"], 31)

    def test_disable_is_independent(self):
        from reminder_policy import set_reminder_enabled

        state = set_reminder_enabled(self.state(5), "rating", False)
        self.assertTrue(state["rating_disabled"])
        self.assertFalse(state["support_disabled"])


if __name__ == "__main__":
    unittest.main()
