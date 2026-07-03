# Mortgage Assistant Agent

ADK mortgage assistant agent deployed to Agent Runtime as an HTTP container.
The container exposes the same agent through:

- A2A JSON-RPC via ADK `to_a2a(...)` at `/a2a/mortgage_agent`
- Vertex AI Playground compatibility via `/api/stream_reasoning_engine`

This mirrors the working `simple-a2a-agent` example. In Agent Runtime, ADK
sessions use Vertex AI session storage so Playground can reload responses after
stream completion. A2A task state uses the default task store from `to_a2a(...)`;
the demo is deployed with one runtime instance.

## Prerequisites

- Terraform infrastructure deployed
- MCP servers registered in Agent Registry and reachable through Agent Gateway
- `uv` installed for local Python commands

## Deploy

Get values from Terraform:

```bash
cd ../../terraform

export PROJECT_ID=$(terraform output -raw foundation_project_id)
export AGENT_GATEWAY=$(terraform output -raw agent_gateway_id)
export MCP_INVOKER_SA=$(terraform output -raw agent_mcp_invoker_email)
```

Create a new Agent Runtime engine:

```bash
cd ../src/mortgage-agent

uv run python deploy_agent.py \
  --project=$PROJECT_ID \
  --agent-gateway=$AGENT_GATEWAY \
  --mcp-invoker-sa=$MCP_INVOKER_SA \
  --enable-agent-identity
```

Update an existing engine:

```bash
uv run python deploy_agent.py \
  --project=$PROJECT_ID \
  --agent-gateway=$AGENT_GATEWAY \
  --mcp-invoker-sa=$MCP_INVOKER_SA \
  --enable-agent-identity \
  --update=projects/PROJECT_NUMBER/locations/us-central1/reasoningEngines/ENGINE_ID
```

The deploy command reads the deployed Reasoning Engine spec after create or
update and fails if `spec.deploymentSpec.agentGatewayConfig` is missing or
points at a different gateway than `--agent-gateway`.
Do not pass `--network-attachment` with `--agent-gateway`: Agent Runtime
rejects deployment specs that set both `pscInterfaceConfig` and
`agentGatewayConfig`.

## A2A Smoke Test

Fetch the agent card:

```bash
ENGINE=projects/PROJECT_NUMBER/locations/us-central1/reasoningEngines/ENGINE_ID
BASE="https://us-central1-aiplatform.googleapis.com/reasoningEngines/v1/${ENGINE}/api"

curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "${BASE}/a2a/mortgage_agent/.well-known/agent-card.json"
```

Send an A2A JSON-RPC message:

```bash
curl -s -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "${BASE}/a2a/mortgage_agent/" \
  -d '{
    "jsonrpc": "2.0",
    "id": "smoke",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "m1",
        "role": "user",
        "parts": [{"kind": "text", "text": "Say hello."}]
      }
    }
  }'
```

## Register in Gemini Enterprise

Add `--ge-deploy` with the required OAuth and Gemini Enterprise flags:

```bash
export OAUTH_CLIENT_SECRET=<your-oauth-client-secret>

uv run python deploy_agent.py \
  --project=$PROJECT_ID \
  --agent-gateway=$AGENT_GATEWAY \
  --mcp-invoker-sa=$MCP_INVOKER_SA \
  --enable-agent-identity \
  --ge-deploy \
  --app-id=<gemini-enterprise-engine-id> \
  --oauth-client-id=<oauth-client-id>
```

## Local Testing

```bash
uv sync
uv run uvicorn agent.fast_api_app:app --host 0.0.0.0 --port 8080
```
