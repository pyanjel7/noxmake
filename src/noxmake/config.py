import pathlib
import os
import tomllib
import functools
import platform

import collections.abc

from .constants import PACKAGE_PATH, PYPROJECT_TOML_FILE
from .warn import warning
from .license import get_primary_license

try:
    import git
    import git.config
except ImportError:
    git = None  # type: ignore[assignment]


class NoxmakeConfig(collections.abc.Mapping):

    def __init__(self, proxyfied=None):
        self.proxyfied = proxyfied or dict()

    def __len__(self):
        return len(self.proxyfied)

    def __iter__(self):
        return iter(self.proxyfied)

    def __getattr__(self, name):

        try:
            return getattr(self.proxyfied, name)
        except AttributeError:
            pass

        try:
            return self.__getitem__(name)
        except KeyError:
            pass

        raise AttributeError(name)

    def __setitem__(self, name, value):
        self.set(name, value)

    def __getitem__(self, name):
        item = self.proxyfied.__getitem__(name)

        if isinstance(item, (dict)):
            return NoxmakeConfig(item)

        return item

    def get(self, name, **kwargs):
        names = name.split(".", 1)

        try:
            item = self.__getitem__(names[0])

            if len(names) > 1:
                if not isinstance(item, NoxmakeConfig):
                    raise KeyError(names[0])

                return item.get(names[1])

            return item

        except KeyError:
            if "default" in kwargs:
                return kwargs.get("default")

            raise

    def set(self, name, value):
        names = name.split(".", 1)

        if len(names) > 1:
            try:
                item = self.__getitem__(names[0])
            except KeyError:
                item = NoxmakeConfig()

            self.proxyfied[names[0]] = item

            if not isinstance(item, NoxmakeConfig):
                raise KeyError(names[0])

            return item.set(names[1], value)

        self.proxyfied[names[0]] = value


class NoxmakeConfigBuilder:

    system = {
        "package_dirname": PACKAGE_PATH.name,
        "package_path": str(PACKAGE_PATH),
        "user": {
            "name": os.environ.get("USER") or os.environ.get("USERNAME"),
            "email": "",
        },
        "environ": dict(os.environ),
        "python_version": ".".join(platform.python_version_tuple()[:2]),
        "system": platform.system(),
    }

    def build(self, namespace):
        cfg = NoxmakeConfig()
        cfg["system"] = self.system
        cfg["pyproject"] = NoxmakeConfig(NoxmakePyproject())
        cfg["license"] = NoxmakeConfig(NoxmakeLicense(cfg))
        cfg["options"] = NoxmakeConfig(NoxmakeOptionConfig(namespace))

        if git is not None:
            cfg["git"] = NoxmakeGitConfig()  # Indicate who your project is intended for
        # "Intended Audience :: Developers",
        # "Topic :: Software Development :: Build Tools",

        return cfg


class NoxmakeLicense:

    def __init__(self, cfg):
        self.cfg = cfg

    @functools.cached_property
    def license(self):
        license_id = self.cfg.get("pyproject.project.license.expr", default=False)

        if license_id:
            details = get_primary_license(license_id)

        return details

    def __getitem__(self, name):
        try:
            return getattr(self.license, name)
        except Exception as e:
            warning(f"license[{name}]: {e}")

        return ""


class NoxmakePyproject:

    @functools.cached_property
    def pyproject(self):
        path = pathlib.Path(PYPROJECT_TOML_FILE)
        pyproject = path.read_text()
        return tomllib.loads(pyproject)

    def __getitem__(self, name):
        return self.pyproject[name]


class NoxmakeGitConfig:

    @functools.cached_property
    def repo(self):
        from git import Repo

        try:
            repo = Repo(PACKAGE_PATH.absolute())
        except Exception:
            raise AttributeError

        return repo

    @functools.cached_property
    def config(self):
        config = self.repo.config_reader()
        return config

    def __getitem__(self, name):
        if name == "head":
            repo = self.repo

            return {
                "tag": str(
                    next(
                        (tag for tag in repo.tags if tag.commit == repo.head.commit),
                        "0.0.0",
                    )
                ),
                "commit": str(repo.head.commit),
                "summary": repo.head.commit.summary,
                "message": repo.head.commit.message,
                "date": str(repo.head.commit.committed_datetime),
                "committer": str(repo.head.commit.committer),
            }

        self.config.sections()
        try:
            return dict(self.config.items(name))
        except Exception:
            pass

        raise IndexError


class NoxmakeOptionConfig:
    def __init__(self, namespace):
        self.namespace = namespace

    def __getitem__(self, name):

        try:
            return getattr(self.namespace, name)
        except AttributeError:
            pass

        raise KeyError(name)
