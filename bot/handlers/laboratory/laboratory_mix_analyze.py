import re

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import Message

from bot.handlers.mixer.mixer import mixer_notify_good_fhp_mix_meat
from bot.handlers.technologist.utils.technologist_check import set_technologist_check_message_fhp
from bot.keyboards.technologist.technologist_check_keyboard import set_technologist_check_keyboard
from bot.loader import bot, dp
from bot.states.fhp_analysis import FHPAnalysis
from data.constants import FLOAT_REGEX
from Web.CRM.dataclasses import RolesModel
from Web.CRM.models import MincedMeatBatchMix, MincedStandards, Status


@dp.callback_query_handler(Text(startswith="analyze_mix"))
@dp.callback_query_handler(Text(startswith="analyze_mix-"))
async def accept_minced_meat_batch_mix(call: types.CallbackQuery, state: FSMContext):
    if "-" in call.data:
        await state.update_data(mix_id=int(call.data.split("-")[1]))
    await call.message.answer("Введите массовую долю жиров")
    await FHPAnalysis.set_fats.set()
    await call.message.delete()


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=FHPAnalysis.set_fats)
async def set_fat_proportion_handler(message: Message, state: FSMContext):
    await state.update_data(fat_proportion=message.text)
    await message.answer("Введите массовую долю белков")
    await FHPAnalysis.set_proteins.set()


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=FHPAnalysis.set_proteins)
async def set_protein_proportion_handler(message: Message, state: FSMContext):
    await state.update_data(protein_proportion=message.text)
    await message.answer("ведите массовую долю влаги")
    await FHPAnalysis.set_moisture.set()


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=FHPAnalysis.set_moisture)
async def finish_fhp_for_mix(message: Message, state: FSMContext, roles: RolesModel):
    await state.update_data(moisture_proportion=message.text)
    state_data = await state.get_data()

    mix = MincedMeatBatchMix.objects.get(pk=state_data.get("mix_id"))

    standart = MincedStandards.objects.get(recipe_id=mix.minced_meat_batch.recipe.pk)
    fats = standart.get_deviation_fats()
    moisture = standart.get_deviation_moisture()
    protein = standart.get_deviation_protein()
    bad_fhp = 0
    add_data = {}
    if (
        not (fats[0] <= float(state_data["fat_proportion"]) <= fats[1])
        or not (protein[0] <= float(state_data["protein_proportion"]) <= protein[1])
        or not (moisture[0] <= float(state_data["moisture_proportion"]) <= moisture[1])
    ):
        bad_fhp = 1
        msg = await set_technologist_check_message_fhp(mix.pk)
        await bot.send_message(
            roles.technologist.telegram_id,
            msg,
            reply_markup=set_technologist_check_keyboard(roles.labaratory.telegram_id, "fhp_is_bad", mix.pk),
        )
        await mix.statuses.acreate(
            status=Status.objects.get(codename="laboratory_analyze_technolog_acception"), additional_data=add_data
        )
        await message.bot.send_message(
            chat_id=roles.Farshesostovitel.telegram_id,
            text="Фарш не прошел проверку ФХП дождитесь информации от технолога!",
        )
        await message.answer("ФХП анализ не прошел эталонные значение, ожидайте новый запрос")
        await state.finish()

    if len(add_data) == 0 and not bad_fhp:
        add_data.update(
            {
                "fat_proportion": state_data["fat_proportion"],
                "protein_proportion": state_data["protein_proportion"],
                "moisture_proportion": state_data["moisture_proportion"],
            }
        )
        await mix.statuses.acreate(
            status=Status.objects.get(codename="laboratory_analyze_finish"), additional_data=add_data
        )

        await message.answer("Данные ФХП успешно внесены")
        await mixer_notify_good_fhp_mix_meat(mix.pk, roles)
        await state.finish()


@dp.message_handler(state=FHPAnalysis.set_proteins)
async def set_protein_proportion_decimal_error_handler(message: Message, state: FSMContext):
    await message.answer("Массовая доля белков должна быть числом")


@dp.message_handler(state=FHPAnalysis.set_moisture)
async def set_moisture_proportion_decimal_error_handler(message: Message, state: FSMContext):
    await message.answer("Массовая доля влаги должна быть числом")


@dp.message_handler(state=FHPAnalysis.set_fats)
async def set_fat_proportion_decimal_error_handler(message: Message, state: FSMContext):
    await message.answer("Массовая доля жиров должна быть числом")


@dp.callback_query_handler(Text(startswith="fhp_pitch_mix"))
async def accept_minced_meat_batch_mix_2(call: types.CallbackQuery, state: FSMContext):
    mix_id = int(call.data.split("-")[1])
    await state.update_data(mix_id=mix_id)
    await call.message.answer("Ввести данные по смоле")
    await FHPAnalysis.set_pitch.set()
    await call.message.edit_reply_markup(None)
