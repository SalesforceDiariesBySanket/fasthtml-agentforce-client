#!/usr/bin/env python3
"""
FastHTML Agentforce API Client
A web interface for interacting with Salesforce Agentforce API
"""

import os
import json
from typing import Optional, Dict, Any
import httpx
from fasthtml.common import *
from dataclasses import dataclass
from datetime import datetime

# Agentforce API configuration
@dataclass
class AgentforceConfig:
    instance_url: str
    client_id: str
    client_secret: str
    agent_id: str

class AgentforceClient:
    """Python client for Salesforce Agentforce API"""

    def __init__(self, config: AgentforceConfig):
        self.config = config
        self.access_token: Optional[str] = None
        self.api_instance_url: Optional[str] = None

    async def authenticate(self) -> None:
        """Authenticate with Salesforce using OAuth2 client credentials"""
        auth_url = f"{self.config.instance_url}/services/oauth2/token"

        data = {
            'grant_type': 'client_credentials',
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret
        }

        print(f"DEBUG: Authenticating with URL: {auth_url}")
        print(f"DEBUG: Client ID: {self.config.client_id[:10]}...")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                auth_url,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            print(f"DEBUG: Auth response status: {response.status_code}")
            print(f"DEBUG: Auth response body: {response.text}")

            if not response.is_success:
                raise Exception(f"Authentication failed: {response.status_code} - {response.text}")

            auth_data = response.json()

            # Check required scopes
            scopes = set(auth_data.get('scope', '').split(' '))
            required_scopes = {'sfap_api', 'chatbot_api', 'api'}

            if not required_scopes.issubset(scopes):
                raise Exception(f"Missing required OAuth scopes. Required: {required_scopes}, Found: {scopes}")

            self.access_token = auth_data['access_token']
            self.api_instance_url = auth_data['api_instance_url']

            print(f"DEBUG: Authentication successful. API URL: {self.api_instance_url}")

    async def create_session(self) -> str:
        """Create a new agent session"""
        if not self.access_token or not self.api_instance_url:
            raise Exception("Client not authenticated")

        session_url = f"{self.api_instance_url}/einstein/ai-agent/v1/agents/{self.config.agent_id}/sessions"

        session_data = {
            "externalSessionKey": f"fasthtml-{datetime.now().timestamp()}",
            "instanceConfig": {
                "endpoint": self.config.instance_url
            },
            "featureSupport": "Streaming",
            "streamingCapabilities": {
                "chunkTypes": ["Text"]
            },
            "bypassUser": True
        }

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        print(f"DEBUG: Creating session with URL: {session_url}")
        print(f"DEBUG: Session data: {json.dumps(session_data, indent=2)}")
        print(f"DEBUG: Headers: {headers}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                session_url,
                json=session_data,
                headers=headers
            )

            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response headers: {dict(response.headers)}")
            print(f"DEBUG: Response body: {response.text}")

            if not response.is_success:
                raise Exception(f"Session creation failed: {response.status_code} - {response.text}")

            session_info = response.json()
            return session_info['sessionId']

    async def send_sync_message(self, session_id: str, message: str, variables: list = None) -> Dict[str, Any]:
        """Send a synchronous message to the agent"""
        if not self.access_token or not self.api_instance_url:
            raise Exception("Client not authenticated")

        if variables is None:
            variables = []

        message_url = f"{self.api_instance_url}/einstein/ai-agent/v1/sessions/{session_id}/messages"

        message_data = {
            "message": {
                "sequenceId": int(datetime.now().timestamp() * 1000),
                "type": "Text",
                "text": message
            },
            "variables": variables
        }

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                message_url,
                json=message_data,
                headers=headers
            )

            if not response.is_success:
                raise Exception(f"Message send failed: {response.status_code} - {response.text}")

            return response.json()

def build_dynamic_ui(response: Dict[str, Any]) -> Any:
    """
    Build dynamic UI based on Agentforce API response structure.
    Extracts ONLY the agent message text for user-friendly display.
    """
    if not isinstance(response, dict):
        return P(str(response))
    
    # Extract message text from response
    if 'messages' in response and isinstance(response['messages'], list):
        for msg in response['messages']:
            if isinstance(msg, dict) and 'message' in msg:
                message_text = msg.get('message', '').strip()
                if message_text:
                    return P(message_text, cls="mb-0")
    
    # Fallback: show formatted response
    return P(json.dumps(response, indent=2), cls="mb-0", style="font-size: 0.9em;")

# FastHTML Application
app, rt = fast_app(
    hdrs=(
        Link(rel='stylesheet', href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css'),
        Script(src='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js'),
    )
)

# Global client instance
agentforce_client: Optional[AgentforceClient] = None
current_session_id: Optional[str] = None

def load_config() -> AgentforceConfig:
    """Load configuration from environment variables"""
    return AgentforceConfig(
        instance_url=os.getenv('SALESFORCE_INSTANCE_URL', ''),
        client_id=os.getenv('SALESFORCE_CLIENT_ID', ''),
        client_secret=os.getenv('SALESFORCE_CLIENT_SECRET', ''),
        agent_id=os.getenv('SALESFORCE_AGENT_ID', '')
    )

@rt('/')
def home():
    """Home page with configuration and chat interface"""
    global agentforce_client

    config = load_config()
    config_valid = all([
        config.instance_url,
        config.client_id,
        config.client_secret,
        config.agent_id
    ])

    if not config_valid:
        return Titled("Agentforce API Client - Configuration Required",
            Div(
                P("Configuration Required", style="font-size: 1.5em; font-weight: bold;"),
                P("Please set the following environment variables:"),
                Div(
                    P(" SALESFORCE_INSTANCE_URL - Your Salesforce org domain"),
                    P(" SALESFORCE_CLIENT_ID - Connected app client ID"),
                    P(" SALESFORCE_CLIENT_SECRET - Connected app client secret"),
                    P(" SALESFORCE_AGENT_ID - Agent ID"),
                    style="margin-left: 20px;"
                ),
                P("Create a .env file in the project root with these values."),
                cls="alert alert-warning"
            )
        )

    # Initialize client if not already done
    if agentforce_client is None:
        agentforce_client = AgentforceClient(config)

    return Titled("Agentforce AI Agent Chat",
        Div(
            Div(
                # Chat messages container - messages appear here
                Div(
                    id="chat-container",
                    cls="mb-4 p-3 rounded",
                    style="height: 500px; overflow-y: auto; background-color: #f8f9fa; border: 1px solid #dee2e6;"
                ),
                
                # Input form at the bottom
                Form(
                    Div(
                        Div(
                            Textarea(
                                id="message",
                                name="message",
                                cls="form-control",
                                rows=3,
                                placeholder="Type your message and press Send...",
                                style="resize: vertical;"
                            ),
                            cls="mb-2"
                        ),
                        Div(
                            Button("Send Message", type="submit", cls="btn btn-primary w-100"),
                            cls=""
                        ),
                        cls="mb-0"
                    ),
                    id="chat-form",
                    method="post",
                    action="/chat",
                    hx_post="/chat",
                    hx_target="#chat-container",
                    hx_swap="beforeend swap:1s",
                    hx_on__after_request="document.querySelector('#message').value = ''",
                    cls="border-top pt-3"
                ),
                
                cls="container-fluid"
            ),
            cls="d-flex flex-column",
            style="height: 100vh;"
        ),
        style="padding: 0;"
    )

@rt('/chat', methods=['POST'])
async def chat(message: str):
    """Handle chat message - uses dynamic UI generation"""
    global agentforce_client, current_session_id

    if not agentforce_client:
        return Div("Client not initialized", cls="alert alert-danger")

    try:
        # Authenticate if not already done
        if not agentforce_client.access_token:
            await agentforce_client.authenticate()

        # Create session if not exists
        if not current_session_id:
            current_session_id = await agentforce_client.create_session()

        # Send message
        response = await agentforce_client.send_sync_message(current_session_id, message)

        # Create user message bubble
        user_bubble = Div(
            P(message, cls="mb-0"),
            cls="mb-2 p-2 rounded",
            style="background-color: #0d6efd; color: white; margin-left: 20%; border-radius: 8px;"
        )

        # Generate DYNAMIC UI based on response structure
        dynamic_agent_ui = build_dynamic_ui(response)
        
        # Create agent message bubble with dynamic content
        agent_bubble = Div(
            dynamic_agent_ui,
            cls="mb-2 p-3 rounded",
            style="background-color: #d1e7dd; color: #0f5132; margin-right: 20%; border-radius: 8px;"
        )

        # Return both messages
        response_html = Div(
            user_bubble,
            agent_bubble,
            cls="chat-exchange"
        )

        return response_html

    except Exception as e:
        error_bubble = Div(
            P(f"Error: {str(e)}", cls="mb-0"),
            cls="mb-2 p-2 rounded",
            style="background-color: #f8d7da; color: #842029; margin-right: 20%; border-radius: 8px;"
        )
        return error_bubble

if __name__ == '__main__':
    # Load environment variables from .env file if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

