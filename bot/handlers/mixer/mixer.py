from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from Web.CRM.dataclasses import RolesModel
from Web.CRM.models import MincedMeatBatchMix, Status, Tilers
from bot.keyboards.mixer.mixer_kb import (
    mixer_keyboard,
    farshovitel_minced_meat_from_analysis_keyboard,
    packer_select_tiler_keyboard,
)
from bot.keyboards.technologist.technologist_check_keyboard import accept_work_line_status
from bot.loader import bot, dp
from bot.utils.text_info import generate_recipe_for_minced_meat_mix_bobo


async def mixer_notify_mix_meat(mix_id, roles: RolesModel):
    mix = MincedMeatBatchMix.objects.get(pk=mix_id)

    text = f"""<b>Линия - {mix.minced_meat_batch.line_type if mix.minced_meat_batch.line_type in [1, 2]
                            else f"Обе {mix.line_type}"}</b>

Был создан новый замес - <b>{mix.minced_meat_batch.recipe.name} замес - {mix.production_id.split("/")[::-1][0]}</b>


ID фарша: {mix.minced_meat_batch.production_id}
Рецепт: {mix.minced_meat_batch.recipe.name}

Используемое сырье и заготовки:
{await generate_recipe_for_minced_meat_mix_bobo(mix.minced_meat_batch.pk)}

"""
    if mix.minced_meat_batch.line_type in [1, 10]:
        await bot.send_message(
            chat_id=roles.Farshesostovitel.telegram_id, text=text, reply_markup=mixer_keyboard(mix_id)
        )
    elif mix.minced_meat_batch.line_type in [2] and mix.minced_meat_batch.type == "ММО":
        await bot.send_message(
            chat_id=roles.Farshesostovitel_line_2.telegram_id, text=text, reply_markup=mixer_keyboard(mix_id)
        )
    elif mix.minced_meat_batch.line_type in [2] and mix.minced_meat_batch.type == "МКО":
        await bot.send_message(
            chat_id=roles.mko_manager_line_2.telegram_id, text=text, reply_markup=mixer_keyboard(mix_id)
        )


async def mixer_notify_good_fhp_mix_meat(mix_id, roles: RolesModel, is_bad=False):
    mix = MincedMeatBatchMix.objects.get(pk=mix_id)

    text = f"""\t\t\t<b>Линия - {mix.minced_meat_batch.line_type if mix.minced_meat_batch.line_type in [1, 2]
                                  else f"Обе {mix.line_type}"}</b>

Замес {"<b>УСПЕШНО</b>" if not is_bad else "<b>НЕ</b>"} прошел ФХП анализ
<b>{mix.minced_meat_batch.recipe.name} замес - {mix.production_id.split("/")[::-1][0]}</b>

ID фарша: {mix.minced_meat_batch.production_id}
Рецепт: {mix.minced_meat_batch.recipe.name}

Используемое сырье и заготовки:
{await generate_recipe_for_minced_meat_mix_bobo(mix.minced_meat_batch.pk)}"""
    work_line = None
    if mix.minced_meat_batch.type == "МКО":
        work_line = mix.minced_meat_batch.line_type
    else:
        await mix.statuses.aget_or_create(status=Status.objects.get(codename="mixer_tiller_mix_meat"))

    if mix.minced_meat_batch.line_type in [1, 10]:
        await bot.send_message(
            chat_id=roles.Farshesostovitel.telegram_id,
            text=text,
            reply_markup=farshovitel_minced_meat_from_analysis_keyboard(mix_id, work_line),
        )

    elif mix.minced_meat_batch.line_type in [2] and mix.minced_meat_batch.type == "ММО":
        await bot.send_message(
            chat_id=roles.Farshesostovitel.telegram_id,
            text=text,
            reply_markup=farshovitel_minced_meat_from_analysis_keyboard(mix_id, work_line),
        )

    elif mix.line_type in [2] and mix.minced_meat_batch.type == "МКО":
        await bot.send_message(
            chat_id=roles.mko_manager_line_2.telegram_id,
            text=text,
            reply_markup=farshovitel_minced_meat_from_analysis_keyboard(mix_id, work_line),
        )


@dp.callback_query_handler(Text(startswith="farshunload_mix"))
async def farshov_mix_finish(call: types.CallbackQuery, state: FSMContext):
    if not Tilers.objects.filter(status=True):
        return await call.message.answer("В данный момент нету свободных плиточников!!!!")
    await call.message.delete()

    mix = MincedMeatBatchMix.objects.filter(pk=int(call.data.split("-")[1])).first()
    await call.message.answer(
        text=f"Выберите свободный номер плиточника для загрузки для замеса {mix.production_id}",
        reply_markup=packer_select_tiler_keyboard(mix.pk),
    )


@dp.callback_query_handler(Text(startswith="select_tiler"))
async def farshov_tiler(call: types.CallbackQuery, state: FSMContext, roles: RolesModel):
    tiler_id = int(call.data.split("-")[1])
    mix_id = int(call.data.split("-")[2])
    tiler = Tilers.objects.get(pk=tiler_id)
    if not tiler.status:
        call.data = f"farshunload_mix-{mix_id}"
        await farshov_mix_finish(call, state)
        return
    tiler.status = False
    tiler.minced_meat_batch_mix_id = mix_id
    tiler.save()
    mix = MincedMeatBatchMix.objects.filter(pk=mix_id).first()
    if (
        int(mix.production_id.split("/")[::-1][0]) == mix.minced_meat_batch.number_mix
        and mix.minced_meat_batch.line_type == 2
    ):
        await bot.send_message(
            roles.technologist.telegram_id,
            "Линия 2 закончила загрузку в плиточник последнего замеса, переключить ее на совместную работу?",
            reply_markup=accept_work_line_status(mix.pk),
        )

    await mix.statuses.acreate(
        status=Status.objects.get(codename="mixer_tiller_mix_meat_end"), additional_data={"tiller_id": tiler_id}
    )
    await mix.asave()
    await mix.statuses.acreate(status=Status.objects.get(codename="mixer_mix_meat_end"))
    await call.message.answer("Загрузка в плиточник успешна!")
    await call.message.delete()
    await state.finish()


@dp.callback_query_handler(Text(startswith="farshov_mix"))
async def accept_minced_meat_batch_mix(call: types.CallbackQuery, state: FSMContext, roles: RolesModel):
    await call.message.delete()
    mix_id = int(call.data.split("-")[1])
    mix = MincedMeatBatchMix.objects.get(pk=mix_id)

    text = f"""
    <b>Линия - {mix.minced_meat_batch.line_type if mix.minced_meat_batch.line_type in [1, 2]
                 else f"Обе {mix.line_type}"}</b>
Новый замес для ФХП анализа
<b>{mix.minced_meat_batch.recipe.name} замес - {mix.production_id.split("/")[::-1][0]}</b>

ID фарша: {mix.minced_meat_batch.production_id} {mix.minced_meat_batch.type}
Рецепт: {mix.minced_meat_batch.recipe.name}

Используемое сырье и заготовки:
{await generate_recipe_for_minced_meat_mix_bobo(mix.minced_meat_batch.pk)}
    """

    await bot.send_message(
        chat_id=roles.labaratory.telegram_id,
        text=text,
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton(text="Начать анализ", callback_data=f"analyze_mix-{mix_id}")
        ),
    )
