import logging
from abc import ABC
from typing import Any, Dict, Optional, Type

from aiohttp import ClientSession
from requests import Session

from .request import BaseApiRequest


class BaseApiClientError(Exception):
    def __init__(self, request: BaseApiRequest[Any], status: int, text: str) -> None:
        self.request = request
        self.status = status
        self.text = text
        super().__init__()
    
    def __str__(self) -> str:
        return f"[{self.status}] {self.text if self.text else '*no content*'}"


class BaseApiClient(ABC):
    name: str = "Base Api"
    base_url: str
    logger: Optional[logging.Logger] = None
    debug: bool = False
    ExceptionClass: Type[BaseApiClientError] = BaseApiClientError

    def __init__(self) -> None:
        assert self.base_url
        if self.debug and self.logger is None:
            raise ValueError(f"Logger required")

    def get_headers(self) -> Dict[str, str]:
        return {}
    
    def raise_exception(self, request: BaseApiRequest[Any], status: int, text: str):
        raise self.ExceptionClass(request, status, text)
    
    def call_error_hook(self, request: BaseApiRequest[Any], status: int, text: str) -> None:
        self.error_hook(request, status, text)

    def error_hook(self, request: BaseApiRequest[Any], status: int, text: str) -> None:
        pass
    
    async def call_async_error_hook(self, request: BaseApiRequest[Any], status: int, text: str) -> None:
        await self.async_error_hook(request, status, text)

    async def async_error_hook(self, request: BaseApiRequest[Any], status: int, text: str) -> None:
        pass

    @property
    def asession(self):
        return ClientSession(headers=self.get_headers())

    @property
    def session(self) -> Session:
        session = Session()
        session.headers.update(self.get_headers())
        return session
    