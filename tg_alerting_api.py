import json
from typing import Any

from aiogram import Bot
from aiogram.enums import ParseMode
from telebot import TeleBot

from .base_client import BaseApiClient
from .request import BaseApiRequest


class TelegramAlertingApi(BaseApiClient):
    def __init__(
            self,
            token: str,
            alert_chat_id: int,
            send_to_tg: bool = True
    ) -> None:
        super().__init__()
        self.bot = TeleBot(token, parse_mode=ParseMode.HTML)
        self.async_bot = Bot(token, parse_mode=ParseMode.HTML)
        self.alert_chat_id = alert_chat_id
        self.send_to_tg = send_to_tg

    def _get_alert_text(self, request: BaseApiRequest[Any], status: int, content: str) -> str:
        text = f"[{request.method}] -> RESP {status}\nURL: {request.url}\n"
        if request.payload:
            text += f"PAYLOAD:\n<code>{json.dumps(request.payload, ensure_ascii=False, indent=2)}</code>\n"
        
        text += f"RESP:\n<code>{content if content else '*no content*'}</code>"
        return text
    
    def call_error_hook(self, request: BaseApiRequest[Any], status: int, text: str) -> None:
        if self.send_to_tg:
            self.bot.send_message(
                chat_id=self.alert_chat_id,
                text=self._get_alert_text(request, status, text)
            )

        return super().call_error_hook(request, status, text)

    async def call_async_error_hook(self, request: BaseApiRequest[Any], status: int, text: str):
        if self.send_to_tg:
            await self.async_bot.send_message(
                chat_id=self.alert_chat_id,
                text=self._get_alert_text(request, status, text)
            )

        return await super().call_async_error_hook(request, status, text)
    