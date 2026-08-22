from datetime import UTC, datetime, time
from types import SimpleNamespace

from app.services.scheduler import email_window_is_open, local_now


def preferences(day_of_week: int = 6, local_time: time = time(hour=9)) -> SimpleNamespace:
    return SimpleNamespace(
        email_enabled=True,
        email_day_of_week=day_of_week,
        email_local_time=local_time,
    )


def test_email_window_stays_closed_on_other_weekdays() -> None:
    # 2026-05-16 is a Saturday; the preference asks for Sunday.
    saturday_evening = local_now("UTC", datetime(2026, 5, 16, 23, 0, tzinfo=UTC))

    assert email_window_is_open(preferences(day_of_week=6), saturday_evening) is False


def test_email_window_opens_only_after_the_local_send_time() -> None:
    # 2026-05-17 is a Sunday. New York is UTC-4 in May, so 12:00Z is 08:00 local.
    before = local_now("America/New_York", datetime(2026, 5, 17, 12, 0, tzinfo=UTC))
    after = local_now("America/New_York", datetime(2026, 5, 17, 14, 0, tzinfo=UTC))

    assert before.hour == 8
    assert after.hour == 10
    assert email_window_is_open(preferences(), before) is False
    assert email_window_is_open(preferences(), after) is True


def test_local_now_falls_back_to_utc_for_an_unusable_zone() -> None:
    moment = datetime(2026, 5, 17, 14, 0, tzinfo=UTC)

    assert local_now("Not/AZone", moment).hour == 14
    assert local_now("../../etc/passwd", moment).hour == 14
