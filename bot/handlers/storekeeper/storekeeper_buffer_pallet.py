import re

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import CallbackQuery

from Web.CRM.dataclasses import RolesModel
from Web.CRM.models import BufferPalletMars
from data.constants import FLOAT_REGEX
from bot.keyboards.second_minced_meat.second_minced_meat_kb import back_to_main_menu
from bot.keyboards.storekeeper.storekeeper_keyboards import storekeeper_mars_remains_actions
from bot.loader import dp


class RemainsBufferPallet(StatesGroup):
    pallet_id = State()
    box_count = State()
    brutto_weight = State()
    pallet_weight = State()


@dp.callback_query_handler(Text(startswith="remains_mars"))
async def remains_mars(call: CallbackQuery, state: FSMContext, roles: RolesModel):
    await call.message.delete()
    await call.message.answer("Выберите действие", reply_markup=storekeeper_mars_remains_actions())


@dp.callback_query_handler(Text(startswith="create_buffer_pallet"))
async def create_buffer_pallet(call: CallbackQuery, state: FSMContext, roles: RolesModel):
    await call.message.delete()
    await call.message.answer("Введите номер паллета", reply_markup=back_to_main_menu())
    await RemainsBufferPallet.pallet_id.set()


@dp.callback_query_handler(Text(startswith="add_to_buffer_pallet"))
async def create_buffer_pallet_2(call: CallbackQuery, state: FSMContext, roles: RolesModel):
    await call.message.delete()
    await state.update_data(pallet_id=BufferPalletMars.objects.filter(box_count__lt=45).first().pallet_id)
    await call.message.answer("Введите кол-во ящиков", reply_markup=back_to_main_menu())
    await RemainsBufferPallet.box_count.set()


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=RemainsBufferPallet.pallet_id)
async def load_minced_meat_to_pallet_number(message: types.Message, state: FSMContext, roles: RolesModel):
    await state.update_data(pallet_id=int(message.text))
    await message.answer("Введите кол-во ящиков", reply_markup=back_to_main_menu())
    await RemainsBufferPallet.box_count.set()


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=RemainsBufferPallet.box_count)
async def load_minced_meat_to_pallet_weight(message: types.Message, state: FSMContext):
    await state.update_data(box_count=int(message.text))
    state_data = await state.get_data()
    pallets = BufferPalletMars.objects.filter(box_count__lt=45)
    if state_data["box_count"] > 45 and not pallets.first():
        await message.answer("Введите вес брутто для 45 ящиков!", reply_markup=back_to_main_menu())
    elif pallets.first():
        pallets_count = pallets.first().box_count + state_data["box_count"] - 45
        pallets_to_add = state_data["box_count"] - pallets_count
        if pallets_count > 0:
            await message.answer(f"Введите вес брутто для {pallets_to_add} ящиков!", reply_markup=back_to_main_menu())
        else:
            await message.answer(
                f'Введите вес брутто для {state_data["box_count"]} ящиков!', reply_markup=back_to_main_menu()
            )
    else:
        await message.answer(
            f'Введите вес брутто для {state_data["box_count"]} ящиков!', reply_markup=back_to_main_menu()
        )

    await RemainsBufferPallet.brutto_weight.set()


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=RemainsBufferPallet.brutto_weight)
async def load_minced_meat_to_pallet_weight_2(message: types.Message, state: FSMContext):
    await state.update_data(brutto_weight=float(message.text))
    await message.answer("Введите вес паллета", reply_markup=back_to_main_menu())
    await RemainsBufferPallet.pallet_weight.set()


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=RemainsBufferPallet.pallet_weight)
async def load_minced_meat_to_pallet_weight_3(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    await state.update_data(
        pallet_weight=float(message.text),
        netto_weight=state_data["brutto_weight"] - state_data["box_count"] * 1.6 - float(message.text),
    )
    state_data = await state.get_data()
    pallets = BufferPalletMars.objects.filter(box_count__lt=45)
    if not pallets.first():
        if state_data["box_count"] > 45:
            remains = state_data["box_count"] - 45
            state_data["box_count"] = 45
            BufferPalletMars.objects.create(**state_data)
            await message.answer(
                f"Успешно создан буферный паллет!\nВ остатке осталось {remains} ящиков, создайте новый паллет!",
                reply_markup=storekeeper_mars_remains_actions(),
            )
        else:
            BufferPalletMars.objects.create(**state_data)
            await message.answer(
                "Успешно создан буферный паллет!\nВыберите дальнейшие действие",
                reply_markup=storekeeper_mars_remains_actions(),
            )
    else:
        pallet = pallets.first()
        remains = pallet.box_count + state_data["box_count"] - 45
        if remains > 0:
            pallet.box_count = 45
            pallet.brutto_weight += state_data["brutto_weight"]
            pallet.netto_weight = pallet.brutto_weight - pallet.box_count * 1.6 - state_data["pallet_weight"]
            pallet.save()
            await message.answer(
                f"Паллет №{pallet.pallet_id} успешно заполнен!\n\nВ остатке {remains} ящиков!\n\nСоздайте "
                f"новый буферный паллет",
                reply_markup=storekeeper_mars_remains_actions(),
            )
        else:
            pallet.box_count += state_data["box_count"]
            pallet.brutto_weight += state_data["brutto_weight"]
            pallet.netto_weight = pallet.brutto_weight - pallet.box_count * 1.6 - state_data["pallet_weight"]
            pallet.save()
            await message.answer(
                f"Паллет №{pallet.pallet_id} успешно дополнен!\n\nВыберите дальнейшие действие",
                reply_markup=storekeeper_mars_remains_actions(),
            )

    await state.reset_state()


@dp.message_handler(state=RemainsBufferPallet.box_count)
@dp.message_handler(state=RemainsBufferPallet.pallet_id)
async def num_error(message: types.Message, state: FSMContext):
    await message.answer("Данный параметр должен быть числом!")


@dp.message_handler(state=RemainsBufferPallet.brutto_weight)
@dp.message_handler(state=RemainsBufferPallet.pallet_weight)
@dp.message_handler(state=RemainsBufferPallet.pallet_weight)
async def set_weight_error(message: types.Message, state: FSMContext):
    await message.answer("Масса должна быть числом", reply_markup=back_to_main_menu())
