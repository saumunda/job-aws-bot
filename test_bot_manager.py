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


class HourlyJobCacheTests(unittest.TestCase):
    def test_heartbeat_clears_jobs_after_one_hour_without_posting(self):
        stop_event = FakeStopEvent(stop_after_waits=1)
        clear_calls = []

        with (
            patch.object(bot_manager, "_stop_event", stop_event),
            patch.object(bot_manager, "clear_seen_jobs", lambda: clear_calls.append(True)),
        ):
            bot_manager.heartbeat()

        self.assertEqual(stop_event.calls, [("wait", config.HEARTBEAT_INTERVAL)])
        self.assertEqual(clear_calls, [])

        stop_event = FakeStopEvent(stop_after_waits=2)
        with (
            patch.object(bot_manager, "_stop_event", stop_event),
            patch.object(bot_manager, "clear_seen_jobs", lambda: clear_calls.append(True)),
        ):
            bot_manager.heartbeat()

        self.assertEqual(stop_event.calls, [("wait", config.HEARTBEAT_INTERVAL)] * 2)
        self.assertEqual(clear_calls, [True])


if __name__ == "__main__":
    unittest.main()
