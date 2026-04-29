from html import escape

from application.ports.email import EmailBodyBuilder


class SimpleEmailBodyBuilder(EmailBodyBuilder):
    async def confirm_email(self, code: int) -> str:
        """Формирует HTML-тело письма с кодом подтверждения регистрации."""
        return self._build_html(
            title="Подтверждение регистрации",
            subtitle="Используйте код ниже для завершения регистрации.",
            code=code,
        )

    async def auth_code(self, code: int) -> str:
        """Формирует HTML-тело письма с кодом входа."""
        return self._build_html(
            title="Код для входа",
            subtitle="Используйте код ниже для входа в аккаунт.",
            code=code,
        )

    async def confirm_new_email(self, code: int) -> str:
        """Формирует HTML-тело письма с кодом подтверждения нового email."""
        return self._build_html(
            title="Подтверждение смены email",
            subtitle="Используйте код ниже для подтверждения нового email.",
            code=code,
        )

    def _build_html(self, title: str, subtitle: str, code: int) -> str:
        safe_title = escape(title)
        safe_subtitle = escape(subtitle)
        safe_code = escape(str(code))
        return (
            '<div style="margin:0;padding:24px;background:#f3f5f7;font-family:Verdana,Tahoma,sans-serif;">'
            '<div style="max-width:520px;margin:0 auto;background:#ffffff;border:1px solid #e4e7eb;border-radius:14px;padding:24px;">'
            f'<h1 style="margin:0 0 10px;font-size:22px;line-height:1.25;color:#111827;">{safe_title}</h1>'
            f'<p style="margin:0 0 18px;font-size:14px;line-height:1.45;color:#4b5563;">{safe_subtitle}</p>'
            '<div style="margin:0 0 16px;padding:14px;border:1px dashed #9ca3af;border-radius:10px;'
            'background:#f9fafb;text-align:center;">'
            f'<span style="font-size:34px;line-height:1;letter-spacing:6px;font-weight:700;color:#111827;">{safe_code}</span>'
            "</div>"
            '<p style="margin:0;font-size:12px;line-height:1.4;color:#6b7280;">'
            "Скопируйте код и вставьте его в форму подтверждения. "
            "Если вы не запрашивали это действие, проигнорируйте письмо."
            "</p>"
            "</div>"
            "</div>"
        )
