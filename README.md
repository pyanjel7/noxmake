# Readme

## About noxmake


Noxmake is a nox wrapper for automatic project file generation.


## Requirements

* Python >= 3.12
* git

## Installation

To install noxmake, simply execute:

```shell
$ pip install noxmake
```

## Getting Started

### Create and costumize your project

Create a project
```sh
$ noxmake -- --license "GPL-3.0+" --version-scm --auto-deps --with-black --with-codespell --with-mypy --with-flake8 --with-gitcliff --auto-baseline --project-line-lenght 200 --project-description "Noxmake is a nox wrapper for automatic project file generation."
```
> **_NOTE:_** project config is saved in the .noxmake_cfg file

Download a template file to costumize it:
```
$ noxmake -s README.md.an
```

Force rewrite your project file with local template
```sh
$ noxmake -s README.md -- -f --only-local
```

### Generate your first project release

Create your repository
```sh
$ git init
```

Commit your project files
```sh
$ git add . && git commit -m "add: initial commit" .
```

Launch project default sessions
```sh
$ nox
```

Finalize project
```sh
$ nox -s finalize
```

Generate the first release
```sh
$ nox -s release
```

## Getting help

```sh
$ noxmake --help
usage: noxmake [-h] [--version] [-l] [--json] [-s [SESSIONS ...]] [-p [PYTHONS ...]] [-k KEYWORDS] [-t [TAGS ...]] [-v] [-ts]
               [-db {conda,mamba,micromamba,virtualenv,venv,uv,none}] [-fb {conda,mamba,micromamba,virtualenv,venv,uv,none}] [--no-venv]
               [--reuse-venv {yes,no,always,never}] [-r] [-N] [-R] [-f NOXFILE] [--envdir ENVDIR] [--extra-pythons [EXTRA_PYTHONS ...]] [-P [FORCE_PYTHONS ...]]
               [-x] [--no-stop-on-first-error] [--error-on-missing-interpreters] [--no-error-on-missing-interpreters] [--error-on-external-run]
               [--no-error-on-external-run] [--install-only] [--no-install] [--report REPORT] [--non-interactive] [--nocolor] [--forcecolor]
               ...

Noxmake is a nox wrapper for automatic project file generation.

General options:
  These are general arguments used when invoking Nox.

  -h, --help            Show this help message and exit.
  --version             Show the Nox version and exit.
  posargs               Arguments following ``--`` that are passed through to the session(s).
  -f NOXFILE, --noxfile NOXFILE
                        Location of the Python file containing Nox sessions.

Sessions options:
  These arguments are used to control which Nox session(s) to execute.

  -l, --list-sessions, --list
                        List all available sessions and exit.
  --json                JSON output formatting. Requires list-sessions currently.
  -s [SESSIONS ...], -e [SESSIONS ...], --sessions [SESSIONS ...], --session [SESSIONS ...]
                        Which sessions to run. By default, all sessions will run.
  -k KEYWORDS, --keywords KEYWORDS
                        Only run sessions that match the given expression.
  -t [TAGS ...], --tags [TAGS ...]
                        Only run sessions with the given tags.

Python options:
  These arguments are used to control which Python version(s) to use.

  -p [PYTHONS ...], --pythons [PYTHONS ...], --python [PYTHONS ...]
                        Only run sessions that use the given python interpreter versions.
  --extra-pythons [EXTRA_PYTHONS ...], --extra-python [EXTRA_PYTHONS ...]
                        Additionally, run sessions using the given python interpreter versions.
  -P [FORCE_PYTHONS ...], --force-pythons [FORCE_PYTHONS ...], --force-python [FORCE_PYTHONS ...]
                        Run sessions with the given interpreters instead of those listed in the Noxfile. This is a shorthand for ``--python=X.Y --extra-
                        python=X.Y``. It will also work on sessions that don't have any interpreter parametrized.

Environment options:
  These arguments are used to control Nox's creation and usage of virtual environments.

  -db {conda,mamba,micromamba,virtualenv,venv,uv,none}, --default-venv-backend {conda,mamba,micromamba,virtualenv,venv,uv,none}
                        Virtual environment backend to use by default for Nox sessions, this is ``'virtualenv'`` by default but any of ``['conda', 'mamba',
                        'micromamba', 'virtualenv', 'venv', 'uv', 'none']`` are accepted.
  -fb {conda,mamba,micromamba,virtualenv,venv,uv,none}, --force-venv-backend {conda,mamba,micromamba,virtualenv,venv,uv,none}
                        Virtual environment backend to force-use for all Nox sessions in this run, overriding any other venv backend declared in the Noxfile and
                        ignoring the default backend. Any of ``['conda', 'mamba', 'micromamba', 'virtualenv', 'venv', 'uv', 'none']`` are accepted.
  --no-venv             Runs the selected sessions directly on the current interpreter, without creating a venv. This is an alias for '--force-venv-backend none'.
  --reuse-venv {yes,no,always,never}
                        Controls existing virtualenvs recreation. This is ``'no'`` by default, but any of ``('yes', 'no', 'always', 'never')`` are accepted.
  -r, --reuse-existing-virtualenvs
                        This is an alias for '--reuse-venv=yes|no'.
  -N, --no-reuse-existing-virtualenvs
                        Disables --reuse-existing-virtualenvs if it is enabled in the Noxfile.
  -R                    Reuse existing virtualenvs and skip package re-installation. This is an alias for '--reuse-existing-virtualenvs --no-install'.
  --envdir ENVDIR       Directory where Nox will store virtualenvs, this is ``.nox`` by default.

Execution options:
  These arguments are used to control execution of sessions.

  -x, --stop-on-first-error
                        Stop after the first error.
  --no-stop-on-first-error
                        Disables --stop-on-first-error if it is enabled in the Noxfile.
  --error-on-missing-interpreters
                        Error instead of skipping sessions if an interpreter can not be located.
  --no-error-on-missing-interpreters
                        Disables --error-on-missing-interpreters if it is enabled in the Noxfile.
  --error-on-external-run
                        Error if run() is used to execute a program that isn't installed in a session's virtualenv.
  --no-error-on-external-run
                        Disables --error-on-external-run if it is enabled in the Noxfile.
  --install-only        Skip session.run invocations in the Noxfile.
  --no-install          Skip invocations of session methods for installing packages (session.install, session.conda_install, session.run_install) when a virtualenv
                        is being reused.
  --non-interactive     Force session.interactive to always be False, even in interactive sessions.

Reporting options:
  These arguments are used to control Nox's reporting during execution.

  -v, --verbose         Logs the output of all commands run including commands marked silent.
  -ts, --add-timestamp  Adds a timestamp to logged output.
  --report REPORT       Output a report of all sessions to the given filename.
  --nocolor, --no-color
                        Disable all color output.
  --forcecolor, --force-color
                        Force color output, even if stdout is not an interactive terminal.
Noxmake global session options.

options:
  -f, --force           Always generate files even if the file already exists.
  --template uri        Uri of the project template.
                                Available scheme:[pymod|file|https|http]
                                /!\ Experimental, uses it only when you trust the source
  --only-local          Uses only local template
  --auto-deps           Search for project dependencies.
                                See pipreqs for more information.
  --auto-deps-mode {>=,==,no}
                        Enable dynamic versioning  (default=">=")
                                cf: pipreqs --mode.
  --auto-deps-local     Use only local package
                                cf: pipreqs --use-local.
  --license LICENSE     Project license (default=GPL-3.0-only).
  --devstatus DEVSTATUS
                        Project development status (default=proto).
  --build-backend BUILD_BACKEND
                        Project build-backend (default=setuptools).
  --srcdir SRCDIR       Path to the project source directory (default=src).
  --testdir TESTDIR     Path to the project test directory (default=tests).
  --docdir DOCDIR       Path to the project documentation directory (default=doc).
  --changelog CHANGELOG
                        Path to the project change log file (default=CHANGELOG.md).
  -k KEYWORDS, --keywords KEYWORDS
                        Project keywords
  --auto-baseline       Request noxmake to generate the baseline name.
                                Uses wonderworld and namemaker packages.
  --no-namespace        Disable namespace finder (setupttools).
  --project-_key_ VALUE
                        Set a pyproject.project._key_ to VALUE.
  --define [DEFINES]    Use this option to define pre-processing constants,
                                    if no value is given, the constant is set to true
                        samples:
                                noxmake -- -k name1
                                noxmake -- k name1=value
                            usage: " ... {{pyproject.tool.noxmake.name1 }} ... ".
  --undef DEFINES       Defines a constant and sets its value to false.
  --version-scm         Uses scm versioning.
  --version-dynamic     Uses dynamic versioning.
  --with-all            Sets all variables beginning with "with" to true.
  --with-_tool_         Activates a tool in the build process.
                        sample: noxmake -- --with-mypy
                        usage: "... {%if options.with_mypy %} ..."
  --without-_tool_      Deactivates a tool.
  --using-_feature_     Enables a tool feature.
                        sample: noxmake -- --with-coverage --using-coverage-branch.
  --not-using-_feature_
                        Disables a feature.
```


## License

GNU General Public License v3.0 or later