from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from Web.CRM.models import MincedMeatBatchMix
from bot.loader import dp
from bot.utils.text_info import (
    generate_recipe_for_minced_meat_mix_bobo,
)


@dp.callback_query_handler(Text(equals="laboratory_mixes"))
async def select_laboratory_raw_batch(call: CallbackQuery, state: FSMContext):
    mixes_list = MincedMeatBatchMix.objects.filter(statuses__status__codename__in=["mixer_mix_meat"]).all()
    mixes_list = [
        mix for mix in mixes_list if mix.statuses.filter(status__codename="laboratory_analyze_finish").first() is None
    ]

    if not mixes_list:
        await call.message.edit_text(
            "В данный момент нету замесов для анализа",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(text="Назад", callback_data="return")),
        )
    else:
        await state.update_data(pos=0, mix_id=mixes_list[0].pk)
        await call.message.edit_text(
            await get_text_for_fhp_mix(mixes_list[0]), reply_markup=kb_for_listing_lab(mixes_list[0])
        )


@dp.callback_query_handler(Text(equals="lab_mixes_next"))
async def lab_next(call: CallbackQuery, state: FSMContext):
    mixes_list = MincedMeatBatchMix.objects.filter(statuses__status__codename__in=["mixer_mix_meat"]).all()
    mixes_list = [
        mix for mix in mixes_list if mix.statuses.filter(status__codename="laboratory_analyze_finish").first() is None
    ]
    if not mixes_list:
        await select_laboratory_raw_batch(call, state)
    else:
        state_data = await state.get_data()
        new_index = 0 if state_data.get("pos", 0) + 1 > len(mixes_list) - 1 else state_data.get("pos", 0) + 1
        await state.update_data(pos=new_index, mix_id=mixes_list[new_index].pk)
        await call.message.edit_text(
            await get_text_for_fhp_mix(mixes_list[new_index]), reply_markup=kb_for_listing_lab(mixes_list[new_index])
        )


@dp.callback_query_handler(Text(equals="lab_mixes_previous"))
async def lab_previous(call: CallbackQuery, state: FSMContext):
    mixes_list = MincedMeatBatchMix.objects.filter(statuses__status__codename__in=["mixer_mix_meat"]).all()
    mixes_list = [
        mix for mix in mixes_list if mix.statuses.filter(status__codename="laboratory_analyze_finish").first() is None
    ]
    if not mixes_list:
        await select_laboratory_raw_batch(call, state)
    else:
        state_data = await state.get_data()
        new_index = len(mixes_list) - 1 if state_data.get("pos", 0) - 1 < 0 else state_data.get("pos", 0) - 1
        await state.update_data(pos=new_index, mix_id=mixes_list[new_index].pk)
        await call.message.edit_text(
            await get_text_for_fhp_mix(mixes_list[new_index]), reply_markup=kb_for_listing_lab(mixes_list[new_index])
        )


async def get_text_for_fhp_mix(mix: MincedMeatBatchMix):
    text_materials = await generate_recipe_for_minced_meat_mix_bobo(mix.minced_meat_batch.pk)
    text = f"""ФХП Анализ

<b>Линия - {mix.minced_meat_batch.line_type if mix.minced_meat_batch.line_type in [1,2]
            else f"Обе {mix.line_type}"}</b>

<b>{mix.minced_meat_batch.recipe.name} замес - {mix.production_id.split("/")[::-1][0]}</b>

ID фарша: {mix.minced_meat_batch.production_id}
Рецепт: {mix.minced_meat_batch.recipe.name}

Используемое сырье и заготовки:
{text_materials}"""
    return text


def kb_for_listing_lab(mix):
    keyboard = InlineKeyboardMarkup(row_width=2)
    if not (
        mix.statuses.filter(status__codename="laboratory_analyze_technolog_acception").first()
        and not mix.statuses.filter(status__codename="laboratory_analyze_again")
        or mix.statuses.filter(status__codename="mix_is_blocked_analyze")
    ):
        keyboard.add(InlineKeyboardButton(text="Начать анализ", callback_data="analyze_mix"))

    keyboard.add(
        *[
            InlineKeyboardButton(text="<", callback_data="lab_mixes_previous"),
            InlineKeyboardButton(text=">", callback_data="lab_mixes_next"),
        ]
    )
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="return"))
    return keyboard
