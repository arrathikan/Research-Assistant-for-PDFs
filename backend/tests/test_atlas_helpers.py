"""Keep live test namespaces within the Atlas shared-tier 38-byte limit."""

import re

from backend.tests.atlas_helpers import new_atlas_database_name


def test_disposable_atlas_database_name_is_short_and_clearly_scoped():
    name = new_atlas_database_name()
    assert len(name.encode("utf-8")) <= 38
    assert re.fullmatch(r"researchai_test_[0-9a-f]+", name)
    assert name != "research_assistant"
