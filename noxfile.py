import os
import typing as t

import nox
from nox import options

PATH_TO_PROJECT = os.path.join(".", "assetextractor")
SCRIPT_PATHS = [PATH_TO_PROJECT, "noxfile.py"]
TEST_PATHS = ["tests"]

options.default_venv_backend = "uv"
options.sessions = ["format_fix", "pyright", "test"]


def uv_sync(
    session: nox.Session, /, *, include_self: bool = False, extras: t.Sequence[str] = (), groups: t.Sequence[str] = ()
) -> None:
    if extras and not include_self:
        raise RuntimeError("When specifying extras, set `include_self=True`.")

    args: list[str] = []
    for extra in extras:
        args.extend(("--extra", extra))

    group_flag = "--group" if include_self else "--only-group"
    for group in groups:
        args.extend((group_flag, group))

    session.run_install(
        "uv", "sync", "--frozen", *args, silent=True, env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}
    )


@nox.session()
def format_fix(session: nox.Session) -> None:
    uv_sync(session, groups=["dev"])
    session.run("python", "-m", "ruff", "format", *SCRIPT_PATHS)
    session.run("python", "-m", "ruff", "check", *SCRIPT_PATHS, "--fix")


@nox.session()
def format(session: nox.Session) -> None:
    uv_sync(session, groups=["dev"])
    session.run("python", "-m", "ruff", "format", *SCRIPT_PATHS, "--check")
    session.run("python", "-m", "ruff", "check", *SCRIPT_PATHS)


@nox.session()
def pyright(session: nox.Session) -> None:
    uv_sync(session, include_self=True, groups=["dev"])
    session.run("pyright", *SCRIPT_PATHS)


@nox.session()
def test(session: nox.Session) -> None:
    """Run pytest tests."""
    uv_sync(session, include_self=True, groups=["dev"])
    session.run("pytest", *TEST_PATHS)


@nox.session()
def test_verbose(session: nox.Session) -> None:
    """Run pytest tests with verbose output."""
    uv_sync(session, include_self=True, groups=["dev"])
    session.run("pytest", "-vv", *TEST_PATHS)


@nox.session()
def test_markers(session: nox.Session) -> None:
    """Run pytest tests filtered by marker."""
    uv_sync(session, include_self=True, groups=["dev"])
    # Example: session.run("pytest", "-m", "buff_ui", *TEST_PATHS)
    session.run("pytest", "--markers")


@nox.session()
def test_coverage(session: nox.Session) -> None:
    """Run pytest with coverage report."""
    uv_sync(session, include_self=True, groups=["dev"])
    session.run("pytest", "--cov=assetextractor", "--cov-report=html", "--cov-report=term", *TEST_PATHS)
