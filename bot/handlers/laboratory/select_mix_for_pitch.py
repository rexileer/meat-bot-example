from datetime import timedelta

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from django.utils import timezone

from bot.loader import dp
from bot.utils.text_info import generate_recipe_for_minced_meat_mix_bobo
from Web.CRM.models import MincedMeatBatchStatus


@dp.callback_query_handler(Text(equals="laboratory_pitch"))
async def select_laboratory_pitch(call: CallbackQuery, state: FSMContext):
    mixes_list = MincedMeatBatchStatus.objects.filter(
        status__codename="laboratory_analyze_finish", minced_meat_batch_mix__minced_meat_batch__type="МКО"
    ).all()
    mixes_list = [
        mix
        for mix in mixes_list
        if mix.created_at + timedelta(minutes=1) < timezone.now() and not mix.additional_data.get("pitch", None)
    ]

    if not mixes_list:
        await call.message.edit_text(
            "В данный момент нету замесов для анализа",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(text="Назад", callback_data="return")),
        )
    else:
        await state.update_data(pos=0, mix_id=mixes_list[0].minced_meat_batch_mix.pk)
        await call.message.edit_text(await get_text_for_fhp_mix(mixes_list[0]), reply_markup=kb_for_listing_lab())


@dp.callback_query_handler(Text(equals="lab_pitch_next"))
async def lab_next(call: CallbackQuery, state: FSMContext):
    mixes_list = MincedMeatBatchStatus.objects.filter(
        status__codename="laboratory_analyze_finish", minced_meat_batch_mix__minced_meat_batch__type="МКО"
    ).all()
    mixes_list = [
        mix
        for mix in mixes_list
        if mix.created_at + timedelta(minutes=1) < timezone.now() and not mix.additional_data.get("pitch", None)
    ]

    if not mixes_list:
        await select_laboratory_pitch(call, state)
    else:
        state_data = await state.get_data()
        new_index = 0 if state_data.get("pos", 0) + 1 > len(mixes_list) - 1 else state_data.get("pos", 0) + 1
        await state.update_data(pos=new_index, mix_id=mixes_list[new_index].minced_meat_batch_mix.pk)
        await call.message.edit_text(
            await get_text_for_fhp_mix(mixes_list[new_index]), reply_markup=kb_for_listing_lab()
        )


@dp.callback_query_handler(Text(equals="lab_pitch_previous"))
async def lab_previous(call: CallbackQuery, state: FSMContext):
    mixes_list = MincedMeatBatchStatus.objects.filter(
        status__codename="laboratory_analyze_finish", minced_meat_batch_mix__minced_meat_batch__type="МКО"
    ).all()
    mixes_list = [
        mix
        for mix in mixes_list
        if mix.created_at + timedelta(minutes=1) < timezone.now() and not mix.additional_data.get("pitch", None)
    ]

    if not mixes_list:
        await select_laboratory_pitch(call, state)
    else:
        state_data = await state.get_data()
        new_index = len(mixes_list) - 1 if state_data.get("pos", 0) - 1 < 0 else state_data.get("pos", 0) - 1
        await state.update_data(pos=new_index, mix_id=mixes_list[new_index].minced_meat_batch_mix.pk)
        await call.message.edit_text(
            await get_text_for_fhp_mix(mixes_list[new_index]), reply_markup=kb_for_listing_lab()
        )


async def get_text_for_fhp_mix(mix: MincedMeatBatchStatus):
    text_materials = await generate_recipe_for_minced_meat_mix_bobo(mix.minced_meat_batch_mix.minced_meat_batch.pk)
    text = f"""Анализа на залу
<b>{mix.minced_meat_batch_mix.minced_meat_batch.recipe.name} замес -
{mix.minced_meat_batch_mix.production_id.split("/")[::-1][0]}</b>


ID фарша: {mix.minced_meat_batch_mix.minced_meat_batch.production_id}
Рецепт: {mix.minced_meat_batch_mix.minced_meat_batch.recipe.name}

Используемое сырье и заготовки:
{text_materials}
Созданные замесы:
{mix.minced_meat_batch_mix.production_id}"""
    return text


def kb_for_listing_lab():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton(text="Начать анализ", callback_data="analyze_pitch_mix"))
    keyboard.add(
        *[
            InlineKeyboardButton(text="<", callback_data="lab_pitch_previous"),
            InlineKeyboardButton(text=">", callback_data="lab_pitch_next"),
        ]
    )
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="return"))
    return keyboard
