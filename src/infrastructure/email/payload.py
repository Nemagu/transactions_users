from pydantic import BaseModel


class EmailSendPayload(BaseModel):
    recipients: list[str]
    body: str
