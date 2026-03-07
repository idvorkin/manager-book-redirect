# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A URL redirect service for idvork.in blog. When sharing blog links, it generates HTML pages with dynamic Open Graph metadata (`og:title`, `og:description`, `og:image`) scraped from the actual blog content, then redirects the browser to the real blog URL. This gives rich link previews in chat apps.

## Commands

```bash
just test          # Run unit tests (parallel via pytest-xdist)
just fast-test     # Fast tests (used by pre-commit hooks)
just e2e-test      # E2E tests against deployed Modal service
just test-all      # Unit + E2E tests
just deploy        # Deploy to Modal
just serve         # Run locally with Modal
just install       # Set up venv and install deps with uv
```

Run a single test:

```bash
uv run pytest test_modal_redirect.py -k "test_name" -v
```

Linting/formatting runs via pre-commit (ruff for Python, biome for JSON, prettier for markdown/HTML). Pre-commit also runs `just fast-test`.

## Architecture

**Active codebase**: `modal_redirect.py` — FastAPI app deployed on Modal. This is the single file that matters for the current service.

**Legacy code**: `Redirect/` directory (Azure Functions) — deprecated, kept for backwards compatibility.

### Key flow in `modal_redirect.py`:

- `GET /{page}/{anchor}` → `generate_title()` → `get_html_for_redirect_simple()` → HTML with og:tags + JS redirect
- `GET /preview_text/{page}/{anchor}` → returns scraped preview text as JSON or plain text
- Title generation fetches the actual heading text from `idvork.in` via `get_heading_text_from_url()`, falling back to URL-based title (`humanize_url_part()`) on failure
- Page HTML is cached in-memory for 15 minutes (`page_cache` dict)
- URL validation restricts fetches to `idvork.in` domains only

### URL routing logic:

- No params → defaults to `manager-book` page
- One path segment → treated as anchor on `manager-book` (backwards compat)
- Two segments → `page/anchor`
- Also supports `?path=page#anchor` query parameter format

### Testing:

- `test_modal_redirect.py` — unit tests using httpx AsyncClient against FastAPI app directly; uses mocks for network calls
- `test_e2e_modal_redirect.py` — tests against the live deployed Modal service
- `test_link_spacing.py` — focused regression test for link spacing in descriptions
