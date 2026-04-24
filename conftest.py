from __future__ import annotations

import os
DEFAULT_TEST_DATABASE_URL = "sqlite://"
CI_TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if os.getenv("GITHUB_ACTIONS") == "true" and CI_TEST_DATABASE_URL:
    os.environ["DATABASE_URL"] = CI_TEST_DATABASE_URL
else:
    os.environ["DATABASE_URL"] = DEFAULT_TEST_DATABASE_URL

os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
