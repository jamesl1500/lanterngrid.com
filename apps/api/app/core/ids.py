import os
import time
import uuid


def uuid7() -> uuid.UUID:
    """A time-ordered UUID (RFC 9562 version 7).

    Ids sort by creation time, so lists can page with `where id < :cursor order by id desc`.
    Python 3.14 ships `uuid.uuid7`; this stands in until the API moves to it.
    """
    unix_ms = time.time_ns() // 1_000_000
    rand = int.from_bytes(os.urandom(10))
    value = (unix_ms & 0xFFFF_FFFF_FFFF) << 80
    value |= 0x7 << 76  # version
    value |= ((rand >> 62) & 0xFFF) << 64  # rand_a
    value |= 0b10 << 62  # variant
    value |= rand & 0x3FFF_FFFF_FFFF_FFFF  # rand_b
    return uuid.UUID(int=value)
