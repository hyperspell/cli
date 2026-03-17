from __future__ import annotations

from typing import Any, Dict

import typer
from rich.console import Console
from rich.table import Table

from hyperspell_cli.config import get_sdk_client, serialize
from hyperspell_cli.lib.output import output_error, output_result, should_output_json
from hyperspell_cli.lib.spinner import with_spinner

app = typer.Typer(
    name="connections",
    help="Manage source connections.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

stderr = Console(stderr=True)
stdout = Console()


def _get_opts(ctx: typer.Context) -> Dict[str, Any]:
    return ctx.ensure_object(dict)


@app.command("list")
def list_connections(ctx: typer.Context) -> None:
    """List all source connections."""
    opts = _get_opts(ctx)
    json_flag = opts.get("json", False)
    quiet = opts.get("quiet", False)

    client = get_sdk_client()

    try:
        with with_spinner(
            "Fetching connections...",
            "Fetched connections",
            "Failed to fetch connections",
            quiet=quiet,
        ):
            result = client.connections.list()
    except typer.Exit:
        raise
    except Exception as exc:
        output_error(str(exc), code="list_error", json_flag=json_flag)

    data = serialize(result)

    if should_output_json(json_flag):
        output_result(data, json_flag=json_flag)
        return

    connections = data if isinstance(data, list) else data.get("connections", [])
    if not connections:
        stderr.print("[yellow]No connections found.[/yellow]")
        return

    table = Table(title="Connections")
    table.add_column("Provider", style="bold")
    table.add_column("Connection ID")
    table.add_column("Status")

    for c in connections:
        if isinstance(c, dict):
            table.add_row(
                c.get("provider", "-"),
                c.get("id", c.get("connection_id", "-")),
                c.get("status", "-"),
            )

    stdout.print(table)


@app.command()
def revoke(
    ctx: typer.Context,
    connection_id: str = typer.Argument(..., help="Connection ID to revoke."),
) -> None:
    """Revoke a source connection."""
    opts = _get_opts(ctx)
    json_flag = opts.get("json", False)
    quiet = opts.get("quiet", False)

    client = get_sdk_client()

    try:
        with with_spinner(
            "Revoking connection...",
            "Connection revoked",
            "Failed to revoke connection",
            quiet=quiet,
        ):
            result = client.connections.revoke(connection_id)
    except typer.Exit:
        raise
    except Exception as exc:
        output_error(str(exc), code="revoke_error", json_flag=json_flag)

    if should_output_json(json_flag):
        output_result(serialize(result), json_flag=json_flag)
        return

    stdout.print(f"[green]\u2714[/green] Connection {connection_id} revoked.")
