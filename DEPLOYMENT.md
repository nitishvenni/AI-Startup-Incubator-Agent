# AI Startup Incubator Agent — Deployment Guide

> **Stack:** Python 3.11+, Flask 3.x, SQLite, IBM watsonx.ai (Granite)

---

## Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Local Development Setup](#2-local-development-setup)
3. [Environment Variables](#3-environment-variables)
4. [Running the Application](#4-running-the-application)
5. [Production Deployment](#5-production-deployment)
   - [5a. Ubuntu/Debian VPS (Gunicorn + Nginx)](#5a-ubuntudebian-vps)
   - [5b. Docker](#5b-docker)
   - [5c. Railway / Render / Fly.io](#5c-railway--render--flyio)
6. [Database Management](#6-database-management)
7. [Customising the AI Mentor](#7-customising-the-ai-mentor)
8. [PDF & DOCX Export](#8-pdf--docx-export)
9. [Logging](#9-logging)
10. [Security Checklist](#10-security-checklist)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Prerequisites

| Tool | Minimum Version |
|------|----------------|
| Python | 3.11 |
| pip | 23+ |
| IBM Cloud account with watsonx.ai access | — |
| (Optional) Docker 24+ | — |
| (Optional) Nginx | — |

---

## 2. Local Development Setup

```bash
# 1. Clone / download the project
git clone <your-repo-url>
cd "AI Startup Incubator Agent"

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and fill in your IBM credentials (see section 3)

# 5. Run the development server
python app.py
# Or:
flask run --debug
```

The app will be available at `http://localhost:5000`.

---

## 3. Environment Variables

Copy `.env.example` to `.env` and fill in:

```env
# ── IBM watsonx.ai ──────────────────────────────────
IBM_API_KEY=your_ibm_api_key_here
IBM_PROJECT_ID=your_ibm_project_id_here
IBM_URL=https://us-south.ml.cloud.ibm.com
IBM_MODEL=ibm/granite-13b-instruct-v2

# ── Flask ────────────────────────────────────────────
FLASK_SECRET_KEY=generate-a-long-random-string-here
FLASK_ENV=production       # or development
FLASK_DEBUG=False          # True only for development

# ── Database ─────────────────────────────────────────
DATABASE_PATH=database/incubator.db

# ── Optional: override port ──────────────────────────
PORT=5000
```

> **Getting IBM credentials:**
> 1. Sign up at [cloud.ibm.com](https://cloud.ibm.com)
> 2. Create a watsonx.ai project at [dataplatform.cloud.ibm.com](https://dataplatform.cloud.ibm.com)
> 3. Generate an API key at **Manage → Access (IAM) → API keys**
> 4. Copy the Project ID from your watsonx.ai project settings

---

## 4. Running the Application

### Development
```bash
python app.py
# or
flask --app app run --debug
```

### Production (single process test)
```bash
FLASK_ENV=production python app.py
```

---

## 5. Production Deployment

### 5a. Ubuntu/Debian VPS

```bash
# Install system dependencies
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip nginx

# Install WeasyPrint system deps (for PDF export)
sudo apt install -y libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf2.0-0

# Set up application
git clone <repo> /opt/incubator
cd /opt/incubator
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt gunicorn
cp .env.example .env
# edit .env ...

# Install systemd service
sudo tee /etc/systemd/system/incubator.service <<EOF
[Unit]
Description=AI Startup Incubator Agent
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/incubator
EnvironmentFile=/opt/incubator/.env
ExecStart=/opt/incubator/.venv/bin/gunicorn \
  --workers 2 \
  --bind 0.0.0.0:5000 \
  --timeout 120 \
  --access-logfile logs/access.log \
  "app:create_app()"
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable incubator
sudo systemctl start incubator

# Nginx config
sudo tee /etc/nginx/sites-available/incubator <<EOF
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }

    location /static/ {
        alias /opt/incubator/static/;
        expires 7d;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/incubator /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Add SSL with Certbot:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

---

### 5b. Docker

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.11-slim

# WeasyPrint system deps
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 libpangocairo-1.0-0 libcairo2 \
    libgdk-pixbuf2.0-0 libffi-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

EXPOSE 5000
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "--timeout", "120", "app:create_app()"]
```

```bash
# Build
docker build -t incubator-agent .

# Run
docker run -d \
  --name incubator \
  -p 5000:5000 \
  --env-file .env \
  -v $(pwd)/database:/app/database \
  -v $(pwd)/logs:/app/logs \
  incubator-agent
```

---

### 5c. Railway / Render / Fly.io

For any PaaS platform:

1. Push your code to GitHub
2. Connect the repo to Railway/Render/Fly.io
3. Set environment variables from section 3 in the platform dashboard
4. Set the start command to:
   ```
   gunicorn --workers 2 --bind 0.0.0.0:$PORT --timeout 120 "app:create_app()"
   ```
5. For **PDF support on Render**, add a build command:
   ```
   apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 && pip install -r requirements.txt
   ```

---

## 6. Database Management

The SQLite database is at `database/incubator.db` by default.

```bash
# Backup
cp database/incubator.db database/incubator.db.backup

# View with sqlite3
sqlite3 database/incubator.db ".tables"

# Run schema migrations (automatic — just restart the app)
# init_db() applies additive migrations safely on every startup
```

For production with heavy traffic, consider migrating to PostgreSQL:
1. Replace `database/db.py` with a psycopg2 adapter
2. Update `DATABASE_PATH` or add a `DATABASE_URL` variable

---

## 7. Customising the AI Mentor

Edit `AGENT_INSTRUCTIONS.yaml` in the project root. Changes take effect immediately (no restart needed).

```yaml
mentor_personality: "direct"      # encouraging | direct | socratic | analytical | visionary
business_tone: "professional"     # professional | casual | academic | startup-friendly | investor-grade
creativity: 8                     # 1 (conservative) to 10 (highly creative)
industry_focus: "Technology"      # leave "" to be industry-agnostic
default_country: "India"          # default when no country is provided
funding_focus: "vc"               # bootstrapping | angel | vc | grants | mixed
writing_style: "bullet-heavy"     # concise | detailed | bullet-heavy | narrative | structured
mentor_name: "Granite Mentor"     # display name in reports
```

You can also toggle individual report sections:
```yaml
sections:
  government_schemes: false   # skip for non-country-specific reports
  weekly_timeline: true
```

---

## 8. PDF & DOCX Export

Export requires:
- **PDF:** `weasyprint` (installed automatically via requirements.txt)
  - On Linux, also install: `libpango-1.0-0 libpangocairo-1.0-0 libcairo2`
  - On Windows, WeasyPrint requires GTK — install from [GTK for Windows Runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer)
- **DOCX:** `python-docx` (installed automatically)

Export buttons appear on:
- `/startup/<id>` → Export Dropdown (PDF / DOCX)
- `/mentor/report/<id>` → Export Dropdown (PDF / DOCX)

---

## 9. Logging

Logs are written to `logs/incubator.log` (rotating, 5 MB × 3 backups).

```bash
# Tail live logs
tail -f logs/incubator.log

# Change log level in development
FLASK_ENV=development python app.py  # DEBUG level
FLASK_ENV=production python app.py   # INFO level
```

---

## 10. Security Checklist

Before going live:

- [ ] Set `FLASK_SECRET_KEY` to a long, random string (32+ characters)
- [ ] Set `FLASK_DEBUG=False` and `FLASK_ENV=production`
- [ ] Enable HTTPS (use Certbot or a platform TLS terminator)
- [ ] Never commit `.env` to version control (it's in `.gitignore`)
- [ ] Restrict `DATABASE_PATH` directory permissions: `chmod 700 database/`
- [ ] Add rate limiting for the `/api/chat/send` endpoint (e.g., Flask-Limiter)
- [ ] Rotate your IBM API key periodically
- [ ] Set up regular database backups

---

## 11. Troubleshooting

| Problem | Solution |
|---------|----------|
| `IBM credentials are not configured` | Set `IBM_API_KEY` and `IBM_PROJECT_ID` in `.env` |
| `WeasyPrint is not installed` | Run `pip install weasyprint`; on Linux install GTK system deps |
| `python-docx is not installed` | Run `pip install python-docx` |
| `yaml` module not found | Run `pip install PyYAML` |
| `No module named 'ibm_watsonx_ai'` | Run `pip install ibm-watsonx-ai==1.1.2` |
| PDF export blank on Windows | Install GTK runtime for WeasyPrint |
| `Database is locked` | Ensure only one process writes at a time; WAL mode is enabled by default |
| App 500 errors | Check `logs/incubator.log` for the full traceback |
| Slow AI generation | Normal; IBM Granite takes 15–60s for large reports |

---

## Project Structure (After Upgrade)

```
AI Startup Incubator Agent/
├── app.py                      # Application factory
├── config.py                   # Flask config
├── AGENT_INSTRUCTIONS.yaml     # 🆕 AI mentor personality config
├── DEPLOYMENT.md               # This file
├── requirements.txt
├── .env                        # Secrets (never commit)
│
├── database/
│   ├── db.py                   # SQLite helpers + schema
│   └── incubator.db            # SQLite database
│
├── models/
│   ├── startup.py              # Startup CRUD + search
│   ├── report.py               # Reports
│   ├── chat.py                 # Chat messages
│   ├── incubation_report.py    # Mentor reports
│   ├── activity.py             # 🆕 Activity log
│   ├── milestone.py            # 🆕 Progress milestones
│   └── profile.py              # 🆕 User profile
│
├── routes/
│   ├── main.py                 # Dashboard, history, activity
│   ├── startup.py              # Create, edit, delete, export
│   ├── mentor.py               # Mentor reports + export
│   ├── chat.py                 # Chat UI
│   ├── api.py                  # JSON API endpoints
│   ├── settings.py             # IBM config status
│   ├── analytics.py            # 🆕 Analytics dashboard
│   ├── progress.py             # 🆕 Progress tracker
│   └── profile.py              # 🆕 Profile settings
│
├── services/
│   ├── watsonx_service.py      # IBM Granite (analysis + chat)
│   └── mentor_ai_service.py    # IBM Granite (mentor reports)
│
├── utils/
│   ├── helpers.py              # Format/score helpers
│   ├── constants.py            # 🆕 Shared dropdown lists
│   ├── validators.py           # 🆕 Input validation
│   ├── export.py               # 🆕 PDF/DOCX export
│   ├── agent_config.py         # 🆕 AGENT_INSTRUCTIONS loader
│   └── logger.py               # 🆕 Logging setup
│
├── templates/
│   ├── base.html               # Layout + global search + toasts
│   ├── landing.html            # Public landing page
│   ├── dashboard.html          # Improved dashboard
│   ├── history.html            # Project list + server-side search
│   ├── detail.html             # Startup detail + export buttons
│   ├── create_startup.html     # Create form
│   ├── edit_startup.html       # 🆕 Edit form
│   ├── chat.html               # AI chat
│   ├── settings.html           # IBM config
│   ├── analytics.html          # 🆕 Analytics dashboard
│   ├── progress_index.html     # 🆕 Progress tracker list
│   ├── progress_detail.html    # 🆕 Progress tracker detail
│   ├── activity.html           # 🆕 Activity log
│   ├── profile.html            # 🆕 Profile settings
│   ├── mentor_form.html        # Mentor form
│   ├── mentor_report.html      # Mentor report + export
│   ├── mentor_history.html     # Mentor report list
│   └── errors/
│       ├── 404.html            # 🆕 Not found page
│       └── 500.html            # 🆕 Server error page
│
├── static/
│   ├── css/main.css            # Dark UI + new components
│   └── js/main.js              # Sidebar, search, toasts, validation
│
└── logs/
    └── incubator.log           # 🆕 Rotating app log
```

---

*Generated by AI Startup Incubator Agent — Production Upgrade*
