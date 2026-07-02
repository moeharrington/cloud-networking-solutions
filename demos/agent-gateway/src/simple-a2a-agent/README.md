# Simple A2A Agent

Minimal ADK agent served through ADK's `to_a2a` helper and deployable with Google Agents CLI.

```bash
cd demos/agent-gateway/src/simple-a2a-agent
UV_CACHE_DIR=/tmp/uv-cache uv sync
PORT=8000 UV_CACHE_DIR=/tmp/uv-cache uv run uvicorn simple_a2a_agent.fast_api_app:app --host 0.0.0.0 --port 8000
```

Deploy:

```bash
cd demos/agent-gateway/src/simple-a2a-agent
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uvx --from google-agents-cli==0.6.1 agents-cli deploy \
  --project aiti-research-sbx-d928 \
  --region us-central1 \
  --deployment-target agent_runtime \
  --service-name simple-a2a-agent \
  --agent-identity \
  --min-instances 1 \
  --max-instances 1 \
  --num-workers 1 \
  --no-confirm-project
```

The Dockerfile already serves on port 8080. Do not pass `--port 8080` to
`agents-cli deploy`; Agent Runtime rejects `PORT` as a reserved environment
variable.
