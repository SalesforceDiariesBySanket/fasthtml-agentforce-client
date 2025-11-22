# FastHTML Agentforce API Client

A clean, production-ready web chat interface for Salesforce Agentforce API built with FastHTML and Python. No external frontend frameworks or legacy AJAX—only FastHTML, HTMX attributes, and pure CSS.

<img width="958" height="473" alt="image" src="https://github.com/user-attachments/assets/33260236-3a6f-4cda-8fbd-b41b5b896b76" />


## ✨ Features

- **Web Chat Interface** – Clean, modern UI with pure FastHTML and custom CSS (no Bootstrap)
- **Real-time Dynamic Updates** – HTMX attributes for seamless message updates (no AJAX/JS)
- **Automatic Session Management** – Creates and maintains Agentforce conversation sessions
- **Auto-clearing Input** – Message input clears automatically after sending
- **Chat Bubbles** – User messages (blue, right-aligned) and Agent messages (green, left-aligned)
- **Error Handling** – User-friendly error messages with red error bubbles
- **OAuth2 Authentication** – Secure client credentials flow with Salesforce

## 📋 Prerequisites

- Python 3.8+
- Salesforce org with Agentforce enabled
- Agentforce agent published and configured

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
```

Edit `.env` with your Salesforce credentials:
```env
SALESFORCE_INSTANCE_URL=https://yourorg.my.salesforce.com
SALESFORCE_CLIENT_ID=your_connected_app_client_id
SALESFORCE_CLIENT_SECRET=your_connected_app_secret
SALESFORCE_AGENT_ID=your_published_agent_id
```

### 3. Run
```bash
python main.py
```

Open browser: `http://localhost:8000`

## 🔧 Salesforce Setup

### Enable Agentforce
1. **Setup** → **Einstein Sales** → **Settings** → Enable Einstein Sales Cloud
2. **Setup** → **Einstein Sales** → **Agents** → Create/publish agent
3. Copy the **Agent ID** from agent details

### Create Connected App
1. **Setup** → **App Manager** → **New Connected App**
2. Enable OAuth Settings:
   - Callback URL: `https://login.salesforce.com`
   - OAuth Scopes: `api`, `refresh_token`, `offline_access`, `sfap_api`, `chatbot_api`
3. Get **Client ID** and **Client Secret**

## 📁 Project Structure

```
main.py              - FastHTML application (no external frontend frameworks)
requirements.txt     - Dependencies: fasthtml, httpx, python-dotenv
.env.example         - Configuration template
.gitignore           - Git ignore rules
README.md            - This file
```

## 🏗️ Architecture & Methods

### Backend Classes

#### `AgentforceConfig` (Dataclass)
Stores Salesforce configuration credentials.

#### `AgentforceClient` (Main API Client)
Handles authentication, session creation, and message exchange with Salesforce Agentforce API using `httpx` (Python only).

### Frontend Functions

#### `build_dynamic_ui(response: Dict[str, Any]) → Any`
Converts Agentforce API response to FastHTML components for display. No JavaScript or external libraries used.

### FastHTML Routes

- `GET /` – Renders the main chat interface page using FastHTML components and custom CSS.
- `POST /chat` – Handles incoming user messages, authenticates, manages session, and returns chat bubbles.

### HTMX Integration

- Form uses `hx_post="/chat"` for dynamic submission (no AJAX/JS code)
- `hx_target="#chat-container"` inserts responses into message container
- `hx_swap="beforeend swap:1s"` appends new messages with animation
- `hx_on__after_request` clears input field after send

### Global Variables

- `agentforce_client: Optional[AgentforceClient]` – Stores client instance for session
- `current_session_id: Optional[str]` – Stores Agentforce session ID

### Helper Functions

- `load_config()` – Loads configuration from environment variables

## 🔐 Security

✅ OAuth2 client credentials (not user password)
✅ Credentials in `.env` (excluded from git via `.gitignore`)
✅ Session-based (no token exposed to frontend)
✅ Error messages sanitized (no credential leakage)
✅ HTTPS recommended for production

## 🎯 Message Flow

```
User Input
    ↓
[HTMX Form Submit] → hx_post="/chat"
    ↓
POST /chat Route
    ↓
[Authenticate if needed] → AgentforceClient.authenticate()
    ↓
[Create session if needed] → AgentforceClient.create_session()
    ↓
[Send message] → AgentforceClient.send_sync_message()
    ↓
[Build UI] → build_dynamic_ui()
    ↓
[Return HTML bubbles]
    ↓
[HTMX inserts into #chat-container]
    ↓
[Input clears] → hx_on__after_request
    ↓
Chat Updates on Screen
```

## ❓ Troubleshooting

| Issue | Solution |
|-------|----------|
| **Authentication Failed** | Check `.env` credentials and OAuth scopes in Connected App |
| **Agent Not Found** | Verify Agent ID is correct and agent is published |
| **Input not clearing** | Ensure HTMX attributes are present in the form |
| **Messages not sending** | Check internet connection and Salesforce API rate limits |
| **404 on endpoints** | Verify Einstein Sales Cloud is enabled in Salesforce org |

## 📚 Dependencies

- **fasthtml** – Web framework for building apps with Python functions
- **httpx** – Async HTTP client for API calls
- **python-dotenv** – Loads environment variables from `.env`

## 📝 License

Open source. Please check individual component licenses.
