from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.loader import dp
from bot.utils.text_info import raw_meat_batch_for_lab
from Web.CRM.models import RawMeatBatch


@dp.callback_query_handler(Text(equals="main_menu_laboratory"))
async def select_laboratory_raw_batch(call: CallbackQuery, state: FSMContext):
    raw_meat_batch_list = RawMeatBatch.objects.filter(statuses=None, weight__gt=0)

    if not raw_meat_batch_list:
        await call.message.edit_text(
            "В данный момент нету партий для анализа",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(text="Назад", callback_data="return")),
        )
    else:
        await state.update_data(pos=0, batch_id=raw_meat_batch_list[0].pk)
        await call.message.edit_text(raw_meat_batch_for_lab(raw_meat_batch_list[0]), reply_markup=kb_for_listing_lab())


@dp.callback_query_handler(Text(equals="lab_next"))
async def lab_next(call: CallbackQuery, state: FSMContext):
    raw_meat_batch_list = RawMeatBatch.objects.filter(statuses=None, weight__gt=0)

    if not raw_meat_batch_list:
        await select_laboratory_raw_batch(call, state)
    else:
        state_data = await state.get_data()
        new_index = 0 if state_data.get("pos", 0) + 1 > len(raw_meat_batch_list) - 1 else state_data.get("pos", 0) + 1
        await state.update_data(pos=new_index, batch_id=raw_meat_batch_list[new_index].pk)
        await call.message.edit_text(
            raw_meat_batch_for_lab(raw_meat_batch_list[new_index]), reply_markup=kb_for_listing_lab()
        )


@dp.callback_query_handler(Text(equals="lab_previous"))
async def lab_previous(call: CallbackQuery, state: FSMContext):
    raw_meat_batch_list = RawMeatBatch.objects.filter(statuses=None, weight__gt=0)

    if not raw_meat_batch_list:
        await select_laboratory_raw_batch(call, state)
    else:
        state_data = await state.get_data()
        new_index = len(raw_meat_batch_list) - 1 if state_data.get("pos", 0) - 1 < 0 else state_data.get("pos", 0) - 1
        await state.update_data(pos=new_index, batch_id=raw_meat_batch_list[new_index].pk)
        await call.message.edit_text(
            raw_meat_batch_for_lab(raw_meat_batch_list[new_index]), reply_markup=kb_for_listing_lab()
        )


def kb_for_listing_lab():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton(text="Начать анализ", callback_data="analyze_raw_meat_batch"))
    keyboard.add(
        *[
            InlineKeyboardButton(text="<", callback_data="lab_previous"),
            InlineKeyboardButton(text=">", callback_data="lab_next"),
        ]
    )
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="return"))
    return keyboard
