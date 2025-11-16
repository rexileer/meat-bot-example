from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from Web.CRM.dataclasses import RolesModel
from Web.CRM.models import MeatBlank, Status
from bot.keyboards.technologist.technologist_check_keyboard import set_technologist_check_keyboard
from bot.loader import dp, bot
from bot.utils.text_info import get_meat_blank_text_before_storekeepr


@dp.callback_query_handler(Text(startswith="e_defrost"))
async def e_defrost(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    id_blank = int(call.data.split("-")[1])
    meat_blank: MeatBlank = await MeatBlank.objects.filter(pk=id_blank).afirst()
    date = await meat_blank.statuses.acreate(status=Status.objects.get(codename="loaded_to_defroster"))
    await call.message.answer(
        text=(await get_meat_blank_text_before_storekeepr(id_blank))
        + f"\nЗагружен в дефростер в {date.created_at:%d-%m-%Y %H:%M}",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton(text="Выключить дефростер", callback_data=f"d_defrost-{id_blank}")
        ),
    )


@dp.callback_query_handler(Text(startswith="e_again_defrost"))
async def e_defrost_2(call: types.CallbackQuery, state: FSMContext, roles: RolesModel):
    await call.message.delete()
    id_blank = int(call.data.split("-")[1])
    meat_blank: MeatBlank = await MeatBlank.objects.filter(pk=id_blank).afirst()
    msg = "Повторное включение дефростера!\nПодтвердите действие"
    await bot.send_message(
        roles.technologist.telegram_id,
        msg,
        reply_markup=set_technologist_check_keyboard(
            roles.defrost_manager.telegram_id, "defrost_again", meat_blank.pk
        ),
    )


@dp.callback_query_handler(Text(startswith="d_defrost"))
async def d_defrost(call: types.CallbackQuery, state: FSMContext, roles: RolesModel):
    await call.message.delete()
    id_blank = int(call.data.split("-")[1])

    meat_blank: MeatBlank = await MeatBlank.objects.filter(pk=id_blank).afirst()
    await meat_blank.statuses.acreate(status=Status.objects.get(codename="unloaded_from_defroster"))
    reply_markup = InlineKeyboardMarkup().add(
        *[
            InlineKeyboardButton(text="Завершить работу", callback_data="defrost_delete"),
            InlineKeyboardButton(text="Включить дефростер (повторно)", callback_data=f"e_again_defrost-{id_blank}"),
        ],
    )
    await bot.send_message(
        roles.defrost_manager.telegram_id,
        text=await get_meat_blank_text_before_storekeepr(id_blank),
        reply_markup=reply_markup,
    )


@dp.callback_query_handler(Text(startswith="defrost_delete"))
async def d_defrost_2(call: types.CallbackQuery, state: FSMContext, roles: RolesModel):
    await call.message.delete()
