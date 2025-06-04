# FRC-GPT Scouting App — Codex Agent Guide

This project is a GPT-augmented scouting app for FRC competitions. The backend is built in FastAPI and connects to Google Sheets, The Blue Alliance API, and Statbotics.

## 🧠 Purpose

This repo supports GPT-powered data cleaning, pick list generation, and match strategy from structured scouting data.

## 📦 Setup

To set up Codex to interact with the app, run:

```python
python setup_codex.py
```

This script:
- Installs required dependencies from `requirements.txt`
- Loads `.env` variables if present
- Initializes the Google Sheets API
- Adds the backend to the Python path

## 📁 Key Modules

| File | Purpose |
|------|---------|
| `backend/app/services/sheets_service.py` | Load and query Google Sheets |
| `backend/app/services/tba_client.py` | Pulls data from The Blue Alliance |
| `backend/app/services/unified_event_data_service.py` | Combines and validates all data sources |
| `setup_codex.py` | Codex runtime setup script |

## 🔧 Example Tasks

You can ask Codex to:
- `get_sheet_headers("Scouting")`
- `update_sheet_values("Sheet1!A2:C5", values)`
- Call any function in `sheets_service.py` or `unified_event_data_service.py`

## 🔐 Secrets

The Google Sheets service account is split into two environment variables:
- `B64_PART_1`
- `B64_PART_2`

These are base64-encoded and decoded inside `sheets_service.py`.

---