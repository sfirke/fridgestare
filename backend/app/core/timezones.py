from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

UTC_ZONE = ZoneInfo("UTC")


def is_valid_timezone(name: str) -> bool:
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        # ZoneInfo raises ValueError, not ZoneInfoNotFoundError, for keys that escape
        # TZPATH (for example "../../etc/passwd"); both mean "not a usable zone".
        return False
    return True


def resolve_timezone(name: str) -> ZoneInfo:
    """Look up an IANA zone, falling back to UTC rather than raising.

    Read paths (planning, scheduling) must not break on a stored zone that has since
    been removed from the system's tz database; write paths validate up front instead.
    """
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        return UTC_ZONE
