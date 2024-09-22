import requests
import requests.adapters
import os
import requests_file
import json
import urllib.parse
import importlib.resources
import pathlib

from .warn import warning


class ModuleAdapter(requests_file.FileAdapter):
    def send(self, request, **kwargs):
        url_parts = urllib.parse.urlparse(request.url)
        module, _, path = url_parts.path.removeprefix("/").partition("/")
        module_path = importlib.resources.files(module)
        filepath = module_path / path
        request.url = filepath.as_uri()
        return super().send(request, **kwargs)


class FileAdapter(requests_file.FileAdapter):
    def send(self, request, **kwargs):
        url_parts = urllib.parse.urlparse(request.url)
        path = url_parts.path.removeprefix("/")
        request.url = pathlib.Path(path).resolve().as_uri()
        return super().send(request, **kwargs)


_session = requests.session()
_session.mount("file", FileAdapter())
_session.mount("pymod", ModuleAdapter())

urllib.parse.uses_relative.extend(("file", "pymod"))
urllib.parse.uses_netloc.extend(("file", "pymod"))

_verify = os.environ.get("NOXMAKE_SSL_VERIFY", "")
_session.verify = False if _verify.lower() == "false" else True if _verify.lower() == "true" else _session.verify


def get(url, params=None, **kwargs):
    return _session.get(url=url, params=params, **kwargs)


def _url_join(url, resources):
    if url[-1] != "/":
        url = url + "/"

    url = url.replace("../", "$p/").replace("./", "$c/")
    url_splitted = urllib.parse.urlsplit(url)

    if not url_splitted.scheme:
        url = pathlib.Path(url).absolute().as_uri()

    url = urllib.parse.urljoin(url, resources)
    url = url.replace("$p/", "../").replace("$c/", "./")

    return url


def get_templates(baseurl, params=None, **kwargs):
    url = _url_join(baseurl, "templates.json")

    resp = _session.get(url=url, params=params, **kwargs)
    if resp.ok:
        try:
            return resp.json()
        except json.JSONDecodeError:
            pass

    warning(f"unable to fetch templates from {url}")

    return dict()


def get_text(baseurl, resource, params=None, **kwargs):
    url = _url_join(baseurl, resource)

    resp = _session.get(url=url, params=params, **kwargs)
    if resp.ok:
        return resp.content.decode(resp.encoding or "utf8"), url

    return "", url
