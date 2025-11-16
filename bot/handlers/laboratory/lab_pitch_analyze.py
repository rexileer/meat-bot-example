import re

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from bot.loader import dp
from bot.states.fhp_analysis import FHPAnalysis
from data.constants import FLOAT_REGEX
from Web.CRM.dataclasses import RolesModel
from Web.CRM.models import MincedMeatBatchMix


@dp.callback_query_handler(Text(startswith="analyze_pitch_mix"))
async def accept_minced_meat_batch_mix(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Ввести данные по смоле")
    await FHPAnalysis.set_pitch.set()
    await call.message.edit_reply_markup(None)


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=FHPAnalysis.set_pitch)
async def finish_fhp_pitch(message: types.Message, state: FSMContext, roles: RolesModel):
    state_data = await state.get_data()
    mix = MincedMeatBatchMix.objects.get(pk=state_data.get("mix_id"))
    mix_status = mix.statuses.get(status__codename="laboratory_analyze_finish")
    add_data = mix_status.additional_data
    add_data.update({"pitch": float(message.text)})
    mix_status.additional_data = add_data
    mix_status.save()
    await message.answer("Анализ по смоле успешно добавлен!")
    await state.finish()
