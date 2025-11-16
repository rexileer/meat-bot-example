import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from minio import Minio

from data.config import env
from bot.utils.locale_manager import LocaleManager

locale_manager = LocaleManager()
base_dir_locales = env.APP_DIR / "locales"
i18_domain = "mybot"
i18n = I18nMiddleware(i18_domain, base_dir_locales)
locale_manager.set_middleware(i18n)


loop = asyncio.get_event_loop()
bot = Bot(token=env.TELEGRAM_BOT_TOKEN, parse_mode=types.ParseMode.HTML)


# storage = RedisStorage2(prefix="meat", host=env.REDIS_HOST, port=env.REDIS_PORT,
#                            db=env.REDIS_DB)
storage = MemoryStorage()

scheduler = AsyncIOScheduler()

minio = Minio(
    env.MINIO_ENDPOINT, access_key=env.MINIO_ACCESS_KEY, secret_key=env.MINIO_SECRET_KEY, secure=env.MINIO_USE_HTTPS
)
dp = Dispatcher(bot, storage=storage)
