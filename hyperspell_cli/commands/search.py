from __future__ import annotations

from typing import Any, Dict

import typer
from rich.console import Console
from rich.table import Table

from hyperspell_cli.config import get_sdk_client, serialize
from hyperspell_cli.lib.output import output_error, output_result, should_output_json
from hyperspell_cli.lib.spinner import with_spinner

stderr = Console(stderr=True)
stdout = Console()


def _get_opts(ctx: typer.Context) -> Dict[str, Any]:
    return ctx.ensure_object(dict)


def _render_results(results: Any) -> None:
    highlights = results.highlights if hasattr(results, "highlights") else []
    total = getattr(results, "total", len(highlights))
    query_id = getattr(results, "query_id", None)

    if not highlights:
        stderr.print("[yellow]No results found.[/yellow]")
        return

    meta_parts = [f"[bold]{total}[/bold] result(s)"]
    if query_id:
        meta_parts.append(f"[dim]query_id={query_id}[/dim]")
    stdout.print("  ".join(meta_parts))

    table = Table(show_header=True, header_style="bold cyan", expand=True)
    table.add_column("Score", style="green", no_wrap=True, min_width=6)
    table.add_column("Title", no_wrap=False, min_width=20)
    table.add_column("Source", style="dim", no_wrap=True)
    table.add_column("Summary", no_wrap=False)

    for h in highlights:
        score = getattr(h, "score", None)
        title = getattr(h, "title", "") or ""
        source = getattr(h, "source", "") or ""
        content = getattr(h, "text", "") or getattr(h, "content", "") or ""
        summary = content[:100] + ("…" if len(content) > 100 else "")

        score_str = f"{score:.3f}" if score is not None else "-"
        table.add_row(score_str, title, source, summary)

    stdout.print(table)


def search(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Search query."),
    limit: int = typer.Option(5, "--limit", "-k", help="Number of results to return."),
) -> None:
    """Search your memories. This is the core command.

    Examples:

        $ hyperspell search "how does authentication work?"

        $ hyperspell search "deploy steps" --json | jq '.highlights[0]'
    """
    opts = _get_opts(ctx)
    json_flag = opts.get("json", False)
    quiet = opts.get("quiet", False)

    client = get_sdk_client()

    try:
        with with_spinner("Searching...", "Search complete", "Search failed", quiet=quiet):
            results = client.memories.search(query=query, max_results=limit)
    except typer.Exit:
        raise
    except Exception as exc:
        output_error(str(exc), code="search_error", json_flag=json_flag)

    if should_output_json(json_flag):
        output_result(serialize(results), json_flag=json_flag)
        return

    _render_results(results)
