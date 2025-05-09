import unittest

from robot.model import BodyItem
from robot.output import LOGGER
from robot.output.listeners import Listeners
from robot.running.outputcapture import OutputCapturer
from robot.utils import DotDict
from robot.utils.asserts import assert_equal

LOGGER.unregister_console_logger()


class Mock:
    non_existing = ()

    def __getattr__(self, name):
        if name[:2] == "__" or name in self.non_existing:
            raise AttributeError
        return ""


class SuiteMock(Mock):

    def __init__(self, is_result=False):
        self.name = "suitemock"
        self.tests = self.suites = []
        if is_result:
            self.doc = "somedoc"
            self.status = "PASS"

    stat_message = "stat message"
    full_message = "full message"


class TestMock(Mock):

    def __init__(self, is_result=False):
        self.name = "testmock"
        self.data = DotDict({"name": self.name})
        if is_result:
            self.doc = "cod"
            self.tags = ["foo", "bar"]
            self.message = "Expected failure"
            self.status = "FAIL"


class KwMock(Mock, BodyItem):
    non_existing = ("branch_status",)

    def __init__(self, is_result=False):
        self.full_name = self.name = "kwmock"
        if is_result:
            self.args = ["a1", "a2"]
            self.status = "PASS"
            self.type = BodyItem.KEYWORD


class ListenOutputs:

    def output_file(self, path):
        self._out_file("Output", path)

    def report_file(self, path):
        self._out_file("Report", path)

    def log_file(self, path):
        self._out_file("Log", path)

    def debug_file(self, path):
        self._out_file("Debug", path)

    def xunit_file(self, path):
        self._out_file("XUnit", path)

    def _out_file(self, name, path):
        print(f"{name}: {path}")


class ListenAll(ListenOutputs):
    ROBOT_LISTENER_API_VERSION = "2"

    def start_suite(self, name, attrs):
        print(f"SUITE START: {name} '{attrs['doc']}'")

    def start_test(self, name, attrs):
        print(f"TEST START: {name} '{attrs['doc']}' {', '.join(attrs['tags'])}")

    def start_keyword(self, name, attrs):
        args = [str(arg) for arg in attrs["args"]]
        print(f"KW START: {name} {args}")

    def end_keyword(self, name, attrs):
        print(f"KW END: {attrs['status']}")

    def end_test(self, name, attrs):
        if attrs["status"] == "PASS":
            print("TEST END: PASS")
        else:
            print(f"TEST END: {attrs['status']} {attrs['message']}")

    def end_suite(self, name, attrs):
        print(f"SUITE END: {attrs['status']} {attrs['statistics']}")

    def close(self):
        print("Closing...")


class TestListeners(unittest.TestCase):
    listener_name = "test_listeners.ListenAll"
    stat_message = "stat message"

    def setUp(self):
        listeners = Listeners([self.listener_name])
        assert_equal(len(listeners), 1)
        self.listener = list(listeners)[0]
        self.capturer = OutputCapturer()
        self.capturer.start()

    def test_start_suite(self):
        self.listener.start_suite(SuiteMock(), SuiteMock(is_result=True))
        self._assert_output("SUITE START: suitemock 'somedoc'")

    def test_start_test(self):
        self.listener.start_test(TestMock(), TestMock(is_result=True))
        self._assert_output("TEST START: testmock 'cod' foo, bar")

    def test_start_keyword(self):
        self.listener.start_keyword(KwMock(), KwMock(is_result=True))
        self._assert_output("KW START: kwmock ['a1', 'a2']")

    def test_end_keyword(self):
        self.listener.end_keyword(KwMock(), KwMock(is_result=True))
        self._assert_output("KW END: PASS")

    def test_end_test(self):
        self.listener.end_test(TestMock(), TestMock(is_result=True))
        self._assert_output("TEST END: FAIL Expected failure")

    def test_end_suite(self):
        self.listener.end_suite(SuiteMock(), SuiteMock(is_result=True))
        self._assert_output("SUITE END: PASS " + self.stat_message)

    def test_output_file(self):
        self.listener.output_file("path/to/output")
        self._assert_output("Output: path/to/output")

    def test_log_file(self):
        self.listener.log_file("path/to/log")
        self._assert_output("Log: path/to/log")

    def test_report_file(self):
        self.listener.report_file("path/to/report")
        self._assert_output("Report: path/to/report")

    def test_debug_file(self):
        self.listener.debug_file("path/to/debug")
        self._assert_output("Debug: path/to/debug")

    def test_xunit_file(self):
        self.listener.xunit_file("path/to/xunit")
        self._assert_output("XUnit: path/to/xunit")

    def test_close(self):
        self.listener.close()
        self._assert_output("Closing...")

    def _assert_output(self, expected):
        stdout, stderr = self.capturer._release()
        assert_equal(stderr, "")
        assert_equal(stdout.rstrip(), expected)


if __name__ == "__main__":
    unittest.main()
