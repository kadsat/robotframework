#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from datetime import datetime

from robot.result import Keyword, ResultVisitor, TestCase, TestSuite
from robot.utils import NullMarkupWriter, XmlWriter
from robot.version import get_full_version


class XmlLogger(ResultVisitor):
    generator = "Robot"

    def __init__(self, output, rpa=False, suite_only=False):
        self._writer = self._get_writer(output, preamble=not suite_only)
        if not suite_only:
            self._writer.start("robot", self._get_start_attrs(rpa))

    def _get_writer(self, output, preamble=True):
        return XmlWriter(output, usage="output", write_empty=False, preamble=preamble)

    def _get_start_attrs(self, rpa):
        return {
            "generator": get_full_version(self.generator),
            "generated": datetime.now().isoformat(),
            "rpa": "true" if rpa else "false",
            "schemaversion": "5",
        }

    def close(self):
        self._writer.end("robot")
        self._writer.close()

    def visit_message(self, msg):
        self._write_message(msg)

    def message(self, msg):
        self._write_message(msg)

    def _write_message(self, msg):
        attrs = {
            "time": msg.timestamp.isoformat() if msg.timestamp else None,
            "level": msg.level,
        }
        if msg.html:
            attrs["html"] = "true"
        self._writer.element("msg", msg.message, attrs)

    def start_keyword(self, kw):
        self._writer.start("kw", self._get_start_keyword_attrs(kw))

    def _get_start_keyword_attrs(self, kw):
        attrs = {"name": kw.name, "owner": kw.owner}
        if kw.type != "KEYWORD":
            attrs["type"] = kw.type
        if kw.source_name:
            attrs["source_name"] = kw.source_name
        return attrs

    def end_keyword(self, kw):
        self._write_list("var", kw.assign)
        self._write_list("arg", [str(a) for a in kw.args])
        self._write_list("tag", kw.tags)
        self._writer.element("doc", kw.doc)
        if kw.timeout:
            self._writer.element("timeout", attrs={"value": str(kw.timeout)})
        self._write_status(kw)
        self._writer.end("kw")

    def start_if(self, if_):
        self._writer.start("if")

    def end_if(self, if_):
        self._write_status(if_)
        self._writer.end("if")

    def start_if_branch(self, branch):
        attrs = {"type": branch.type, "condition": branch.condition}
        self._writer.start("branch", attrs)

    def end_if_branch(self, branch):
        self._write_status(branch)
        self._writer.end("branch")

    def start_for(self, for_):
        attrs = {
            "flavor": for_.flavor,
            "start": for_.start,
            "mode": for_.mode,
            "fill": for_.fill,
        }
        self._writer.start("for", attrs)

    def end_for(self, for_):
        for name in for_.assign:
            self._writer.element("var", name)
        for value in for_.values:
            self._writer.element("value", value)
        self._write_status(for_)
        self._writer.end("for")

    def start_for_iteration(self, iteration):
        self._writer.start("iter")

    def end_for_iteration(self, iteration):
        for name, value in iteration.assign.items():
            self._writer.element("var", value, {"name": name})
        self._write_status(iteration)
        self._writer.end("iter")

    def start_try(self, root):
        self._writer.start("try")

    def end_try(self, root):
        self._write_status(root)
        self._writer.end("try")

    def start_try_branch(self, branch):
        attrs = {
            "type": "EXCEPT",
            "pattern_type": branch.pattern_type,
            "assign": branch.assign,
        }
        if branch.type == branch.EXCEPT:
            self._writer.start("branch", attrs)
            self._write_list("pattern", branch.patterns)
        else:
            self._writer.start("branch", attrs={"type": branch.type})

    def end_try_branch(self, branch):
        self._write_status(branch)
        self._writer.end("branch")

    def start_while(self, while_):
        attrs = {
            "condition": while_.condition,
            "limit": while_.limit,
            "on_limit": while_.on_limit,
            "on_limit_message": while_.on_limit_message,
        }
        self._writer.start("while", attrs)

    def end_while(self, while_):
        self._write_status(while_)
        self._writer.end("while")

    def start_while_iteration(self, iteration):
        self._writer.start("iter")

    def end_while_iteration(self, iteration):
        self._write_status(iteration)
        self._writer.end("iter")

    def start_group(self, group):
        self._writer.start("group", {"name": group.name})

    def end_group(self, group):
        self._write_status(group)
        self._writer.end("group")

    def start_var(self, var):
        attr = {"name": var.name}
        if var.scope is not None:
            attr["scope"] = var.scope
        if var.separator is not None:
            attr["separator"] = var.separator
        self._writer.start("variable", attr, write_empty=True)

    def end_var(self, var):
        for val in var.value:
            self._writer.element("var", val)
        self._write_status(var)
        self._writer.end("variable")

    def start_return(self, return_):
        self._writer.start("return")

    def end_return(self, return_):
        for value in return_.values:
            self._writer.element("value", value)
        self._write_status(return_)
        self._writer.end("return")

    def start_continue(self, continue_):
        self._writer.start("continue")

    def end_continue(self, continue_):
        self._write_status(continue_)
        self._writer.end("continue")

    def start_break(self, break_):
        self._writer.start("break")

    def end_break(self, break_):
        self._write_status(break_)
        self._writer.end("break")

    def start_error(self, error):
        self._writer.start("error")

    def end_error(self, error):
        for value in error.values:
            self._writer.element("value", value)
        self._write_status(error)
        self._writer.end("error")

    def start_test(self, test):
        attrs = {"id": test.id, "name": test.name, "line": str(test.lineno or "")}
        self._writer.start("test", attrs)

    def end_test(self, test):
        self._writer.element("doc", test.doc)
        self._write_list("tag", test.tags)
        if test.timeout:
            self._writer.element("timeout", attrs={"value": str(test.timeout)})
        self._write_status(test)
        self._writer.end("test")

    def start_suite(self, suite):
        attrs = {"id": suite.id, "name": suite.name}
        if suite.source:
            attrs["source"] = str(suite.source)
        self._writer.start("suite", attrs)

    def end_suite(self, suite):
        self._writer.element("doc", suite.doc)
        for name, value in suite.metadata.items():
            self._writer.element("meta", value, {"name": name})
        self._write_status(suite)
        self._writer.end("suite")

    def statistics(self, stats):
        self.visit_statistics(stats)

    def start_statistics(self, stats):
        self._writer.start("statistics")

    def end_statistics(self, stats):
        self._writer.end("statistics")

    def start_total_statistics(self, total_stats):
        self._writer.start("total")

    def end_total_statistics(self, total_stats):
        self._writer.end("total")

    def start_tag_statistics(self, tag_stats):
        self._writer.start("tag")

    def end_tag_statistics(self, tag_stats):
        self._writer.end("tag")

    def start_suite_statistics(self, tag_stats):
        self._writer.start("suite")

    def end_suite_statistics(self, tag_stats):
        self._writer.end("suite")

    def visit_stat(self, stat):
        attrs = stat.get_attributes(values_as_strings=True)
        self._writer.element("stat", stat.name, attrs)

    def errors(self, errors):
        self.visit_errors(errors)

    def start_errors(self, errors):
        self._writer.start("errors")

    def end_errors(self, errors):
        self._writer.end("errors")

    def _write_list(self, tag, items):
        for item in items:
            self._writer.element(tag, item)

    def _write_status(self, item):
        attrs = {
            "status": item.status,
            "start": item.start_time.isoformat() if item.start_time else None,
            "elapsed": format(item.elapsed_time.total_seconds(), "f"),
        }
        self._writer.element("status", item.message, attrs)


class LegacyXmlLogger(XmlLogger):

    def _get_start_attrs(self, rpa):
        return {
            "generator": get_full_version(self.generator),
            "generated": self._datetime_to_timestamp(datetime.now()),
            "rpa": "true" if rpa else "false",
            "schemaversion": "4",
        }

    def _datetime_to_timestamp(self, dt):
        if dt is None:
            return None
        return dt.isoformat(" ", timespec="milliseconds").replace("-", "")

    def _get_start_keyword_attrs(self, kw):
        attrs = {"name": kw.kwname, "library": kw.libname}
        if kw.type != "KEYWORD":
            attrs["type"] = kw.type
        if kw.source_name:
            attrs["sourcename"] = kw.source_name
        return attrs

    def _write_status(self, item):
        attrs = {
            "status": item.status,
            "starttime": self._datetime_to_timestamp(item.start_time),
            "endtime": self._datetime_to_timestamp(item.end_time),
        }
        if (
            isinstance(item, (TestSuite, TestCase))
            or isinstance(item, Keyword)
            and item.type == "TEARDOWN"
        ):
            message = item.message
        else:
            message = ""
        self._writer.element("status", message, attrs)

    def _write_message(self, msg):
        ts = self._datetime_to_timestamp(msg.timestamp) if msg.timestamp else None
        attrs = {"timestamp": ts, "level": msg.level}
        if msg.html:
            attrs["html"] = "true"
        self._writer.element("msg", msg.message, attrs)


class NullLogger(XmlLogger):

    def __init__(self):
        super().__init__(None)

    def _get_writer(self, output, preamble=True):
        return NullMarkupWriter()
