# Recoll MCP Server

Read-only MCP tools for a local [Recoll](https://www.recoll.org/) index. The
server uses Recoll's Python bindings for search and text extraction, including
PDF and Office documents supported by the local Recoll installation.

## Setup

Install Recoll, its Python bindings, and the extractors needed for your file
types. Build a Recoll index first. Then create a virtual environment with the
same Python version as the Recoll bindings:

```sh
uv venv --python /usr/bin/python3 --system-site-packages .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

Set `RECOLL_CONFDIR` to the Recoll index configuration directory and
`RECOLL_ALLOWED_ROOT` to the document tree the server may expose. The server
will return only indexed files under that root. Its tools do not write files.

```sh
RECOLL_CONFDIR="$HOME/.recoll" \
RECOLL_ALLOWED_ROOT="$HOME/Documents" \
.venv/bin/python recoll_mcp_server.py
```

The server uses MCP over stdio. Configure your MCP client with the Python
executable and this script as arguments, and set the two environment variables
above. For example:

```sh
codex mcp add recoll-search \
  --env RECOLL_CONFDIR="$HOME/.recoll" \
  --env RECOLL_ALLOWED_ROOT="$HOME/Documents" \
  -- "$PWD/.venv/bin/python" "$PWD/recoll_mcp_server.py"
```

## Tools

- `search_filesystem(query, max_results=10)` returns indexed paths, MIME types,
  document IDs, and short previews. Recoll query syntax supports Boolean terms,
  quoted phrases, and wildcards. At most 20 results are returned per call.
- `get_document_content(document_id, max_chars=12000)` extracts text from one
  indexed hit. At most 20,000 characters are returned, and sources larger than
  25 MB are refused.

Both tools check that the indexed file resolves under `RECOLL_ALLOWED_ROOT`.
Document IDs must come from the configured index. An MCP client may send
returned excerpts to its model provider, so treat the client configuration as
having access to the indexed documents.

## Development

The server requires MCP Python SDK 1.x. The `requirements.txt` file pins its
major version. The Recoll binding comes from the system package so it matches
the system Recoll version.
