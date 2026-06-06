# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Open Knowledge Chat — a Django 6.0 chat application using Python 3.14+, with HTMX and Alpine.js for the frontend. Package management uses `uv`.

## Architecture

- **`config/`** — Django project settings, root URL conf, WSGI/ASGI entry points
- **`open_knowledge_chat/`** — Application package containing Django apps
  - **`core/`** — Core app with shared base models and utilities
  - **`chat/`** — Chat feature app
  - **`templates/`** — Templates directory. Each app store its template within this directory, not in the app directory. base template is `open_knowledge_chat/templates/base.html`.

Apps are registered in `INSTALLED_APPS` without the `open_knowledge_chat.` prefix (e.g., `'core'`, `'chat'`). The `PYTHONPATH` includes `open_knowledge_chat/` so imports use the short form: `from core.models import TimeStampedModel`.

## Frontend Stack

- **Django templates**
- **HTMX** for dynamic interactions without full page reloads
- **Alpine.js** for client-side reactivity
- Partials are defined with `{% partialdef name inline %}` and referenced in Python as `'app/template.html#partial-name'`

## Code Style
- PEP 8
- 120 maximum characters per line.
