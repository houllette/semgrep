import json
import os
import subprocess
import sys
from pathlib import Path
from typing import NoReturn
from typing import Optional
from typing import Sequence

import click

from semgrep.commands.wrapper import handle_command_errors
from semgrep.constants import SHOULDAFOUND_BASE_URL
from semgrep.error import SemgrepError
from semgrep.state import get_state
from semgrep.types import JsonObject


@click.command()
@click.option(
    "--message",
    "-m",
    required=True,
    type=str,
    help="Explain what should have been found, plus any supporting information (such as framework, etc.).",
)
@click.option(
    "--email",
    type=str,
    help="Your email, to collect a shiny prize (defaults to your git email)",
)
@click.option("--start", "-s", type=int, help="Line at which vulnerability starts")
@click.option(
    "--end",
    "-e",
    type=int,
    help="Line at which vulnerability ends (defaults to --start)",
)
@click.option(
    "--yes", "-y", is_flag=True, help="Send data to Semgrep.dev without confirmation"
)
@click.argument("path", required=True, nargs=1, type=Path)
@handle_command_errors
def shouldafound(
    message: str,
    email: Optional[str],
    start: Optional[int],
    end: Optional[int],
    yes: bool,
    path: Path,
) -> NoReturn:
    """
    Report a false negative in this project. "path" should be the file in which you expected the vulnerability to be found.
    """
    if not email:
        email = (
            subprocess.check_output(["git", "config", "user.email"]).decode().strip()
        )

    text = _read_lines(path, start, end)

    data = {
        "email": email,
        "lines": text,
        "message": message,
        "path": str(path.resolve().relative_to(os.getcwd())),
    }

    if not yes:
        click.echo("Will send to Semgrep.dev:", err=True)
        click.echo(json.dumps(data, indent=2), err=True)
        if not click.confirm("OK to send?", err=True):
            click.echo("Aborted", err=True)
            sys.exit(0)

    # send to backend
    try:
        playground_link = _make_shouldafound_request(data)
        click.echo("Sent feedback. Thanks for your contribution!", err=True)
        click.echo(
            f"You can view and extend the generated rule template here: {playground_link}",
            err=True,
        )
        sys.exit(0)
    except SemgrepError:
        click.echo(
            "Could not send feedback to server. Please consider instead reaching out to us another way!",
            err=True,
        )
        sys.exit(2)


def _make_shouldafound_request(data: JsonObject) -> Optional[str]:
    state = get_state()
    resp = state.app_session.post(f"{SHOULDAFOUND_BASE_URL}/shouldafound", json=data)

    if resp.status_code == 200:
        if "playground_link" in resp.json():
            return str(resp.json()["playground_link"])
        else:
            raise SemgrepError(
                f"Failed to parse playground link, response text: {resp.text}"
            )
    else:
        raise SemgrepError(
            f"Failed to POST shouldafound data, error code: {resp.status_code}"
        )


def _read_lines(path: Path, start: Optional[int], end: Optional[int]) -> Sequence[str]:
    with path.open("r") as fd:
        lines = fd.readlines()
    if start is not None:
        if start < 1:
            click.echo("--start must be > 0", err=True)
            sys.exit(2)
        if start > len(lines):
            click.echo("--start must be no more than number of lines in file", err=True)
            sys.exit(2)
        if end is None:
            end = start
        else:
            if end < start:
                click.echo("--end must be >= than --start", err=True)
                sys.exit(2)
        lines = lines[start - 1 : end]
    text = "".join(lines)
    return text
