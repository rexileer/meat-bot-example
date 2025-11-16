from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from bot.loader import dp

from bot.utils.locale_manager import LocaleManager


class UsersMiddleware(BaseMiddleware):
    @staticmethod
    async def on_pre_process_message(message: Message, data):
        if message.text in ["/start", "Назад", "Вернуться"]:
            CancelHandler()
            user_fsm = dp.current_state(chat=message.from_user.id, user=message.from_user.id)
            await user_fsm.reset_state(with_data=True)
        # from bot.handlers.start.start import start
        #   await start(message, user_fsm, LocaleManager())

        roles = await UsersMiddleware.get_tgid_positions()

        data["roles"] = roles

        data["_"] = LocaleManager()

    @staticmethod
    async def on_pre_process_callback_query(callback_query: CallbackQuery, data):
        roles = await UsersMiddleware.get_tgid_positions()

        data["roles"] = roles
        data["_"] = LocaleManager()

    @staticmethod
    async def on_pre_process_inline_query(callback_query: CallbackQuery, data):
        roles = await UsersMiddleware.get_tgid_positions()

        data["roles"] = roles
        data["_"] = LocaleManager()

    @staticmethod
    async def get_tgid_positions():
        from Web.CRM.models import Users

        return Users.list_roles
