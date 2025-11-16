import re
from datetime import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State

from Web.CRM.dataclasses import RolesModel
from Web.CRM.models import MincedMeatBatchMix, Status, MincedMeatBatchStatus
from data.constants import FLOAT_REGEX
from bot.loader import dp


class LoadToPallet(StatesGroup):
    pallet_number = State()


@dp.callback_query_handler(Text(startswith="farshloadshoсk_mix-"))
async def load_minced_meat_to_shocker(call: types.CallbackQuery, state: FSMContext, roles: RolesModel):
    mix_id = int(call.data.split("-")[1])
    await call.message.delete()
    msg = await call.message.answer("Введите номер паллеты")
    await state.update_data(mix_id=mix_id, msg_id=msg.message_id)
    await LoadToPallet.pallet_number.set()


def pallet_id(mix: MincedMeatBatchMix):
    pallet_data = MincedMeatBatchStatus.objects.filter(
        minced_meat_batch_mix_id=mix.pk, status__codename="mixer_tiller_mix_meat_end"
    ).first()
    if pallet_data:
        return int(pallet_data.additional_data.get("pallet", 0))


def pallet_id_v2(mix: MincedMeatBatchMix):
    statuses = Status.objects.filter(codename__in=['pallet_is_set',])
    ids = [status.pk for status in statuses]
    pallet_data = mix.statuses.filter(status_id__in=ids).all()
    if pallet_data:
        return [pal.additional_data["pallet"] for pal in pallet_data if pal.additional_data.get("pallet")]
    else:
        return []


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=LoadToPallet.pallet_number)
async def load_minced_meat_to_pallet_number(message: types.Message, state: FSMContext):
    mixes = MincedMeatBatchMix.objects.filter(created_at__day=datetime.now().day).all()
    # all_pallets_ids = [pallet_id(mix) for mix in mixes]
    all_pallets_ids = []
    for mix in mixes:
        all_pallets_ids.extend(pallet_id_v2(mix))
    # await message.answer(f"all_pallets = {all_pallets_ids}")
    if int(message.text) in all_pallets_ids:
        return await message.answer(
            f"Палетта {message.text} занята. \nСписок занятых палетт сегодня: "
            f"{[pid for pid in all_pallets_ids if pid]}\nВведите еще раз"
        )
    await state.update_data(pallet=int(message.text))
    state_data = await state.get_data()
    mix = MincedMeatBatchMix.objects.get(pk=state_data["mix_id"])
    await message.bot.delete_message(message.from_user.id, state_data["msg_id"])
    await mix.statuses.acreate(
        status_id=Status.objects.get(codename="pallet_is_set").pk, additional_data={"pallet": state_data["pallet"]}
    )
    await mix.statuses.acreate(status=Status.objects.get(codename="mixer_mix_meat_end"))
    await state.reset_state()
    await message.answer("Паллет успешно установлен!")


@dp.message_handler(state=LoadToPallet.pallet_number)
async def num_error(message: types.Message, state: FSMContext):
    await message.answer("Данный параметр должен быть числом!")
