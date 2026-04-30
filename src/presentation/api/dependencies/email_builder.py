from fastapi import Request

from infrastructure.email import SimpleEmailBodyBuilder


async def email_builder(request: Request) -> SimpleEmailBodyBuilder:
    return request.app.state.email_builder
