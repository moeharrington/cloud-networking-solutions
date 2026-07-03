# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for deploy-time Reasoning Engine verification."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from deploy_agent import _verify_agent_gateway_config


def test_verify_agent_gateway_config_accepts_proto_style_object():
    engine = SimpleNamespace(
        api_resource=SimpleNamespace(
            name="projects/p/locations/us-central1/reasoningEngines/1",
            spec=SimpleNamespace(
                deployment_spec=SimpleNamespace(
                    agent_gateway_config=SimpleNamespace(
                        agent_to_anywhere_config=SimpleNamespace(
                            agent_gateway="projects/p/locations/us-central1/agentGateways/gw"
                        )
                    )
                )
            ),
        )
    )

    _verify_agent_gateway_config(engine, "projects/p/locations/us-central1/agentGateways/gw")


def test_verify_agent_gateway_config_accepts_camel_case_dict():
    engine = {
        "name": "projects/p/locations/us-central1/reasoningEngines/1",
        "spec": {
            "deploymentSpec": {
                "agentGatewayConfig": {
                    "agentToAnywhereConfig": {
                        "agentGateway": "projects/p/locations/us-central1/agentGateways/gw",
                    }
                }
            }
        },
    }

    _verify_agent_gateway_config(engine, "projects/p/locations/us-central1/agentGateways/gw")


def test_verify_agent_gateway_config_fails_when_missing():
    engine = {"name": "projects/p/locations/us-central1/reasoningEngines/1", "spec": {"deploymentSpec": {}}}

    with pytest.raises(RuntimeError, match="missing spec.deploymentSpec.agentGatewayConfig"):
        _verify_agent_gateway_config(engine, "projects/p/locations/us-central1/agentGateways/gw")


def test_verify_agent_gateway_config_fails_on_unexpected_gateway():
    engine = {
        "spec": {
            "deploymentSpec": {
                "agentGatewayConfig": {
                    "agentToAnywhereConfig": {
                        "agentGateway": "projects/p/locations/us-central1/agentGateways/other",
                    }
                }
            }
        },
    }

    with pytest.raises(RuntimeError, match="unexpected Agent Gateway"):
        _verify_agent_gateway_config(engine, "projects/p/locations/us-central1/agentGateways/gw")
