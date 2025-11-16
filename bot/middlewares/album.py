import asyncio

from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message


class AlbumMiddleware(BaseMiddleware):
    """Мидлтварь для работы с несколькими файлами, но
    в основном его юзаю только для работы с фото"""

    album_data: dict = {}

    def __init__(self, latency: int | float = 0.1):
        self.latency = latency
        super().__init__()

    async def on_pre_process_message(self, message: Message, data: dict):
        if message.document:
            await message.answer("Отправьте фотографии(ю) со сжатием, такой формат не поддерживается!")
            raise CancelHandler()
        if message.media_group_id:
            await self.multiply_files(message, data)
            return

    async def multiply_files(self, message: Message, data: dict):
        try:
            self.album_data[message.media_group_id].append(message)
            raise CancelHandler()
        except KeyError:
            self.album_data[message.media_group_id] = [message]
            await asyncio.sleep(self.latency)

            message.conf["is_last"] = True
            data["album"] = self.album_data[message.media_group_id]

    async def on_post_process_message(self, message: Message, result: dict, data: dict):
        if message.media_group_id and message.conf.get("is_last"):
            del self.album_data[message.media_group_id]
