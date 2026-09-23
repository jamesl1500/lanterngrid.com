import time

from app.core.ids import uuid7


def test_uuid7_is_version_7_and_sorts_by_time() -> None:
    first = uuid7()
    time.sleep(0.002)
    second = uuid7()
    assert first.version == 7
    assert first.variant == "specified in RFC 4122"
    assert first < second
