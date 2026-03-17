from __future__ import annotations

from typing import Any, Dict, Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from hyperspell_cli.config import get_sdk_client, serialize
from hyperspell_cli.lib.output import output_error, output_result, should_output_json
from hyperspell_cli.lib.spinner import with_spinner

stderr = Console(stderr=True)
stdout = Console()


def _get_opts(ctx: typer.Context) -> Dict[str, Any]:
    return ctx.ensure_object(dict)


def _render_results(results: Any) -> None:
    highlights = results.highlights if hasattr(results, "highlights") else []
    if not highlights:
        stderr.print("[yellow]No results found.[/yellow]")
        return

    for i, h in enumerate(highlights, 1):
        source = getattr(h, "source", "unknown")
        score = getattr(h, "score", None)
        title_text = getattr(h, "title", "") or ""
        content = getattr(h, "text", "") or getattr(h, "content", "") or ""
        url = getattr(h, "url", None)

        title_parts = [f"[bold]#{i}[/bold]  {source}"]
        if score is not None:
            title_parts.append(f"[dim]score={score:.3f}[/dim]")
        title = Text.from_markup("  ".join(title_parts))

        snippet = content[:500] + ("..." if len(content) > 500 else "") if content else ""
        body = Markdown(snippet) if snippet else Text.from_markup("[dim]no content[/dim]")

        if title_text and not snippet:
            body = Text(title_text)

        stdout.print(Panel(body, title=title, subtitle=url, border_style="blue"))


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
            results = client.memories.search(query=query, limit=limit)
    except typer.Exit:
        raise
    except Exception as exc:
        output_error(str(exc), code="search_error", json_flag=json_flag)

    if should_output_json(json_flag):
        output_result(serialize(results), json_flag=json_flag)
        return

    _render_results(results)
