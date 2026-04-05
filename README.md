# CRM Full

A lightweight CRM system for managing clients, deals, tasks and orders. Built as a single-page app with a Python backend and no frontend framework dependencies.

## Problem it solves

Small sales teams often need a simple CRM without the complexity of enterprise tools. This app provides a clean pipeline view, client notes, activity history and task tracking - all in one place.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | SQLite |
| Auth | Session-based (Flask sessions) |
| Frontend | Vanilla HTML/CSS/JavaScript |
| Deploy | Gunicorn, Procfile-ready |

## Architecture

```
Browser (index.html)
      |
      | REST API (JSON)
      v
Flask App (app.py)
      |
      v
SQLite (crm.db)
   - clients
   - notes
   - activities
   - tasks
   - orders
```

## Key Features

- Client pipeline with stages: Lead - Contact - Proposal - Negotiation - Won/Lost
- Activity feed per client (auto-logs stage changes, calls, notes)
- Tasks and orders management
- Multi-user session auth
- Responsive dark UI, no frontend framework

## How to Run Locally

```bash
git clone https://github.com/MaximLopatin123/crm-full.git
cd crm-full
pip install -r requirements.txt
python app.py
```

Open `http://localhost:8080`

Set a custom secret key via environment variable:

```bash
SECRET_KEY=your-secret-key python app.py
```

## Screenshots

_Screenshots coming soon_
