import inspect
import unittest
from unittest.mock import patch

from qt_Port import Port
from qt_uart import QtSerial


class _ReadStub:
    def __init__(self, failures):
        self.failures = failures
        self.calls = 0

    def read(self, key):
        self.calls += 1
        if self.calls <= self.failures:
            raise RuntimeError(f"offline: {key}")
        return b"done"

    def readv(self, key):
        return self.read(key)


class QtSerialRetryTests(unittest.TestCase):
    def test_default_timeout_is_fifty_milliseconds(self):
        timeout = inspect.signature(QtSerial).parameters["timeout"].default
        self.assertEqual(timeout, 0.05)

    @patch("qt_Port.time.sleep", return_value=None)
    def test_register_read_retries_four_times_then_stops(self, _sleep):
        module = _ReadStub(failures=10)

        with self.assertRaisesRegex(RuntimeError, "after 4 attempts"):
            Port.read_module_value(module, "gain_p", retries=4)

        self.assertEqual(module.calls, 4)

    @patch("qt_Port.time.sleep", return_value=None)
    def test_register_read_can_recover_within_retry_budget(self, _sleep):
        module = _ReadStub(failures=2)

        value = Port.read_module_value(module, "gain_p", use_readv=True, retries=4)

        self.assertEqual(value, b"done")
        self.assertEqual(module.calls, 3)


if __name__ == "__main__":
    unittest.main()
