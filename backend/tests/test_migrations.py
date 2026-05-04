from app.cli.main import detect_legacy_schema_revision


def test_detect_legacy_schema_revision_for_pre_alembic_schema() -> None:
    revision = detect_legacy_schema_revision(
        {"users", "user_preferences"},
        {"user_id", "novel_meal_ratio", "takeout_frequency_per_week"},
    )

    assert revision == "20260503_0001"


def test_detect_legacy_schema_revision_for_already_upgraded_schema() -> None:
    revision = detect_legacy_schema_revision(
        {"users", "user_preferences"},
        {"user_id", "novel_meal_ratio", "takeout_frequency_per_week", "leftovers_per_week"},
    )

    assert revision == "20260503_0002"


def test_detect_legacy_schema_revision_skips_alembic_managed_schema() -> None:
    revision = detect_legacy_schema_revision(
        {"alembic_version", "users", "user_preferences"},
        {"user_id", "novel_meal_ratio", "takeout_frequency_per_week"},
    )

    assert revision is None