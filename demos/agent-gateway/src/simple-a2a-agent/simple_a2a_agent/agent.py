import os

import google.auth
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

if "GOOGLE_CLOUD_PROJECT" not in os.environ:
    _, project_id = google.auth.default()
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
os.environ["GOOGLE_CLOUD_LOCATION"] = os.getenv("MODEL_LOCATION", "global")

root_agent = Agent(
    name="simple_a2a_agent",
    model=Gemini(
        model=os.getenv("MODEL_NAME", "gemini-3.1-flash-lite-preview"),
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    description="Minimal A2A test agent.",
    instruction=(
        "You are a minimal A2A test agent. Reply directly in one concise sentence. "
        "Do not call tools."
    ),
)

app = App(root_agent=root_agent, name="simple_a2a_agent")
