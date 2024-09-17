import dataclasses
import license_expression
import functools
import difflib

from .constants import LICENSE_URL
from .classifiers import license_to_classifier
from .warn import warning
from ._requests import get


@dataclasses.dataclass
class License:
    reference: str
    isDeprecatedLicenseId: bool
    detailsUrl: str
    referenceNumber: int
    name: str
    licenseId: str
    seeAlso: list[str]
    isOsiApproved: bool
    isFsfLibre: bool | None = None

    @functools.cached_property
    def details(self):
        return get(self.detailsUrl).json()

    @functools.cached_property
    def classifier(self):
        try:
            osi_license = license_to_classifier(self.details["name"])
            return osi_license
        except Exception as e:
            warning(f"unable to get licenses classifiers: {e}")

        return ""


@dataclasses.dataclass
class Licenses:
    licenses: dict[str, License]
    licenseListVersion: str
    releaseDate: str

    def get(self, key):
        for lic in self.licenses:
            if lic.licenseId == key:
                return lic.licenseId

    def __post_init__(self):
        if isinstance(self.licenses, list):
            self.licenses = {lic["licenseId"]: License(**lic) for lic in self.licenses}


_all_licenses = None


def get_all_licenses():
    global _all_licenses

    if _all_licenses is None:
        res_json = get(LICENSE_URL).json()

        _all_licenses = Licenses(**res_json)

    return _all_licenses


def get_licenses(expr):
    keys = license_expression.Licensing().license_keys(expr)
    return [get_all_licenses().licenses.get(key_close_match(key), key) for key in keys]


def get_primary_license(expr):
    key = license_expression.Licensing().primary_license_key(expr)
    return get_all_licenses().licenses.get(key_close_match(key), key)


def key_close_match(key):
    lic_keys = get_all_licenses().licenses.keys()
    matches = difflib.get_close_matches(key, lic_keys, n=1, cutoff=0.8)
    if matches:
        return matches[0]
    return key


def close_match_expr(expr):
    tokens = license_expression.Licensing().tokenize(expr)

    new_expr = ""
    for token in tokens:
        if isinstance(token[0], license_expression.LicenseSymbol):
            new_expr = " ".join((new_expr, key_close_match(token[1])))
        else:
            new_expr = " ".join((new_expr, token[1]))

    return new_expr
