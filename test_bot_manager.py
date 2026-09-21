import os
import unittest
from unittest.mock import patch

import bot_manager
import config


class FakeStopEvent:
    def __init__(self, stop_after_waits):
        self.stop_after_waits = stop_after_waits
        self.wait_count = 0
        self.calls = []

    def is_set(self):
        return False

    def wait(self, timeout):
        self.wait_count += 1
        self.calls.append(("wait", timeout))
        return self.wait_count >= self.stop_after_waits


class ReminderSchedulingTests(unittest.TestCase):
    def test_reminder_interval_rejects_values_below_one_minute(self):
        with patch.dict(
            os.environ,
            {"FUEL_BOT_REMINDER_INTERVAL_SECONDS": "0"},
        ):
            with self.assertRaisesRegex(RuntimeError, "must be at least 60"):
                config._read_reminder_interval_seconds()

    def test_stripe_reminder_waits_before_first_message(self):
        stop_event = FakeStopEvent(stop_after_waits=2)
        calls = stop_event.calls

        with (
            patch.object(bot_manager, "_stop_event", stop_event),
            patch.object(bot_manager, "FUEL_BOT_REMINDER_INTERVAL_SECONDS", 1800),
            patch.object(bot_manager, "send", lambda message: calls.append(("send", message))),
        ):
            bot_manager.fuel_bot_reminder()

        self.assertEqual(calls[0], ("wait", 2000))
        self.assertEqual(calls[1][0], "send")
        self.assertIn(bot_manager.STRIPE_PAYMENT_LINK, calls[1][1])
        self.assertEqual(calls[2], ("wait", 1800))

    def test_heartbeat_does_not_send_stripe_reminder(self):
        stop_event = FakeStopEvent(stop_after_waits=1)
        sent_messages = []

        with (
            patch.object(bot_manager, "_stop_event", stop_event),
            patch.object(bot_manager, "send", sent_messages.append),
            patch.object(bot_manager, "clear_seen_jobs"),
        ):
            bot_manager.heartbeat()

        self.assertEqual(len(sent_messages), 1)
        self.assertIn("BOT LIVE", sent_messages[0])
        self.assertNotIn(bot_manager.STRIPE_PAYMENT_LINK, sent_messages[0])


if __name__ == "__main__":
    unittest.main()
