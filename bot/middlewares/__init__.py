from aiogram import Dispatcher


from .album import AlbumMiddleware
from .db import UsersMiddleware


def setup(dp: Dispatcher):
    dp.setup_middleware(UsersMiddleware())
    dp.setup_middleware(AlbumMiddleware())
