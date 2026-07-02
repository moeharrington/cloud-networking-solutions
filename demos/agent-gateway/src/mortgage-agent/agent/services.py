import functools
import os

from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.sessions.in_memory_session_service import InMemorySessionService


@functools.cache
def get_session_service():
    if agent_engine_id := os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID"):
        from google.adk.sessions.vertex_ai_session_service import VertexAiSessionService

        return VertexAiSessionService(
            project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
            location=_agent_engine_location(),
            agent_engine_id=agent_engine_id,
        )
    return InMemorySessionService()


@functools.cache
def get_artifact_service():
    return InMemoryArtifactService()


def _agent_engine_location() -> str | None:
    for name in (
        "GOOGLE_CLOUD_AGENT_ENGINE_LOCATION",
        "AGENT_ENGINE_LOCATION",
        "MCP_REGISTRY_LOCATION",
        "REGION",
    ):
        if value := os.environ.get(name):
            return value

    model_location = os.environ.get("GOOGLE_CLOUD_LOCATION")
    if model_location and model_location != "global":
        return model_location

    return "us-central1"
