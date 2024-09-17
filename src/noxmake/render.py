import jinja2
import datetime
import re
import pathlib
import jinja2.compiler
import jinja2.ext
import os

import namemaker
import wonderwords

from .requirements import requirements
from .license import get_primary_license, get_licenses, close_match_expr
from .constants import PACKAGE_PATH, NOXMAKE_EXT
from .classifiers import (
    match_python_version,
    devstatus_to_classifier,
    classifiers_to_devstatus,
)
from ._requests import get_templates, get_text
from .text import book


def _spdx_template_var(text, name=None, value=None):
    if isinstance(text, str):
        if value is None:
            value = r"\g<original>"
        name = name and f';name="{name}"' or r';name="[^"]+"'

        re_var_spdx_template = rf'<<var{name};original="(?P<original>[^"]+)";match="(?P<match>[^"]+)">>'

        text = re.sub(re_var_spdx_template, value, text)

    return text


def _spdx_template_optional(text, name=None, show=True):
    if isinstance(text, str):
        value = show and r"\g<original>" or ""
        name = name and f';name="{name}"' or r'(?:;name="[^"]+")?'
        re_optional_spdx_template = rf"(?s)<<beginOptional{name}>>(?P<original>(.(?!<<beginOptional>>)|.(?=<<endOptional>>))*)<<endOptional>>"

        text = re.sub(re_optional_spdx_template, value, text)

    return text


def _classifier_pyver(text):
    return match_python_version(text)[:-2]  # remove version not in release state


def _new_jinja_env(loader=None, template_name=""):

    if template_name.endswith(".py"):
        env = jinja2.Environment(loader=loader or loaders)
    else:
        env = jinja2.Environment(loader=loader or loaders)

    env.globals["time"] = datetime.datetime
    env.filters["spdx_var"] = _spdx_template_var
    env.filters["spdx_opt"] = _spdx_template_optional
    env.filters["pyver"] = _classifier_pyver
    env.filters["devclassifier"] = devstatus_to_classifier
    env.filters["devstatus"] = classifiers_to_devstatus
    env.filters["license"] = get_primary_license
    env.filters["licenses"] = get_licenses
    env.filters["licExpr"] = close_match_expr
    env.filters["requirements"] = requirements
    env.filters["wonder_s"] = wondersentences
    env.add_extension(NoxmakeExtension)

    return env


def wondersentences(text=""):
    names = {n.strip() for line in book.splitlines() for n in line.split(" ") if n.istitle()}
    names = namemaker.clean(names)

    nameset = namemaker.make_name_set(names)

    sent = wonderwords.RandomSentence(nouns=[nameset.make_name()])
    return sent.bare_bone_sentence().replace("The ", "")


class NoxmakeExtension(jinja2.ext.Extension):

    regex_statement = re.compile(r"#\s*j2:\s*(.*)")
    regex_inline = re.compile(r"#\s*j2_:\s*(.*)")

    def preprocess(self, source: str, name: str | None, filename: str | None = None) -> str:
        p_source: list[str] = []

        for line in source.splitlines():
            line = self.regex_statement.sub(r"{% \1 %}", line)
            line = self.regex_inline.sub(r"\1", line)
            p_source.append(line)

        return os.linesep.join(p_source)


class NoxmakeJsonLoader(jinja2.BaseLoader):
    def __init__(self):
        self.baseurl = "pymod:///noxmake.templates.default"
        self.mapping = dict()
        self.reset()

    def reset(self, baseurl: str | None = None):
        if baseurl:
            self.baseurl = baseurl

        self.mapping = get_templates(self.baseurl)

    def get_source(self, environment: jinja2.Environment, template: str):
        template = self.mapping.get(template)
        if template:
            source, url = get_text(self.baseurl, template)
            if source:
                return source, url, lambda: True

        raise jinja2.TemplateNotFound(template)

    def list_templates(self):
        return sorted(self.mapping)


class NoxmakeProjectLoader(jinja2.BaseLoader):

    def get_source(self, environment: jinja2.Environment, template: str):
        file = pathlib.Path(PACKAGE_PATH) / (template + NOXMAKE_EXT)
        if file.exists():
            source = file.read_text()
            return source, str(file), lambda: True

        raise jinja2.TemplateNotFound(template)

    def _list_templates(self, path: pathlib.Path):
        templates = []
        for entry in path.iterdir():
            if entry.name != "templates":
                if entry.is_file() and entry.suffix == NOXMAKE_EXT:
                    templates.append((path / entry.stem).as_posix())
                elif entry.is_dir():
                    templates.extend(self._list_templates(entry))

        return templates

    def list_templates(self):
        templates = self._list_templates(pathlib.Path())
        return sorted(templates)


project_loader = NoxmakeProjectLoader()
uri_loader = NoxmakeJsonLoader()

loaders = jinja2.ChoiceLoader(
    [
        project_loader,
        uri_loader,
    ]
)


def render(template_name: str, obj, loader=loaders):
    template = _new_jinja_env(loader, template_name=template_name).get_template(template_name)
    return template.render(obj), template.filename


def source(template_name: str, obj, loader=loaders):
    return loader.get_source(_new_jinja_env(loader), template_name)
