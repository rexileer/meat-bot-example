from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, Message

from bot.keyboards.main_menu import main_menu_keyboard
from bot.loader import dp
from bot.utils.locale_manager import LocaleManager
from Web.CRM.dataclasses import RolesModel


@dp.message_handler(text="Вернуться", state="*")
@dp.message_handler(text="Назад", state="*")
@dp.message_handler(commands=["start"], state="*")
async def start(message: Message, state: FSMContext, _: LocaleManager(), roles: RolesModel):
    await state.reset_state()
    # if message.from_user.id == 551763936:
    #     await message.answer_document(
    #         caption='Информация по вторфаршу за сегодня',
    #         document=InputFile(filename="Вторфарш.xlsx", path_or_bytesio=await generate_second_minced_meat_info())
    #     )
    # if message.from_user.id ==551763936:
    #     from bot.handlers.mixer.mixer import mixer_notify_good_fhp_mix_meat
    #     await mixer_notify_good_fhp_mix_meat(231,roles)
    #     await mixer_notify_good_fhp_mix_meat(232,roles)
    await message.answer(text="Главное меню", reply_markup=main_menu_keyboard(message.from_user.id))


@dp.callback_query_handler(Text(equals="return"), state="*")
async def main_menu_callback(call: CallbackQuery, state: FSMContext):
    await state.reset_state()
    await call.message.delete()

    await call.message.answer(text="Главное меню", reply_markup=main_menu_keyboard(call.from_user.id))
