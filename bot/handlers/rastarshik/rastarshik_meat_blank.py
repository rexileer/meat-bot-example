from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from Web.CRM.dataclasses import RolesModel
from Web.CRM.models import MeatBlank, Status
from bot.loader import bot, dp


@dp.callback_query_handler(Text(startswith="accpet_rastareno"))
async def accpet_rastareno(call: types.CallbackQuery, state: FSMContext, roles: RolesModel):
    await call.message.delete()
    meat_blank_id = int(call.data.split("-")[1])
    meat_blank: MeatBlank = await MeatBlank.objects.aget(pk=meat_blank_id)
    await meat_blank.statuses.acreate(
        status=Status.objects.get(codename="rastarshik_unload_meat_blank_end"),
        additional_data=(await state.get_data()),
    )
    await state.finish()

    reply_markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton(text="Включить дефростер", callback_data=f"e_defrost-{meat_blank_id}")
    )
    from bot.utils.text_info import get_meat_blank_text_before_storekeepr

    await bot.send_message(
        roles.defrost_manager.telegram_id,
        text=await get_meat_blank_text_before_storekeepr(meat_blank_id),
        reply_markup=reply_markup,
    )


@dp.callback_query_handler(Text(startswith="declime_rastareno"))
async def declime_rastareno(call: types.CallbackQuery, state: FSMContext, roles: RolesModel):
    await bot.send_message(roles.technologist.telegram_id, "Ошибка на этапе расстарки! Требует вашего внимания!")
