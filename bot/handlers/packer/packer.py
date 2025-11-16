from datetime import datetime, timedelta

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import Message

from bot.keyboards.mixer.mixer_kb import (
    packer_for_unload_keyboard,
    packer_for_unload_shocker_keyboard,
    packer_for_unload_shocker_second_minced_meat_keyboard,
)
from bot.loader import bot, dp
from bot.states.pallet_select import PalletSelect
from Web.CRM.dataclasses import RolesModel
from Web.CRM.models import MincedMeatBatchMix, MincedMeatBatchStatus, SecondMincedMeat, ShockerMixLoad, Status, Tilers


async def packer_notify_mix_meat(mix_id, roles: RolesModel):
    mix = MincedMeatBatchMix.objects.get(pk=mix_id)
    tiller_id = mix.statuses.filter(status__codename="mixer_tiller_mix_meat_end").first()

    text = f"""
        Выгрузите из плиточника
        Замес - {mix.production_id}
        Плиточник - {tiller_id.additional_data['tiller_id']}
        """

    await bot.send_message(
        chat_id=roles.packer.telegram_id, text=text, reply_markup=packer_for_unload_keyboard(mix_id)
    )


async def packer_notify_mix_meat_unload_shocker(mix_id, roles: RolesModel):
    mix = MincedMeatBatchMix.objects.get(pk=mix_id)

    shocker = ShockerMixLoad.objects.filter(minced_meat_batch_mix_id=mix.pk).first()
    text = f"""
        Выгрузите из шокера
        №паллета - {shocker.additional_data['pallet']}
        Шокер - {shocker.shocker_id}
        """

    await bot.send_message(
        chat_id=roles.packer.telegram_id, text=text, reply_markup=packer_for_unload_shocker_keyboard(mix.pk)
    )


async def packer_notify_second_mix_meat(second_minced_meat_id, roles: RolesModel):
    minced_meat = ShockerMixLoad.objects.get(pk=second_minced_meat_id)
    text = f"""
        Выгрузите из плиточника
        Вторфарш - {minced_meat.second_minced_meat.production_id}
        Шокер - {minced_meat.shocker_id}
        """

    await bot.send_message(
        chat_id=roles.packer.telegram_id,
        text=text,
        reply_markup=packer_for_unload_shocker_second_minced_meat_keyboard(minced_meat.pk),
    )


@dp.callback_query_handler(Text(startswith="pack_unloaded-"))
async def pack_unloaded(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    mix_id = int(call.data.split("-")[1])
    tiller = Tilers.objects.filter(minced_meat_batch_mix_id=mix_id).first()
    await PalletSelect.set_to_pallet.set()
    await state.update_data(mix_id=mix_id, tiller_id=tiller.pk)
    await call.message.answer("Введите номер палета")


@dp.callback_query_handler(Text(startswith="next_unloading"))
async def pack_unloaded_2(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    second_minced_meat = (
        ShockerMixLoad.objects.filter(
            status_unload=False, second_minced_meat__isnull=False, minced_meat_batch_mix_id__isnull=True
        )
        .exclude(second_minced_meat__statuses__status__codename="unload_shocker")
        .order_by("updated_at")
        .first()
    )
    mix = (
        MincedMeatBatchMix.objects.filter(statuses__status__codename__in=["mixer_mix_meat_end"])
        .all()
        .exclude(statuses__status__codename="unloaded_to_packer_end")
        .exclude(statuses__status__codename="unload_shocker_finish")
        .order_by("updated_at")
        .first()
    )
    if not mix and not second_minced_meat:
        await call.message.answer("В данный момент нету загруженных паллетов!")
    if second_minced_meat and not mix:
        unload_time = second_minced_meat.updated_at + timedelta(minutes=30, hours=2)
        await call.message.answer(f"Ближайшая выгрузка в {unload_time:%H:%M:%S}")
    if mix and not second_minced_meat:
        unload_time = mix.updated_at + timedelta(minutes=30, hours=2)
        await call.message.answer(f"Ближайшая выгрузка в {unload_time:%H:%M:%S}")
    if mix and second_minced_meat:
        if mix.updated_at > second_minced_meat.updated_at:
            unload_time = mix.updated_at + timedelta(minutes=30, hours=2)
        else:
            unload_time = second_minced_meat.updated_at + timedelta(minutes=30, hours=2)
        await call.message.answer(f"Ближайшая выгрузка в {unload_time:%H:%M:%S}")


def get_pallet_id(mix: MincedMeatBatchMix):
    pallet_data = MincedMeatBatchStatus.objects.filter(
        minced_meat_batch_mix_id=mix.pk, status__codename="mixer_tiller_mix_meat_end"
    ).first()
    if pallet_data:
        return int(pallet_data.additional_data.get("pallet", 0))


def get_all_pallets_ids():
    mixes = MincedMeatBatchMix.objects.filter(created_at__day=datetime.now().day).all()
    mix_pallets_ids = [get_pallet_id(mix) for mix in mixes]
    second_meats = SecondMincedMeat.objects.filter(created_at__day=datetime.now().day).all()
    second_palets = [meat.additional_data.get('pallet') for meat in second_meats if meat.additional_data]
    all_pallets_ids = [*mix_pallets_ids, *second_palets]
    all_pallets_ids = [id for id in all_pallets_ids if id is not None]
    all_pallets_ids.sort()
    return all_pallets_ids


@dp.message_handler(state=PalletSelect.set_to_pallet)
async def set_pallet(message: Message, state: FSMContext, roles: RolesModel):
    try:
        pallet_id = int(message.text)
    except Exception:
        await message.answer("Введенное значение должно быть числом!")
        return

    state_data = await state.get_data()
    # номера палетов 1
    all_pallets_ids = get_all_pallets_ids()
    if int(message.text) in all_pallets_ids:
        return await message.answer(
            f"Палетта {message.text} занята. \nСписок занятых палетт сегодня: "
            f"{[pid for pid in all_pallets_ids if pid]}\nВведите еще раз"
        )
    mix = MincedMeatBatchMix.objects.get(pk=state_data["mix_id"])
    tiller = Tilers.objects.filter(pk=state_data["tiller_id"]).first()

    mix.statuses.create(status_id=Status.objects.get(codename="unloaded_to_packer_end").pk)
    tiller.status = True
    tiller.minced_meat_batch_mix = None
    tiller.save()

    status = MincedMeatBatchStatus.objects.filter(
        minced_meat_batch_mix_id=mix.pk, status__codename="mixer_tiller_mix_meat_end"
    ).first()
    status.additional_data = {"pallet": pallet_id, "tiler_id": state_data["tiller_id"]}
    status.save()
    await message.answer("Выгрузка успешна")
    await state.finish()


@dp.callback_query_handler(Text(startswith="pack_unloaded_shock_second"))
async def pack_unloaded_3(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    id_meat = int(call.data.split("-")[1])
    minced_meat = ShockerMixLoad.objects.get(pk=id_meat)
    minced_meat.second_minced_meat.statuses.create(status_id=Status.objects.get(codename="unload_shocker_finish").pk)
    minced_meat.status_unload = True
    minced_meat.save()
    await call.message.answer("Выгрузка успешна")
    await state.finish()


@dp.callback_query_handler(Text(startswith="pack_unloaded_shock"))
async def pack_unloaded_4(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    mix_id = int(call.data.split("-")[1])
    mix = MincedMeatBatchMix.objects.get(pk=mix_id)
    shocker = ShockerMixLoad.objects.filter(minced_meat_batch_mix_id=mix.pk).first()
    shocker.status_unload = True
    shocker.save()
    await mix.statuses.acreate(status=Status.objects.get(codename="unload_shocker_finish"))
    await call.message.answer("Выгрузка успешна")
    await state.finish()
