# FastHTML Agentforce API Client

A clean, production-ready web chat interface for Salesforce Agentforce API built with FastHTML and Python.

## ✨ Features

- **Web Chat Interface** - Clean, modern UI with Bootstrap 5.3.0 styling
- **Real-time AJAX** - HTMX-powered dynamic message updates without page reloads
- **Automatic Session Management** - Creates and maintains Agentforce conversation sessions
- **Auto-clearing Input** - Message input clears automatically after sending
- **Chat Bubbles** - User messages (blue, right-aligned) and Agent messages (green, left-aligned)
- **Error Handling** - User-friendly error messages with red error bubbles
- **OAuth2 Authentication** - Secure client credentials flow with Salesforce

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

## 🛠 Salesforce Setup

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
main.py              - FastHTML application (380 lines)
requirements.txt     - Dependencies: fasthtml, httpx, python-dotenv
.env.example        - Configuration template
.gitignore          - Git ignore rules
README.md           - This file
```

## 🏗️ Architecture & Methods

### Backend Classes

#### `AgentforceConfig` (Dataclass)
Stores Salesforce configuration credentials.

**Attributes:**
- `instance_url` - Salesforce org domain
- `client_id` - OAuth2 client ID
- `client_secret` - OAuth2 client secret
- `agent_id` - Published Agentforce agent ID

#### `AgentforceClient` (Main API Client)

**Methods:**

##### `__init__(config: AgentforceConfig)`
Initializes the client with configuration and sets up token/URL storage.

##### `async authenticate() → None`
Performs OAuth2 client credentials authentication with Salesforce.

**Steps:**
1. Sends POST to `/services/oauth2/token` endpoint
2. Includes `client_id`, `client_secret`, `grant_type=client_credentials`
3. Validates required OAuth scopes: `sfap_api`, `chatbot_api`, `api`
4. Stores `access_token` and `api_instance_url` for later requests
5. Raises exception if authentication fails or scopes missing

**Usage:** Called automatically on first message if not already authenticated

##### `async create_session() → str`
Creates a new Agentforce conversation session.

**Steps:**
1. Validates authentication (must call `authenticate()` first)
2. Sends POST to `/einstein/ai-agent/v1/agents/{agentId}/sessions`
3. Includes session metadata and feature support options
4. Returns `sessionId` for message exchange
5. Session persists across multiple messages

**Parameters:** None (uses stored config)  
**Returns:** Session ID string  
**Usage:** Called once, stored in global `current_session_id`

##### `async send_sync_message(session_id: str, message: str, variables: list = None) → Dict[str, Any]`
Sends a user message to the agent and receives response.

**Steps:**
1. Validates authentication
2. Creates message payload with:
   - `sequenceId` - Timestamp-based unique ID
   - `type` - Message type (always "Text")
   - `text` - User message content
3. Sends POST to `/einstein/ai-agent/v1/sessions/{sessionId}/messages`
4. Returns full JSON response with agent message

**Parameters:**
- `session_id` - Active session ID
- `message` - User message text
- `variables` - Optional context variables (default: empty list)

**Returns:** Dictionary with structure:
```python
{
  "sessionId": "...",
  "messages": [
    {
      "type": "Inform",
      "message": "Agent response text",
      "id": "...",
      "isContentSafe": bool,
      "metrics": {},
      "result": [],
      "citedReferences": []
    }
  ],
  "links": {...}
}
```

**Usage:** Called for each user message in chat

### Frontend Functions

#### `build_dynamic_ui(response: Dict[str, Any]) → Any`
Converts Agentforce API response to HTML for display.

**Logic:**
1. Validates response is dictionary
2. Extracts `messages` array from response
3. Finds first message with `type="Inform"`
4. Extracts and returns the `message` text field
5. Falls back to formatted JSON if no message found

**Parameters:** API response dictionary  
**Returns:** FastHTML `P` (paragraph) component with message text  
**Usage:** Called in `/chat` route to display agent response

### FastHTML Routes

#### `GET /`
Renders the main chat interface page.

**Function:** `home()`

**Logic:**
1. Loads configuration from environment
2. Validates all required credentials present
3. If missing: displays error alert with required env vars
4. If valid: initializes global `AgentforceClient`
5. Returns HTML page with:
   - Chat header ("AI Agent Assistant")
   - Scrollable message container (500px height, light gray bg)
   - Input form with textarea + send button
   - HTMX attributes for AJAX

**Returns:** Full HTML page

**HTMX Integration:**
- Form uses `hx_post="/chat"` for AJAX submission
- `hx_target="#chat-container"` inserts responses into message container
- `hx_swap="beforeend swap:1s"` appends new messages with 1s animation
- `hx_on__after_request` clears input field after send

#### `POST /chat`
Handles incoming user messages.

**Function:** `async chat(message: str)`

**Logic:**
1. Validates client initialized
2. Authenticates if not already done (calls `authenticate()`)
3. Creates session if not exists (calls `create_session()`)
4. Sends user message to agent (calls `send_sync_message()`)
5. Creates two message bubbles:
   - **User bubble:** Blue (#0d6efd), white text, right-aligned (20% margin-left)
   - **Agent bubble:** Green (#d1e7dd), dark text (#0f5132), left-aligned (20% margin-right)
6. Generates UI from response (calls `build_dynamic_ui()`)
7. Returns both bubbles as HTML partial

**Returns:** HTML `Div` with both user and agent message bubbles

**Error Handling:**
- Catches exceptions and returns red error bubble (#f8d7da)
- Displays error message to user
- Continues session for next message attempt

### Global Variables

```python
agentforce_client: Optional[AgentforceClient] = None
# Stores client instance for entire session

current_session_id: Optional[str] = None
# Stores Agentforce session ID across multiple messages
```

### Helper Functions

#### `load_config() → AgentforceConfig`
Loads configuration from environment variables.

**Returns:** `AgentforceConfig` object with credentials

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
| **Input not clearing** | Ensure HTMX is loaded (included in CDN links) |
| **Messages not sending** | Check internet connection and Salesforce API rate limits |
| **404 on endpoints** | Verify Einstein Sales Cloud is enabled in Salesforce org |

## 📚 Dependencies

- **fasthtml** - Web framework for building apps with Python functions
- **httpx** - Async HTTP client for API calls
- **python-dotenv** - Loads environment variables from `.env`

## 📝 License

Open source. Please check individual component licenses.
