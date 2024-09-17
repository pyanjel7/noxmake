import nox
import nox.sessions

import jinja2
import pathlib
import os
import argparse
import re
import json

from .config import NoxmakeConfigBuilder, NoxmakeConfig
from .constants import NOXMAKE_EXT
from .render import render, source, uri_loader, loaders, project_loader, wondersentences


templates = []


class _add(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        if not values:
            values = self.const

        items = getattr(namespace, self.dest) or list()

        keyword = re.match(".+:", values)
        if keyword:
            items = {item for item in items if not item.startswith(keyword.group())}
        else:
            items = set(items)

        items.add(values)
        setattr(namespace, self.dest, list(items))


def _define(key=None):
    class _define(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            items = getattr(namespace, self.dest) or dict()
            k = key

            if k is None:
                k, _, v = values.partition("=")
            else:
                v = values

            items[k.strip()] = v.strip() if v else True

            setattr(namespace, self.dest, items)

    return _define


def _undef(key=None):

    class _undef(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            items = getattr(namespace, self.dest) or dict()
            k = key

            if k is None:
                k = values

            items[k.strip()] = False

            setattr(namespace, self.dest, items)

    return _undef


def _config_read():
    try:

        with open(".noxmake_cfg") as f:
            config_dict = json.load(f)

        return argparse.Namespace(**config_dict)

    except FileNotFoundError:
        pass

    return argparse.Namespace()


def _config_write(namespace: argparse.Namespace):
    with open(".noxmake_cfg", "w") as f:

        cfg = dict(namespace.__dict__)

        cfg.pop("force", None)
        cfg.pop("only_local", None)
        cfg.pop("with__tool_", None)
        cfg.pop("without__tool_", None)
        cfg.pop("using__feature_", None)
        cfg.pop("project__key_", None)
        cfg.pop("not_using__feature_", None)

        json.dump(cfg, f, indent=4)


def _parse(args, namespace=None):

    class _Namespace(argparse.Namespace):
        def __getattr__(self, name):
            if name.startswith("with_"):
                return self.with_all

            raise AttributeError(name)

    parser = create_parser()

    namespace, unknown = parser.parse_known_args(args, namespace)

    for define_ in filter(lambda opt: opt.startswith("-D"), unknown):
        parser.add_argument(define_, dest="defines", nargs="?", action=_define(define_[2:]))

    for undef_ in filter(lambda opt: opt.startswith("-U"), unknown):
        parser.add_argument(undef_, dest="defines", nargs=0, action=_undef(undef_[2:]))

    for with_ in filter(lambda opt: opt.startswith(("--with-", "--without-")), unknown):
        action = "store_true" if with_.startswith("--with-") else "store_false"
        dest = "with_" + with_.removeprefix("--with-").removeprefix("--without-").replace("-", "_")
        parser.add_argument(with_, dest=dest, action=action, default=namespace.with_all)

    for using_ in filter(lambda opt: opt.startswith(("--using-", "--not-using-")), unknown):
        action = "store_true" if using_.startswith("--using-") else "store_false"
        dest = "using_" + using_.removeprefix("--using-").removeprefix("--not-using-").replace("-", "_")
        parser.add_argument(using_, dest=dest, action=action, default=namespace.using_all)

    for project_ in filter(lambda opt: opt.startswith("--project-"), unknown):
        parser.add_argument(project_, default=None)

    namespace = parser.parse_args(unknown, namespace)

    return _Namespace(**namespace.__dict__)


def _build_config(poargs):
    return _parse(poargs, _config_read())


def _prepare_file(
    session: nox.Session,
    filename,
    loader=None,
    template=None,
):
    namespace = _build_config(session.posargs)

    cfg = NoxmakeConfigBuilder().build(namespace)

    file = pathlib.Path(filename)
    template = template or str(file)

    if not namespace.force and file.exists():
        session.skip(f"{file.name} already exists")

    try:
        rendered_text, filename = render(template, cfg, loader)
    except jinja2.exceptions.TemplateNotFound:
        session.error(f"unable to find a valid template for {file.name}")

    if rendered_text == "makedirs":
        file.mkdir(parents=True, exist_ok=True)
        session.log(f"create directory: {file}")
        return

    session.log(f"render from {filename}")
    file.write_text(rendered_text)

    return namespace


def _prepare_an(session: nox.Session, tmplname: str, loader: jinja2.loaders.BaseLoader):
    namespace = _build_config(session.posargs)

    file = pathlib.Path(tmplname + NOXMAKE_EXT)

    if not namespace.force and file.exists():
        session.skip(f"{file.name} already exists")

    templates = source(tmplname, loader)
    file.write_text(templates[0])


def create_parser():
    parser = argparse.ArgumentParser(add_help=False, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Always generate files even if the file already exists.",
    )
    parser.add_argument(
        "--template",
        metavar="uri",
        help="Uri of the project template.\n\tAvailable scheme:[pymod|file|https|http]\n\t/!\\ Experimental, uses it only when you trust the source",
    )

    parser.add_argument("--only-local", action="store_true", help="Uses only local template")

    parser.add_argument(
        "--auto-deps",
        action="store_true",
        help="Search for project dependencies.\n\tSee pipreqs for more information.",
    )
    parser.add_argument(
        "--auto-deps-mode",
        choices=[">=", "==", "no"],
        default=">=",
        help='Enable dynamic versioning  (default="%(default)s")\n\tcf: pipreqs --mode.',
    )
    parser.add_argument(
        "--auto-deps-local",
        action="store_true",
        help="Use only local package\n\tcf: pipreqs --use-local.",
    )

    parser.add_argument(
        "--license",
        default="GPL-3.0-only",
        help="Project license (default=%(default)s).",
    )
    parser.add_argument(
        "--devstatus",
        default="proto",
        help="Project development status (default=%(default)s).",
    )

    parser.add_argument(
        "--build-backend",
        default="setuptools",
        help="Project build-backend (default=%(default)s).",
    )
    parser.add_argument(
        "--srcdir",
        default="src",
        help="Path to the project source directory (default=%(default)s).",
    )
    parser.add_argument(
        "--testdir",
        default="tests",
        help="Path to the project test directory (default=%(default)s).",
    )
    parser.add_argument(
        "--docdir",
        default="doc",
        help="Path to the project documentation directory (default=%(default)s).",
    )
    parser.add_argument(
        "--changelog",
        default="CHANGELOG.md",
        help="Path to the project change log file (default=%(default)s).",
    )
    parser.add_argument("-k", "--keywords", action=_add, help="Project keywords", default=[])
    parser.add_argument(
        "--auto-baseline",
        dest="keywords",
        nargs=0,
        action=_add,
        const=f"baseline:{wondersentences()}",
        help="Request noxmake to generate the baseline name.\n\tUses wonderworld and namemaker packages.",
    )

    parser.add_argument(
        "--no-namespace",
        dest="namespaces",
        action="store_false",
        default=True,
        help="Disable namespace finder (setupttools).",
    )
    parser.add_argument(
        "--project-_key_",
        metavar="VALUE",
        default=None,
        help="Set a pyproject.project._key_ to VALUE.",
    )

    parser.add_argument(
        "--define",
        dest="defines",
        nargs="?",
        action=_define(),
        default=dict(),
        help='Use this option to define pre-processing constants,\n\t\
    if no value is given, the constant is set to true\nsamples:\n\tnoxmake -- -k name1\n\tnoxmake -- k name1=value\n\
    usage: " ... {{pyproject.tool.noxmake.name1 }} ... ".',
    )
    parser.add_argument(
        "--undef",
        dest="defines",
        action=_undef(),
        help="Defines a constant and sets its value to false.",
    )

    parser.add_argument("--version-scm", action="store_true", help="Uses scm versioning.")
    parser.add_argument("--version-dynamic", action="store_true", help="Uses dynamic versioning.")
    parser.add_argument(
        "--with-all",
        action="store_true",
        help='Sets all variables beginning with "with" to true.',
    )
    parser.add_argument(
        "--with-_tool_",
        action="store_true",
        help='Activates a tool in the build process.\nsample: noxmake -- --with-mypy\nusage: "... {%%if options.with_mypy %%} ..."',
    )
    parser.add_argument("--without-_tool_", action="store_false", help="Deactivates a tool.")
    parser.add_argument(
        "--using-_feature_",
        action="store_true",
        help="Enables a tool feature.\nsample: noxmake -- --with-coverage --using-coverage-branch.",
    )
    parser.add_argument("--not-using-_feature_", action="store_false", help="Disables a feature.")
    return parser


def create_session(posargs):
    global templates

    namespace = _build_config(posargs)

    uri_loader.reset(namespace.template)
    loader = project_loader if namespace.only_local else loaders
    templates = loader.list_templates()

    for tmpl in loader.list_templates():

        @nox.session(python=False, default=False, name=tmpl)
        def _(session: nox.Session, cfg: NoxmakeConfig | None = None):
            _prepare_file(session, session.name, loader=loader)

    for tmpl in uri_loader.list_templates():

        @nox.session(python=False, default=False, name=tmpl + NOXMAKE_EXT)
        def _(session: nox.Session, cfg: NoxmakeConfig | None = None, tmplname: str = tmpl):
            _prepare_an(session, tmplname, loader=uri_loader)


@nox.session(python=False, default=True)
def prepare(session: nox.Session):
    try:
        if "pyproject.toml" in templates:
            namespace = _prepare_file(session, "pyproject.toml")
            _config_write(namespace)
    except nox.sessions._SessionSkip:
        pass

    if not os.path.exists("pyproject.toml"):
        session.error("pyproject.toml not found")

    for tmpl in templates:
        if tmpl != "pyproject.toml":
            session.notify(tmpl)
