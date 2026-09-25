import time

from app.core.ids import uuid7


def test_uuid7_is_version_7_and_sorts_by_time() -> None:
    first = uuid7()
    time.sleep(0.002)
    second = uuid7()
    assert first.version == 7
    assert first.variant == "specified in RFC 4122"
    assert first < second


def test_uuid7_increases_within_a_millisecond() -> None:
    ids = [uuid7() for _ in range(1000)]
    assert ids == sorted(ids)
    assert len(set(ids)) == len(ids)
    assert all(i.version == 7 for i in ids)
