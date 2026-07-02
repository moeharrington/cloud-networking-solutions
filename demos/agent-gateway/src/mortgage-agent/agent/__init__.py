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

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

def _disable_urllib3_pyopenssl_when_mtls_disabled() -> None:
    # Keep in sync with ../sitecustomize.py. The startup hook should run first
    # in Agent Runtime; this is a defensive fallback for local/import paths.
    if os.getenv("GOOGLE_API_USE_CLIENT_CERTIFICATE", "").lower() != "false":
        return

    try:
        import urllib3.contrib.pyopenssl

        urllib3.contrib.pyopenssl.extract_from_urllib3()

        def _noop_inject_into_urllib3() -> None:
            urllib3.contrib.pyopenssl.extract_from_urllib3()

        urllib3.contrib.pyopenssl.inject_into_urllib3 = _noop_inject_into_urllib3
    except Exception:
        pass


_disable_urllib3_pyopenssl_when_mtls_disabled()

import google.auth  # noqa: E402

from . import agent  # noqa: E402,F401

try:
    _, project_id = google.auth.default()
    if project_id:
        os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
except Exception:
    pass

os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
