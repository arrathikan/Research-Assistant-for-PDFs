"""Short, disposable database names compatible with Atlas shared-tier limits."""

from uuid import uuid4


def new_atlas_database_name() -> str:
    return "researchai_test_" + uuid4().hex[:16]
