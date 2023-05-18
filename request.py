import asyncio
import json
import logging
from abc import ABC
from enum import Enum
from typing import (TYPE_CHECKING, Any, Callable, Generator, Generic, List,
                    Optional, Type, TypeAlias, TypeVar, Union)
from urllib.parse import urlencode

from aiohttp import ClientResponse
from pydantic import BaseModel
from requests import Response

if TYPE_CHECKING:
    from .base_client import BaseApiClient


JSON: TypeAlias = Union[dict[str, 'JSON'], list['JSON'], str, int, float, bool, None]
_ReturnType = TypeVar('_ReturnType', bound=BaseModel)


class ApiMethod(str, Enum):
    GET = 'get'
    POST = 'post'
    PUT = 'put'
    PATCH = 'patch'
    DELETE = 'delete'

    
class BaseApiRequest(ABC, Generic[_ReturnType]):
    def __init__(
            self,
            api: 'BaseApiClient',
            method: ApiMethod,
            url: str,
            ReturnType: Type[_ReturnType],
            payload: Optional[JSON] = None,
            allowed_error_codes: Optional[List[int]] = None,
            **query_args: str
    ) -> None:
        self.api = api
        self.method = method
        self.url = self._build_url(url)
        self.payload = payload
        self.ReturnType = ReturnType
        self.allowed_error_codes = allowed_error_codes
        self.query_args = query_args

    def _build_url(self, method: str, **query_args: Any) -> str:
        query_args = {key: value for key, value in query_args.items() if value is not None}
        url = self.api.base_url + method
        if query_args:
            url += '?' + urlencode(query_args, safe='+')

        return url

    def _log_request(self, status: int, content: str, level: int = logging.DEBUG) -> None:
        if self.api.logger:
            text = f"[{self.method}] -> {status}\nURL: {self.url}\n"
            if self.payload:
                text += f"PAYLOAD:\n{json.dumps(self.payload, ensure_ascii=False, indent=2)}\n"
            
            text += f"RESP:\n{content if content else '*no content*'}"
            self.api.logger.log(level, text)


class AsyncApiRequest(BaseApiRequest[_ReturnType]):
    async def __check_response(self, response: ClientResponse):
        status, text = response.status, await response.text()
        
        if status < 400:
            return
        
        if self.allowed_error_codes and status not in self.allowed_error_codes:
            self._log_request(status, text, logging.ERROR)
            asyncio.ensure_future(self.api.call_async_error_hook(self, status, text))

        self.api.raise_exception(self, status, text)

    async def __return_resp(self, response: ClientResponse) -> _ReturnType:
        return self.ReturnType.parse_obj(await response.json())

    async def _async_make_request(self) -> _ReturnType:
        async with self.api.asession as session:
            request_method: Callable[..., ClientResponse] = getattr(session, self.method)
            async with request_method(self.url, json=self.payload) as response:
                self._log_request(response.status, await response.text())
                await self.__check_response(response)

                return await self.__return_resp(response)
            
    def __await__(self) -> Generator[Any, None, _ReturnType]:
        return self._async_make_request().__await__()


class SyncApiRequest(BaseApiRequest[_ReturnType]):
    def __check_response(self, response: Response):
        status, text = response.status_code, response.text
        
        if status < 400:
            return
        
        if self.allowed_error_codes and status not in self.allowed_error_codes:
            self._log_request(status, text, logging.ERROR)
            self.api.call_error_hook(self, status, text)
            
        self.api.raise_exception(self, status, text)

    def __return_resp(self, response: Response) -> _ReturnType:
        return self.ReturnType.parse_obj(response.json())
    
    def _make_request(self):
        request_method = getattr(self.api.session, self.method)
        response: Response = request_method(self.url, json=self.payload)
        
        self._log_request(response.status_code, response.text)
        self.__check_response(response)

        return self.__return_resp(response)

    def execute(self) -> _ReturnType:
        return self._make_request()


class ApiRequest(SyncApiRequest[_ReturnType], AsyncApiRequest[_ReturnType]):
    pass
