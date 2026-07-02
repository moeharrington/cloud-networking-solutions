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
export VPC_NAME=$(terraform output -raw vpc_name)
export PSC_ATTACHMENT=$(terraform output -raw psc_interface_network_attachment_id)
export DNS_PEERING_DOMAIN=$(terraform output -raw psc_interface_dns_peering_domain)
```

Create a new Agent Runtime engine:

```bash
cd ../src/mortgage-agent

uv run python deploy_agent.py \
  --project=$PROJECT_ID \
  --network-attachment=$PSC_ATTACHMENT \
  --dns-peering-domain=$DNS_PEERING_DOMAIN \
  --dns-peering-target-project=$PROJECT_ID \
  --dns-peering-target-network=$VPC_NAME \
  --enable-agent-identity
```

Update an existing engine:

```bash
uv run python deploy_agent.py \
  --project=$PROJECT_ID \
  --network-attachment=$PSC_ATTACHMENT \
  --dns-peering-domain=$DNS_PEERING_DOMAIN \
  --dns-peering-target-project=$PROJECT_ID \
  --dns-peering-target-network=$VPC_NAME \
  --enable-agent-identity \
  --update=projects/PROJECT_NUMBER/locations/us-central1/reasoningEngines/ENGINE_ID
```

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
  --network-attachment=$PSC_ATTACHMENT \
  --dns-peering-domain=$DNS_PEERING_DOMAIN \
  --dns-peering-target-project=$PROJECT_ID \
  --dns-peering-target-network=$VPC_NAME \
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
