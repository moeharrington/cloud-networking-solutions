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
            location=(
                os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_LOCATION")
                or os.environ.get("GOOGLE_CLOUD_LOCATION")
            ),
            agent_engine_id=agent_engine_id,
        )
    return InMemorySessionService()


@functools.cache
def get_artifact_service():
    return InMemoryArtifactService()

