import logging

from aiogram import Dispatcher

from data.config import env


async def on_startup_notify(dp: Dispatcher):
    try:
        await dp.bot.send_message(env.DEVELOPER, "Бот Запущен и готов с кнопками\n/start")
    except Exception as err:
        logging.exception(err)
