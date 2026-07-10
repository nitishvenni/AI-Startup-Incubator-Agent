# AI Startup Incubator Agent

> An AI-powered startup mentor that helps entrepreneurs validate startup ideas and receive professional business guidance — built with **Python Flask** and **IBM Granite** via **IBM watsonx.ai**.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🚀 **AI Business Analysis** | Submit your startup idea and receive a full multi-dimensional report from IBM Granite |
| 📊 **Score Dashboard** | Viability, Market Fit, Innovation, and Execution scores with visual radar charts |
| 💬 **AI Mentor Chat** | Free-form conversational AI mentor with project-aware context |
| 📁 **Project History** | Browse, search, and filter all past startup analyses |
| 🎨 **Dark Glassmorphism UI** | Beautiful, responsive Bootstrap 5 interface with animated charts |
| 🔒 **Secure Credentials** | All IBM credentials loaded exclusively from `.env` — nothing hardcoded |
| 🗄️ **SQLite Database** | Lightweight embedded database — zero external dependencies |

---

## 🏗️ Project Structure

```
AI Startup Incubator Agent/
├── app.py                     # Application factory & entry point
├── config.py                  # Environment-based configuration
├── requirements.txt           # Python dependencies
├── .env.example               # Credential template
├── .gitignore
│
├── database/
│   ├── __init__.py
│   └── db.py                  # SQLite connection helper + schema init
│
├── models/
│   ├── __init__.py
│   ├── startup.py             # startup_projects table helpers
│   ├── report.py              # reports table helpers
│   └── chat.py                # chat_messages table helpers
│
├── routes/
│   ├── __init__.py
│   ├── main.py                # Landing + Dashboard + History
│   ├── startup.py             # Create / View / Delete / Re-analyze
│   ├── chat.py                # Chat page
│   ├── api.py                 # AJAX JSON API
│   └── settings.py            # Settings page
│
├── services/
│   ├── __init__.py
│   └── watsonx_service.py     # IBM Granite integration
│
├── utils/
│   ├── __init__.py
│   └── helpers.py             # Utility functions
│
├── templates/
│   ├── base.html              # Sidebar layout shell
│   ├── landing.html           # Public landing page
│   ├── dashboard.html         # Main dashboard with charts
│   ├── create_startup.html    # Multi-step submission form
│   ├── detail.html            # AI report detail view
│   ├── history.html           # Project history list
│   ├── chat.html              # AI mentor chat interface
│   └── settings.html          # Credential status & setup guide
│
└── static/
    ├── css/
    │   ├── main.css           # Dark glassmorphism design system
    │   └── landing.css        # Landing page specific styles
    └── js/
        └── main.js            # Sidebar, animations, loading overlay
```

---

## ⚙️ Prerequisites

- **Python 3.11+**
- An **IBM Cloud account** (free tier works)
- An **IBM watsonx.ai project** with Granite model access

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-username/ai-startup-incubator.git
cd ai-startup-incubator
```

### 2. Create and activate a virtual environment

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure IBM credentials

```bash
cp .env.example .env
```

Open `.env` and fill in your credentials:

```env
IBM_API_KEY=your_ibm_api_key_here
IBM_PROJECT_ID=your_ibm_project_id_here
IBM_URL=https://us-south.ml.cloud.ibm.com
IBM_MODEL=ibm/granite-13b-instruct-v2

FLASK_SECRET_KEY=a-long-random-secret-key
FLASK_ENV=development
FLASK_DEBUG=True
```

#### Where to find your credentials:

| Credential | Where to get it |
|---|---|
| `IBM_API_KEY` | [cloud.ibm.com/iam/apikeys](https://cloud.ibm.com/iam/apikeys) → Create an API key |
| `IBM_PROJECT_ID` | [dataplatform.cloud.ibm.com](https://dataplatform.cloud.ibm.com) → Your Project → Manage → Project ID |
| `IBM_URL` | Use `https://us-south.ml.cloud.ibm.com` for Dallas region |
| `IBM_MODEL` | See table below |

#### Available IBM Granite Models

| Model ID | Use Case |
|---|---|
| `ibm/granite-13b-instruct-v2` | Best for detailed analysis — **Recommended** |
| `ibm/granite-3-8b-instruct` | Faster, lighter model |
| `ibm/granite-20b-multilingual` | Non-English startup contexts |

### 5. Run the application

```bash
python app.py
```

Open your browser at **[http://localhost:5000](http://localhost:5000)**

---

## 📋 Application Pages

| URL | Page | Description |
|---|---|---|
| `/` | Landing Page | Public marketing page |
| `/dashboard` | Dashboard | Stats, charts, recent activity |
| `/startup/create` | Create Startup | Submit your startup idea for analysis |
| `/startup/<id>` | Analysis Report | Full AI report with scores and charts |
| `/history` | Project History | Searchable list of all projects |
| `/chat` | AI Mentor Chat | Free-form chat with IBM Granite |
| `/settings` | Settings | Credential status and setup guide |

---

## 🗄️ Database Schema

### `users`
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment ID |
| `name` | TEXT | User name |
| `email` | TEXT UNIQUE | User email |
| `created_at` | TEXT | Timestamp |

### `startup_projects`
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment ID |
| `startup_name` | TEXT | Name of the startup |
| `founder_name` | TEXT | Founder's name |
| `country` | TEXT | Country of operation |
| `industry` | TEXT | Industry sector |
| `budget` | TEXT | Budget range |
| `target_audience` | TEXT | Target market |
| `business_goal` | TEXT | Strategic goal |
| `idea_description` | TEXT | Full idea description |
| `status` | TEXT | `pending` or `analyzed` |

### `reports`
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment ID |
| `project_id` | INTEGER FK | Linked startup project |
| `content` | TEXT | Full markdown report from Granite |
| `viability_score` | INTEGER | 0–100 score |
| `market_score` | INTEGER | 0–100 score |
| `innovation_score` | INTEGER | 0–100 score |
| `execution_score` | INTEGER | 0–100 score |

### `chat_messages`
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment ID |
| `project_id` | INTEGER FK | Optional project context |
| `role` | TEXT | `user` or `assistant` |
| `content` | TEXT | Message content |

---

## 🔧 Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `IBM_API_KEY` | ✅ | — | IBM Cloud API Key |
| `IBM_PROJECT_ID` | ✅ | — | watsonx.ai Project ID |
| `IBM_URL` | ✅ | `https://us-south.ml.cloud.ibm.com` | watsonx.ai endpoint |
| `IBM_MODEL` | ✅ | `ibm/granite-13b-instruct-v2` | Granite model ID |
| `FLASK_SECRET_KEY` | ✅ | — | Flask session secret |
| `FLASK_ENV` | ❌ | `development` | `development` or `production` |
| `FLASK_DEBUG` | ❌ | `True` | Enable debug mode |
| `DATABASE_PATH` | ❌ | `database/incubator.db` | SQLite file path |

---

## 🧑‍💻 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, Flask 3.0 |
| AI Model | IBM Granite (via watsonx.ai) |
| Database | SQLite 3 |
| Frontend | Bootstrap 5.3, Chart.js 4.4 |
| Icons | Bootstrap Icons 1.11 |
| Fonts | Inter (Google Fonts) |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- **IBM watsonx.ai** and the **IBM Granite** foundation model team
- **Bootstrap** for the UI framework
- **Chart.js** for beautiful data visualizations
