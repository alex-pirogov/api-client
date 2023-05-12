import asyncio
import logging
import os
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel

from .request import ApiMethod, ApiRequest
from .tg_alerting_api import TelegramAlertingApi

load_dotenv('.env')

logger = logging.getLogger('test_api')
logging.basicConfig(level=logging.INFO)
logging.getLogger('asyncio').setLevel(logging.ERROR)

TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')
assert TOKEN
assert ADMIN_ID


class Product(BaseModel):
    id: int
    title: str
    description: str
    price: int
    discountPercentage: float
    rating: float
    stock: int
    brand: str
    category: str
    thumbnail: str
    images: List[str]


class TestApi(TelegramAlertingApi):
    name = "Test Api"
    base_url = 'https://dummyjson.com'
    logger = logger

    def get_products(self):
        a = ApiRequest(api, ApiMethod.GET, url='/products/1', ReturnType=Product, payload={'hello': 'world'})
        return a

api = TestApi(token=TOKEN, alert_chat_id=int(ADMIN_ID))

async def main():
    await api.get_products()
    api.get_products().execute()

async def start():
    await asyncio.gather(main())

asyncio.run(start())
