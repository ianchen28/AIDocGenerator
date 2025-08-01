# AI Document Generator

AI-powered document generation system using LangGraph.

## Installation

```bash
pip install -e .
```

## Usage

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8001
```

## Features

- AI-powered document generation
- LangGraph workflow orchestration
- FastAPI REST API
- Celery background tasks
- Redis stream processing 