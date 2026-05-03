from pydantic import BaseModel


class SendEmailResponse(BaseModel):
    status: str
    delivery_mode: str


class EmailPreviewOut(BaseModel):
    subject: str
    html: str
    delivery_mode: str
