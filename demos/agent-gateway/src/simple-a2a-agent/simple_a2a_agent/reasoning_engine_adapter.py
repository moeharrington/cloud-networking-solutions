import inspect
import json
from collections.abc import AsyncIterator

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route
from vertexai.agent_engines.templates.adk import AdkApp

from simple_a2a_agent import services

_runtime: AdkApp | None = None
_streaming_methods: set[str] = set()
_sync_methods: set[str] = set()
_SESSION_METHODS = {"async_stream_query", "stream_query"}


def _get_runtime() -> AdkApp:
    global _runtime, _streaming_methods, _sync_methods
    if _runtime is None:
        from simple_a2a_agent.agent import app as adk_app

        _runtime = AdkApp(
            app=adk_app,
            session_service_builder=services.get_session_service,
            artifact_service_builder=services.get_artifact_service,
        )
        _runtime.set_up()
        operations = _runtime.register_operations()
        _streaming_methods = set(operations.get("stream", [])) | set(
            operations.get("async_stream", [])
        )
        _sync_methods = set(operations.get("", [])) | set(operations.get("async", []))
    return _runtime


def _resolve_method(class_method: str, *, streaming: bool):
    runtime = _get_runtime()
    allowed = _streaming_methods if streaming else _sync_methods
    if class_method not in allowed:
        return None
    return getattr(runtime, class_method)


async def _runtime_input(body: dict) -> dict:
    runtime_input = dict(body.get("input") or {})
    if body.get("class_method") in _SESSION_METHODS and runtime_input.get("session_id"):
        session_service = _get_runtime()._tmpl_attrs["session_service"]
        app_name = _get_runtime()._tmpl_attrs["app"].name
        user_id = runtime_input["user_id"]
        session_id = runtime_input["session_id"]
        try:
            session = await session_service.get_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id,
            )
        except ValueError:
            runtime_input.pop("session_id", None)
        else:
            if session is None:
                await session_service.create_session(
                    app_name=app_name,
                    user_id=user_id,
                    session_id=session_id,
                )
    return runtime_input


async def stream_reasoning_engine(request: Request) -> StreamingResponse | JSONResponse:
    body = await request.json()
    method = _resolve_method(body.get("class_method", ""), streaming=True)
    if method is None:
        return JSONResponse(
            {"detail": f"Unsupported reasoning_engine method: {body.get('class_method')!r}"},
            status_code=404,
        )
    runtime_input = await _runtime_input(body)

    async def generator() -> AsyncIterator[str]:
        async for event in method(**runtime_input):
            yield json.dumps(event) + "\n"

    return StreamingResponse(generator(), media_type="application/json")


async def reasoning_engine(request: Request) -> JSONResponse:
    body = await request.json()
    method = _resolve_method(body.get("class_method", ""), streaming=False)
    if method is None:
        return JSONResponse(
            {"detail": f"Unsupported reasoning_engine method: {body.get('class_method')!r}"},
            status_code=404,
        )
    runtime_input = await _runtime_input(body)
    if inspect.iscoroutinefunction(method):
        output = await method(**runtime_input)
    else:
        output = method(**runtime_input)
    return JSONResponse({"output": output})


def attach_reasoning_engine_routes(app: Starlette) -> None:
    for path in ("/api/stream_reasoning_engine", "/stream_reasoning_engine"):
        app.routes.append(Route(path, stream_reasoning_engine, methods=["POST"]))
    for path in ("/api/reasoning_engine", "/reasoning_engine"):
        app.routes.append(Route(path, reasoning_engine, methods=["POST"]))
