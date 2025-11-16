from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from bot.keyboards.storekeeper.storekeeper_keyboards import storekeeper_mars_actions
from bot.loader import dp


# start_action
@dp.callback_query_handler(Text(equals="mars_shock"))
async def add_second_minced_meat(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Что вы собираетесь сделать?", reply_markup=storekeeper_mars_actions())
