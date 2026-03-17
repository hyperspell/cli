from __future__ import annotations

import os
from typing import Any, Dict, Optional

import typer
from rich.console import Console

from hyperspell_cli.config import (
    clear_config,
    get_http_client,
    load_config,
    resolve_base_url,
    save_config,
)
from hyperspell_cli.lib.output import output_error, output_result, should_output_json
from hyperspell_cli.lib.prompts import confirm_action, require_password, require_text
from hyperspell_cli.lib.spinner import with_spinner

app = typer.Typer(
    name="auth",
    help="Manage authentication.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

stderr = Console(stderr=True)
stdout = Console()


def _get_opts(ctx: typer.Context) -> Dict[str, Any]:
    return ctx.ensure_object(dict)


@app.command()
def login(
    ctx: typer.Context,
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Hyperspell API base URL."),
    user_id: Optional[str] = typer.Option(None, "--user-id", help="User ID for X-As-User header."),
) -> None:
    """Log in to Hyperspell with an API key.

    You'll be prompted for your API key. The key is validated before saving.
    """
    opts = _get_opts(ctx)
    json_flag = opts.get("json", False)
    quiet = opts.get("quiet", False)

    effective_url = base_url or resolve_base_url()

    key = require_password(
        None, prompt_msg="Enter your API key:", flag="api-key", json_flag=json_flag
    )

    uid = user_id or require_text(
        None,
        prompt_msg="User ID for X-As-User (optional, press enter to skip):",
        flag="user-id",
        json_flag=json_flag,
        validate=lambda v: True,
    )

    # Validate credentials by calling /auth/me
    try:
        with with_spinner(
            "Validating credentials...",
            "Credentials valid",
            "Authentication failed",
            quiet=quiet,
        ):
            from hyperspell import Hyperspell

            kwargs: Dict[str, Any] = {"api_key": key, "base_url": effective_url}
            if uid and uid.strip():
                kwargs["default_headers"] = {"X-As-User": uid.strip()}
            client = Hyperspell(**kwargs)
            client.auth.me()
    except typer.Exit:
        raise
    except Exception as exc:
        output_error(f"Authentication failed: {exc}", code="auth_failed", json_flag=json_flag)

    cfg = load_config()
    cfg["api_key"] = key
    if effective_url != "https://api.hyperspell.com":
        cfg["base_url"] = effective_url
    if uid and uid.strip():
        cfg["user_id"] = uid.strip()
    save_config(cfg)

    if not quiet:
        stderr.print("  [green]\u2714[/green] Config saved to ~/.hyperspell/config.json")


@app.command()
def status(ctx: typer.Context) -> None:
    """Show current authentication state."""
    opts = _get_opts(ctx)
    json_flag = opts.get("json", False)

    env_key = os.environ.get("HYPERSPELL_API_KEY")
    cfg = load_config()

    if env_key:
        auth_source = "env (API key)"
    elif cfg.get("api_key"):
        auth_source = "config (API key)"
    else:
        auth_source = "none"

    info = {
        "authenticated": bool(env_key) or bool(cfg.get("api_key")),
        "auth_source": auth_source,
        "user_id": os.environ.get("HYPERSPELL_USER_ID") or cfg.get("user_id"),
        "base_url": os.environ.get("HYPERSPELL_BASE_URL")
        or cfg.get("base_url", "https://api.hyperspell.com"),
        "base_url_source": "env"
        if os.environ.get("HYPERSPELL_BASE_URL")
        else ("config" if cfg.get("base_url") else "default"),
    }

    if should_output_json(json_flag):
        output_result(info, json_flag=json_flag)
        return

    stdout.print()
    if info["authenticated"]:
        stdout.print(f"  Auth:      [green]authenticated[/green]  [dim]({auth_source})[/dim]")
    else:
        stdout.print("  Auth:      [red]not authenticated[/red]")
    uid = info["user_id"] or "[dim]not set[/dim]"
    stdout.print(f"  User ID:   {uid}")
    stdout.print(f"  Base URL:  {info['base_url']}  [dim]({info['base_url_source']})[/dim]")
    stdout.print()


@app.command()
def whoami(ctx: typer.Context) -> None:
    """Show the currently authenticated user (calls /auth/me)."""
    opts = _get_opts(ctx)
    json_flag = opts.get("json", False)
    quiet = opts.get("quiet", False)

    try:
        with with_spinner(
            "Fetching user info...", "User info retrieved", "Failed to fetch user info", quiet=quiet
        ):
            http = get_http_client()
            resp = http.get("/auth/me")
            resp.raise_for_status()
            data = resp.json()
    except typer.Exit:
        raise
    except Exception as exc:
        output_error(f"Failed to fetch user info: {exc}", code="whoami_failed", json_flag=json_flag)

    if should_output_json(json_flag):
        output_result(data, json_flag=json_flag)
        return

    stdout.print()
    for key, value in data.items():
        stdout.print(f"  {key}: {value}")
    stdout.print()


@app.command()
def logout(
    ctx: typer.Context,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt."),
) -> None:
    """Clear saved credentials from ~/.hyperspell/config.json."""
    opts = _get_opts(ctx)
    json_flag = opts.get("json", False)

    confirm_action("Are you sure you want to log out?", yes_flag=yes, json_flag=json_flag)

    clear_config()
    stderr.print("  Logged out. Config cleared.")
