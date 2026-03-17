from __future__ import annotations

from typing import Any, Dict, Optional

import typer
from rich.console import Console
from rich.table import Table

from hyperspell_cli.config import get_sdk_client, serialize
from hyperspell_cli.lib.output import output_error, output_result, should_output_json
from hyperspell_cli.lib.spinner import with_spinner

app = typer.Typer(
    name="memories",
    help="Manage memories.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

stderr = Console(stderr=True)
stdout = Console()


def _get_opts(ctx: typer.Context) -> Dict[str, Any]:
    return ctx.ensure_object(dict)


@app.command("list")
def list_memories(
    ctx: typer.Context,
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Filter by source."),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of memories to return."),
) -> None:
    """List memories."""
    opts = _get_opts(ctx)
    json_flag = opts.get("json", False)
    quiet = opts.get("quiet", False)

    client = get_sdk_client()

    try:
        with with_spinner(
            "Fetching memories...", "Fetched memories", "Failed to fetch memories", quiet=quiet
        ):
            kwargs: Dict[str, Any] = {"limit": limit}
            if source:
                kwargs["source"] = source
            page = client.memories.list(**kwargs)
            items = list(page)
    except typer.Exit:
        raise
    except Exception as exc:
        output_error(str(exc), code="list_error", json_flag=json_flag)

    if should_output_json(json_flag):
        output_result(serialize(items), json_flag=json_flag)
        return

    if not items:
        stderr.print("[yellow]No memories found.[/yellow]")
        return

    table = Table(title="Memories")
    table.add_column("Source", style="bold")
    table.add_column("Resource ID")
    table.add_column("Title")
    table.add_column("Status")

    for m in items:
        table.add_row(
            getattr(m, "source", "-"),
            getattr(m, "resource_id", "-"),
            (getattr(m, "title", "") or "")[:50],
            getattr(m, "status", "-"),
        )

    stdout.print(table)


@app.command()
def add(
    ctx: typer.Context,
    text: str = typer.Argument(..., help="Text content to add as a memory."),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Optional title."),
) -> None:
    """Add a memory from text."""
    opts = _get_opts(ctx)
    json_flag = opts.get("json", False)
    quiet = opts.get("quiet", False)

    client = get_sdk_client()

    try:
        with with_spinner("Adding memory...", "Memory added", "Failed to add memory", quiet=quiet):
            kwargs: Dict[str, Any] = {"text": text}
            if title:
                kwargs["title"] = title
            result = client.memories.add(**kwargs)
    except typer.Exit:
        raise
    except Exception as exc:
        output_error(str(exc), code="add_error", json_flag=json_flag)

    if should_output_json(json_flag):
        output_result(serialize(result), json_flag=json_flag)
        return

    rid = getattr(result, "resource_id", "")
    stdout.print(f"[green]\u2714[/green] Memory added  (resource_id: {rid})")


@app.command()
def get(
    ctx: typer.Context,
    source: str = typer.Argument(..., help="Source name."),
    resource_id: str = typer.Argument(..., help="Resource ID."),
) -> None:
    """Get a specific memory by source and resource ID."""
    opts = _get_opts(ctx)
    json_flag = opts.get("json", False)
    quiet = opts.get("quiet", False)

    client = get_sdk_client()

    try:
        with with_spinner(
            "Fetching memory...", "Fetched memory", "Failed to fetch memory", quiet=quiet
        ):
            memory = client.memories.get(resource_id, source=source)
    except typer.Exit:
        raise
    except Exception as exc:
        output_error(str(exc), code="get_error", json_flag=json_flag)

    if should_output_json(json_flag):
        output_result(serialize(memory), json_flag=json_flag)
        return

    stdout.print(f"[bold]{getattr(memory, 'title', '') or 'Untitled'}[/bold]")
    stdout.print(f"  Source:      {getattr(memory, 'source', '-')}")
    stdout.print(f"  Resource ID: {getattr(memory, 'resource_id', '-')}")
    stdout.print(f"  Status:      {getattr(memory, 'status', '-')}")
    content = getattr(memory, "text", "") or getattr(memory, "content", "") or ""
    if content:
        stdout.print()
        stdout.print(content[:1000])


@app.command()
def delete(
    ctx: typer.Context,
    source: str = typer.Argument(..., help="Source name."),
    resource_id: str = typer.Argument(..., help="Resource ID."),
) -> None:
    """Delete a memory."""
    opts = _get_opts(ctx)
    json_flag = opts.get("json", False)
    quiet = opts.get("quiet", False)

    client = get_sdk_client()

    try:
        with with_spinner(
            "Deleting memory...", "Memory deleted", "Failed to delete memory", quiet=quiet
        ):
            result = client.memories.delete(resource_id, source=source)
    except typer.Exit:
        raise
    except Exception as exc:
        output_error(str(exc), code="delete_error", json_flag=json_flag)

    if should_output_json(json_flag):
        output_result(serialize(result), json_flag=json_flag)
        return

    stdout.print("[green]\u2714[/green] Memory deleted.")


@app.command("status")
def memory_status(ctx: typer.Context) -> None:
    """Show memory ingestion status."""
    opts = _get_opts(ctx)
    json_flag = opts.get("json", False)
    quiet = opts.get("quiet", False)

    client = get_sdk_client()

    try:
        with with_spinner(
            "Fetching status...", "Status retrieved", "Failed to fetch status", quiet=quiet
        ):
            result = client.memories.status()
    except typer.Exit:
        raise
    except Exception as exc:
        output_error(str(exc), code="status_error", json_flag=json_flag)

    if should_output_json(json_flag):
        output_result(serialize(result), json_flag=json_flag)
        return

    data = serialize(result)
    if isinstance(data, dict):
        for k, v in data.items():
            stdout.print(f"  {k}: {v}")
    else:
        stdout.print(str(data))
