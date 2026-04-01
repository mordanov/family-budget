import pytest

from scripts.migration_bootstrap import decide_migration_action


def test_decide_action_upgrade_for_empty_schema():
    assert decide_migration_action([]) == "upgrade"


def test_decide_action_upgrade_when_alembic_version_exists():
    assert decide_migration_action(["alembic_version", "users"]) == "upgrade"


def test_decide_action_stamp_for_legacy_complete_schema():
    tables = [
        "users",
        "categories",
        "operations",
        "attachments",
        "monthly_balances",
    ]
    assert decide_migration_action(tables) == "stamp"


def test_decide_action_fails_for_partial_legacy_schema():
    with pytest.raises(RuntimeError):
        decide_migration_action(["users", "categories"])

