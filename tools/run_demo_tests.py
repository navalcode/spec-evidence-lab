"""Run the bundled example and record actual unittest outcomes as JUnit XML."""

import argparse
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cases = {}

    def startTest(self, test):
        super().startTest(test)
        name = test.id()
        classname, method = name.rsplit(".", 1)
        self.cases[name] = ET.Element("testcase", {"classname": classname, "name": method})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        ET.SubElement(self.cases[test.id()], "failure").text = self._exc_info_to_string(err, test)

    def addError(self, test, err):
        super().addError(test, err)
        ET.SubElement(self.cases[test.id()], "error").text = self._exc_info_to_string(err, test)

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        ET.SubElement(self.cases[test.id()], "skipped", {"message": reason})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/demo.xml")
    args = parser.parse_args()
    # Fixed bundled fixture, never a command or module supplied by a proposal.
    suite = unittest.defaultTestLoader.discover(str(ROOT / "examples/offline_catalog"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordedResult).run(suite)
    xml = ET.Element("testsuite", {"name": "offline-catalog-demo", "tests": str(result.testsRun),
        "failures": str(len(result.failures)), "errors": str(len(result.errors)), "skipped": str(len(result.skipped))})
    xml.extend(result.cases.values())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(xml).write(args.output, encoding="utf-8", xml_declaration=True)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
