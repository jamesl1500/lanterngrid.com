from pydantic import BaseModel


class RealtimeTicket(BaseModel):
    """Open `url` with `?ticket=` within a minute. A ticket works once."""

    ticket: str
    url: str
