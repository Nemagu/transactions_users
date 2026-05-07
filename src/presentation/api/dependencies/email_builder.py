from fastapi import Request

from infrastructure.email import SimpleEmailMessageBuilder


async def email_builder(request: Request) -> SimpleEmailMessageBuilder:
    return request.app.state.email_builder
