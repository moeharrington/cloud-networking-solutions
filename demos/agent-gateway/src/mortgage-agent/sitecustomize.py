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

"""Process-wide runtime compatibility hooks.

Agent Runtime imports ``sitecustomize`` during interpreter startup when this file
is packaged on ``sys.path``. Keep this module dependency-light: it runs before
the application and before Vertex/ADK telemetry setup.
"""

from __future__ import annotations

import base64
import os
import ssl
from pathlib import Path


def _disable_urllib3_pyopenssl_when_mtls_disabled() -> None:
    """Prevent PyOpenSSL from becoming urllib3's global SSL backend.

    The OTLP HTTP trace exporter uses ``requests``/``urllib3``. In Agent Runtime
    we have seen a later Google auth mTLS setup replace urllib3's stdlib
    ``SSLContext`` with ``urllib3.contrib.pyopenssl.PyOpenSSLContext``. Reusing
    that context can crash span export with:

        ValueError: Context has already been used to create a Connection

    When the deployment explicitly disables Google API client certificates, keep
    urllib3 on the stdlib SSL backend and make later PyOpenSSL injection calls
    harmless.
    """

    if os.getenv("GOOGLE_API_USE_CLIENT_CERTIFICATE", "").lower() != "false":
        return

    try:
        import urllib3.contrib.pyopenssl as pyopenssl

        pyopenssl.extract_from_urllib3()

        def _noop_inject_into_urllib3() -> None:
            pyopenssl.extract_from_urllib3()

        pyopenssl.inject_into_urllib3 = _noop_inject_into_urllib3
    except Exception:
        pass


def _install_agent_gateway_root_certificates() -> None:
    encoded = os.getenv("AGENT_GATEWAY_ROOT_CERTIFICATES_B64")
    if not encoded:
        return

    try:
        extra_pem = base64.b64decode(encoded).decode("utf-8")
    except Exception:
        return

    ca_bundle = Path("/tmp/agent_gateway_ca_bundle.pem")
    parts: list[str] = []
    try:
        import certifi

        parts.append(Path(certifi.where()).read_text())
    except Exception:
        default_cafile = ssl.get_default_verify_paths().cafile
        if default_cafile:
            try:
                parts.append(Path(default_cafile).read_text())
            except Exception:
                pass
    parts.append(extra_pem)

    try:
        ca_bundle.write_text("\n".join(part.rstrip() for part in parts if part) + "\n")
    except Exception:
        return

    os.environ.setdefault("SSL_CERT_FILE", str(ca_bundle))
    os.environ.setdefault("REQUESTS_CA_BUNDLE", str(ca_bundle))
    os.environ.setdefault("GRPC_DEFAULT_SSL_ROOTS_FILE_PATH", str(ca_bundle))


_install_agent_gateway_root_certificates()
_disable_urllib3_pyopenssl_when_mtls_disabled()
