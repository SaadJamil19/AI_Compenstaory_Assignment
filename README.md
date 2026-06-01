# AI-Enhanced CRM & Ticket Management System

Mini Zendesk/Freshdesk-style CRM for managing customers, support tickets, activity logs, AI outputs, dashboards, reports, users, and Telegram notifications.

**Team members:** Saad Jamil, Aon Raza

## Features Mapped to Requirements

- MR-1: JWT login with Manager and Agent roles, bcrypt password hashing
- MR-2: Customer create, view, update, delete with manager RBAC
- MR-3: Ticket create, assign, status/priority update, filters, detail view
- MR-4: Ticket comments plus full changelog/activity timeline
- MR-5: Dashboard stats, charts, manager workload, agent assigned tickets
- MR-6: Gemini AI categorization, sentiment, escalation, summaries, reply suggestion, chatbot
- MR-7: Telegram Bot API notifications with persistent message log
- MR-8: SQLite persistent database through SQLAlchemy
- MR-9: Project report in `docs/PROJECT_REPORT.md`
- MR-10: Setup instructions and API summary included below

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python FastAPI |
| Database | SQLite + SQLAlchemy |
| Auth | JWT + bcrypt |
| Frontend | HTML, CSS, Vanilla JavaScript |
| AI | Google Gemini |
| Messaging | Telegram Bot API |
| Charts | Chart.js |

## Folder Structure

```text
backend/        FastAPI app, routers, models, schemas, services, tests
frontend/       Static HTML/CSS/JS frontend served by FastAPI
docs/           Project report and screenshot placeholders
docker-compose.yml
README.md
```

## Environment Variables

| Variable | Purpose | Required |
|---|---|---|
| `SECRET_KEY` | JWT signing key | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Required for final demo, optional for development |
| `GEMINI_MODEL` | Gemini model name | Optional, default `gemini-1.5-flash` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Required for final demo, optional for development |
| `TELEGRAM_CHAT_ID` | Telegram recipient chat/channel ID | Required for final demo, optional for development |
| `DATABASE_URL` | SQLAlchemy DB URL | Optional, default `sqlite:///./crm.db` |

## Setup - Windows PowerShell

```powershell
cd e:\Downloads\aon_work\aon_work\backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend\.env`:

```env
SECRET_KEY=change-me-to-a-long-random-string
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash (use 2.5 flash or latest)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
DATABASE_URL=sqlite:///./crm.db
```

Run:

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`.

## Setup - Linux/Mac

```bash
cd /path/to/aon_work/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Demo Credentials

| Role | Email | Password |
|---|---|---|
| Manager | `admin@test.com` | `admin123` |
| Agent | `agent@test.com` | `agent123` |

## Reset Database

Schema changes are handled lightly, but for a clean student demo reset:

```powershell
cd backend
Remove-Item .\crm.db
uvicorn main:app --reload
```

Linux/Mac:

```bash
cd backend
rm -f crm.db
uvicorn main:app --reload
```

## Gemini Setup

Create a key in Google AI Studio, set `GEMINI_API_KEY`, and restart the backend.

1. Open `https://aistudio.google.com/app/apikey`.
2. Create an API key.
3. Add it to `backend\.env` as `GEMINI_API_KEY=...`.
4. Keep `GEMINI_MODEL=gemini-1.5-flash` unless your instructor requires a different model.
5. Log in as manager and open **Integrations** to run the Gemini test.

Fallback mode is for development only. For the final demo recording, configure a real Gemini key and show real AI category/sentiment and AI reply/summary output.

## Telegram Setup

Create a bot with BotFather, send a message to the bot, get your chat ID, then set:

1. Open Telegram and message `@BotFather`.
2. Send `/newbot` and follow the prompts.
3. Copy the bot token into `TELEGRAM_BOT_TOKEN`.
4. Send any message to the new bot from the Telegram account that should receive CRM alerts.
5. Get your chat ID using `@userinfobot` or by opening `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`.
6. Copy the chat ID into `TELEGRAM_CHAT_ID`.
7. Log in as manager and open **Integrations** or **Notifications** to send a test message.

```env
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=123456789

(Issues with telegram in pakistan and why the api might not work as intended: https://explorer.ooni.org/findings/324516225200)
```

Use the manager-only Notifications page to send a test message. Missing Telegram settings are logged as `skipped`, not treated as app errors.

Fallback/skipped mode is for development only. For final demo recording, configure a real Telegram bot and capture a screenshot of the received Telegram message.

## Integration Health Check

Managers can open `/integrations.html` to verify final-demo readiness:

- Gemini configured or missing
- Telegram configured or missing
- Test AI categorization/sentiment output
- Test Telegram message delivery

Secret values are never displayed.

## API Summary

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/login` | Login |
| GET | `/api/auth/me` | Current user |
| GET/POST/PUT/DELETE | `/api/customers` | Customer CRUD |
| GET | `/api/customers/{id}/profile` | Customer profile and ticket history |
| GET/POST/PUT/DELETE | `/api/tickets` | Ticket listing and CRUD |
| PATCH | `/api/tickets/{id}/status` | Update ticket status |
| PATCH | `/api/tickets/{id}/assign` | Manager ticket assignment |
| POST | `/api/tickets/{id}/comments` | Add comment/internal note |
| POST | `/api/tickets/{id}/ai-suggest-reply` | Generate AI reply draft |
| GET | `/api/dashboard/stats` | Dashboard stats |
| GET/POST | `/api/notifications` | Notification log and test |
| GET/POST | `/api/integrations` | Manager integration health checks |
| GET | `/api/reports/summary` | Manager reports |
| GET/POST/PUT/PATCH | `/api/users` | Manager user management |
| POST | `/api/ai/chat` | FAQ chatbot |

## Tests

```powershell
cd backend
pytest
```

## Export Report to PDF

The report source is `docs/PROJECT_REPORT.md`. Export it to PDF before submission.

Recommended command:

```powershell
python docs/export_report_pdf.py
```

Output:

```text
docs/AI_CRM_Project_Report.pdf
```

This command uses Pandoc if installed. If Pandoc is missing, it uses the built-in Python fallback exporter and still creates a PDF with screenshot placeholder boxes.

Direct pandoc command:

```powershell
pandoc docs/PROJECT_REPORT.md -o docs/AI_CRM_Project_Report.pdf --toc --number-sections
```

Alternative: install the VS Code extension **Markdown PDF**, open `docs/PROJECT_REPORT.md`, right-click, and choose **Markdown PDF: Export (pdf)**.

## Docker

```powershell
docker compose up --build
```

Then open `http://127.0.0.1:8000/`.


## Troubleshooting

| Issue | Fix |
|---|---|
| `401 Unauthorized` | Log in again; token may have expired |
| Missing new columns | Delete `backend/crm.db` and restart |
| Gemini not responding | Check `GEMINI_API_KEY` and `GEMINI_MODEL` |
| Telegram skipped | Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` |
| Port already used | Run `uvicorn main:app --port 8001` |

## Security Note

Do not commit `.env`, API keys, `crm.db`, `*.db`, virtual environments, `.pytest_cache`, `node_modules`, or `__pycache__`. The `.gitignore` excludes these generated and secret files.
