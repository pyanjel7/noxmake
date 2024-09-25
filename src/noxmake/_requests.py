import requests
import requests.adapters
import os
import requests_file
import urllib.parse
import importlib.resources
import pathlib


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
        return super().send(request, **kwargs)


session = requests.session()
session.mount("file", FileAdapter())
session.mount("pymod", ModuleAdapter())

urllib.parse.uses_relative.extend(("file", "pymod"))
urllib.parse.uses_netloc.extend(("file", "pymod"))

_verify = os.environ.get("NOXMAKE_SSL_VERIFY", "")
session.verify = False if _verify.lower() == "false" else True if _verify.lower() == "true" else session.verify


def get(url, params=None, **kwargs):
    return session.get(url=url, params=params, **kwargs)


def as_uri(url):
    url_splitted = urllib.parse.urlsplit(url)

    if not url_splitted.scheme:
        return pathlib.Path(url).resolve().as_uri()

    if url_splitted.scheme == "file" and url_splitted.path.startswith(("/../", "/./")):
        return pathlib.Path(url_splitted.path[1:]).resolve().as_uri()

    return url


def url_join(url, resources):
    if url[-1] != "/":
        url = url + "/"

    url = url.replace("../", "$p/").replace("./", "$c/")
    url = urllib.parse.urljoin(url, resources)
    url = url.replace("$p/", "../").replace("$c/", "./")

    return url
