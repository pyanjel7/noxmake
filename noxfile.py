import nox
import subprocess
import glob
import pathlib


SESSIONS_KWARGS = {
    
    "venv_backend": '',
    
    "reuse_venv": False,
    
    "venv_params": [],
    
    
    "python": ['3.12'],
    
}



nox.options.envdir = ''



nox.options.sessions = ["prep", "lint", "tests", "coverage"]


#
# helpers
#
def git_add(path=["."]):
    subprocess.run(["git", "add", *path])


def git_commit(msg, path=["."]):
    subprocess.run(["git", "commit", "-m", msg, *path])


def tag(tag, msg, force=False):
    args = ["git", "tag", tag, "-m", msg]

    if force:
        args.append("-af")

    subprocess.run(args)


def get_current_tag():
    try:
        return subprocess.check_output(["git", "describe", "--no-abbrev", "--tags"], text=True).strip() or "v0.0.0"
    except subprocess.CalledProcessError:
        pass

    return ""


def is_git_clean():
    return subprocess.check_output(["git", "describe", "--all", "--dirty"], text=True).find("dirty") == -1


def get_distrib_files():
    files = glob.glob("dist/*")
    version = get_current_tag().lstrip("v")
    whl_name = f"noxmake-{version}-py"
    src_name = f"noxmake-{version}.tar.gz"
    return [file for file in files if file.endswith(src_name) or file.find(whl_name) != -1]


def get_new_version_from_git_cliff(session, bump):
    try:
        version = subprocess.check_output([pathlib.Path(session.bin) / "git-cliff", "--bumped-version", "--bump", bump], text=True).strip()
        return f"{version.splitlines()[-1]}"
    except subprocess.CalledProcessError:
        pass

    return ""


def format(session):
    
    session.install("black")
    session.run("black", "src")
    


#
# sessions
#


@nox.session(**SESSIONS_KWARGS)
def dev(session: nox.Session) -> None:
    session.install("--upgrade", "pip")
    session.install("-e", ".[dev]")


@nox.session
def prep(session: nox.Session) -> None:
    force = "-f" in session.posargs

    if not is_git_clean() and not force:
        session.error('Version is not clean, , use "nox -s finalize -- -f" to disable version check')

    bump = "auto"
    new_version = ""

    for arg in session.posargs:
        if arg in ("major", "minor", "patch"):
            bump = arg
        if arg.startswith("v"):
            new_version = arg

    
    session.install("git-cliff")
    new_version = new_version or get_new_version_from_git_cliff(session, bump)
    session.run(
        "git-cliff",
        "--tag",
        new_version,
        "-o",
        "CHANGELOG.md",
    )
    pathlib.Path(".changelog_version").write_text(new_version)
    git_add([".changelog_version"])
    
    session.run("noxmake", "--", "-f", "--only-local", silent=True, external=True)
    format(session)


@nox.session
def finalize(session: nox.Session) -> None:
    force = "-f" in session.posargs

    try:
        version = pathlib.Path(".changelog_version").read_text()
    except FileNotFoundError:
        session.error("Changelog version not found, run prep session before")

    
    git_commit(
        "ign: changelog updated",
        path=[
            ".changelog_version",
            "CHANGELOG.md"
        ],
    )

    

    if version == get_current_tag() and not force:
        session.error('No change detected, use "nox -s finalize -- -f" to move the current version to the head')

    if not is_git_clean() and not force:
        session.error('Version is not clean, use "nox -s finalize -- -f" to disable version check')

    if force:
        tag(version, "-af", "ign: baseline=")
    else:
        tag(version, "ign: baseline=")


@nox.session(**SESSIONS_KWARGS)
def release(session) -> None:
    session.install("build")

    session.run("python", "-m", "build")
    files = get_distrib_files()
    session.log(files)
    if not files:
        session.error("no release package have been created, check git status")


@nox.session(**SESSIONS_KWARGS)
def lint(session: nox.Session) -> None:
    session.install("-e", ".[dev]")

    
    session.install("codespell")
    session.run("codespell", "src")
    

    
    session.install("flake8")
    session.run(
        "flake8",
        
        "--max-line-length",  "200",
        
        "src"
    )
    

    
    session.install("mypy")
    session.run("mypy")
    


@nox.session(**SESSIONS_KWARGS)
def tests(session: nox.Session):
    
    session.skip("test is not defined")
    


@nox.session(**SESSIONS_KWARGS)
def coverage(session: nox.Session):
    
    session.skip("coverage is not defined")
    


@nox.session
def build(session: nox.Session):
    session.install("build")
    session.run("python", "-m", "build")


@nox.session
def publish(session: nox.Session):
    session.install("twine")
    files = get_distrib_files()
    session.log("%s" % files)
    session.run("twine", "upload", *files)


if __name__ == "__main__":
    import nox.__main__

    nox.__main__.main()