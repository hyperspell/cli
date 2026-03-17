# Hyperspell CLI

The Hyperspell CLI for developers and AI agents. Search your memories, manage connections, and integrate Hyperspell into any workflow - all from the terminal.

## Installation

```bash
pip install hyperspell-cli
```

Verify the installation:

```bash
hyperspell --version
```

## Authentication

```bash
hyperspell auth login
```

You'll be prompted for your API key and optional user ID. The CLI validates credentials before saving to `~/.hyperspell/config.json`.

### Check auth status

```bash
hyperspell auth status
```

### Log out

```bash
hyperspell auth logout
```

## Searching

The primary use case - search your memories from the terminal:

```bash
hyperspell search "quarterly revenue figures"
```

| Flag | Short | Description |
|------|-------|-------------|
| `--limit` | `-k` | Number of results to return (default: 5) |

### Piping results

When stdout is not a TTY, the CLI automatically outputs JSON:

```bash
hyperspell search "refund policy" | jq '.highlights[0].text'
```

Force JSON output in interactive mode:

```bash
hyperspell search "deploy steps" --json | jq '.highlights[0]'
```

## Memories

### List memories

```bash
hyperspell memories list
hyperspell memories list --source slack --limit 10
```

### Add a memory

```bash
hyperspell memories add "The deploy process changed to blue-green as of March 2026"
hyperspell memories add "API rate limits are 1000 req/min" --title "Rate Limits"
```

### Get a specific memory

```bash
hyperspell memories get <source> <resource_id>
```

### Delete a memory

```bash
hyperspell memories delete <source> <resource_id>
```

### Check ingestion status

```bash
hyperspell memories status
```

## Connections

### List connections

```bash
hyperspell connections list
```

### Revoke a connection

```bash
hyperspell connections revoke <connection_id>
```

## Global Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--version` | `-v` | Print version and exit |
| `--json` | | Force JSON output |
| `--quiet` | `-q` | Suppress spinners and interactive output; implies `--json` |

## Configuration

The CLI resolves configuration in this order: **CLI flags** > **environment variables** > **config file** > **defaults**.

### Environment variables

| Variable | Description |
|----------|-------------|
| `HYPERSPELL_API_KEY` | API key (overrides config file) |
| `HYPERSPELL_BASE_URL` | API base URL (default: `https://api.hyperspell.com`) |
| `HYPERSPELL_USER_ID` | User ID for X-As-User header |

### Config file

Stored at `~/.hyperspell/config.json`:

```json
{
  "api_key": "hs-...",
  "user_id": "user_123",
  "base_url": "https://api.hyperspell.com"
}
```

## Output Behavior

| Context | Behavior |
|---------|----------|
| Interactive terminal | Rich output with colors, spinners, and tables |
| Piped or redirected | Clean JSON on stdout |
| `--json` flag | Forces JSON output |
| `--quiet` flag | Suppresses all interactive elements, implies `--json` |

Errors always go to stderr. In JSON mode, errors are formatted as:

```json
{
  "error": {
    "message": "No API key found",
    "code": "no_api_key"
  }
}
```

Exit codes: `0` for success, `1` for failure.

## Command Reference

```
hyperspell [--version] [--json] [--quiet] <command>

Commands:
  search          Search your memories
  auth            Authentication management
    login         Authenticate with API key
    status        Print current auth state
    logout        Clear stored credentials
  memories        Memory management
    list          List memories
    add           Add a memory from text
    get           Get a specific memory
    delete        Delete a memory
    status        Show ingestion status
  connections     Source connection management
    list          List all connections
    revoke        Revoke a connection
```

## License

MIT
