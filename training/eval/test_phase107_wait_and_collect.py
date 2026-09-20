import unittest

from phase107_wait_and_collect import accounting_state, is_terminal_state


class SlurmStateTests(unittest.TestCase):
    def test_parses_first_accounting_state(self):
        self.assertEqual(accounting_state("FAILED 00:00:03\n"), "FAILED")

    def test_empty_accounting_output_is_unknown(self):
        self.assertEqual(accounting_state("  \n"), "unknown")

    def test_distinguishes_live_queue_states_from_terminal_states(self):
        for state in ("PENDING", "CONFIGURING", "RUNNING", "COMPLETING", "unknown"):
            with self.subTest(state=state):
                self.assertFalse(is_terminal_state(state))
        for state in ("FAILED", "CANCELLED", "COMPLETED", "TIMEOUT"):
            with self.subTest(state=state):
                self.assertTrue(is_terminal_state(state))


if __name__ == "__main__":
    unittest.main()
