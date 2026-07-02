import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from a2a.types import AgentCapabilities, AgentCard, AgentSkill, TransportProtocol
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from simple_a2a_agent.agent import root_agent
from simple_a2a_agent.reasoning_engine_adapter import attach_reasoning_engine_routes

AGENT_DIRECTORY = "simple_a2a_agent"
A2A_PATH = f"/a2a/{AGENT_DIRECTORY}"


async def health(_: object) -> JSONResponse:
    return JSONResponse({"status": "ok"})


def runtime_api_base_url() -> str:
    if app_url := os.getenv("APP_URL"):
        return app_url.rstrip("/")

    agent_engine_id = os.getenv("GOOGLE_CLOUD_AGENT_ENGINE_ID")
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_AGENT_ENGINE_LOCATION", "us-central1")
    if agent_engine_id and project:
        return (
            f"https://{location}-aiplatform.googleapis.com/reasoningEngines/v1"
            f"/projects/{project}/locations/{location}/reasoningEngines/{agent_engine_id}/api"
        )

    port = os.getenv("PORT", "8080")
    return f"http://localhost:{port}"


def build_agent_card() -> AgentCard:
    return AgentCard(
        name="simple-a2a-agent",
        description="Minimal ADK agent exposed through the A2A protocol.",
        url=f"{runtime_api_base_url()}{A2A_PATH}",
        version=os.getenv("AGENT_VERSION", "0.1.0"),
        preferred_transport=TransportProtocol.jsonrpc,
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[
            AgentSkill(
                id="simple_chat",
                name="Simple chat",
                description="Replies directly to a short user message.",
                tags=["chat", "a2a", "adk"],
                examples=["Reply with hello."],
            )
        ],
    )


a2a_app = to_a2a(root_agent, agent_card=build_agent_card())


@asynccontextmanager
async def lifespan(_: Starlette) -> AsyncIterator[None]:
    async with a2a_app.router.lifespan_context(a2a_app):
        yield

app = Starlette(
    routes=[
        Route("/health", health, methods=["GET"]),
        Mount(A2A_PATH, app=a2a_app),
    ],
    lifespan=lifespan,
)
attach_reasoning_engine_routes(app)
