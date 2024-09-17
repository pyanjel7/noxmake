import trove_classifiers
import re
import difflib

from pip._vendor.packaging import specifiers

PYTHON_VER = re.compile(r"Programming Language :: Python :: (\d+.\d+)")
OSI_LICENSE = re.compile(r"License :: OSI Approved :: (.+)")


def python_realease():
    pyvers = filter(None, map(PYTHON_VER.match, trove_classifiers.sorted_classifiers))
    pyvers = (g[1] for g in pyvers)
    return pyvers


def osi_license():
    licenses = filter(None, map(OSI_LICENSE.match, trove_classifiers.sorted_classifiers))
    licenses = (g[1] for g in licenses)
    return licenses


def license_to_classifier(license_name):
    cs_licenses = list(osi_license())
    matches = difflib.get_close_matches(license_name, cs_licenses, n=1, cutoff=0.8)
    return f"License :: OSI Approved :: {matches[0]}" if matches else ""


def match_python_version(pyver_expr):

    spec = specifiers.Specifier(pyver_expr)
    result = list()

    for p in python_realease():
        if spec.contains(p):
            result.append(p)

    return sorted(result)


_devstatus_classifier = {
    "proto": "Development Status :: 2 - Pre-Alpha",
    "tune": "Development Status :: 3 - Alpha",
    "fix": "Development Status :: 4 - Beta",
    "prod": "Development Status :: 5 - Production/Stable",
    "lts": "Development Status :: 6 - Mature",
    "deprecated": "Development Status :: 7 - Inactive",
}


def devstatus_to_classifier(devstatus: str):
    return _devstatus_classifier.get(devstatus, "")


def classifiers_to_devstatus(classifiers: list):
    for classifier in classifiers:
        for status, value in _devstatus_classifier.items():
            if classifier == value:
                return status

    return ""
