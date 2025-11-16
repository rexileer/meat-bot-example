import re

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup

from Web.CRM.dataclasses import RolesModel
from Web.CRM.models import SecondMincedMeat, ShockerCamera, ShockerMixLoad
from data.constants import FLOAT_REGEX
from bot.keyboards.second_minced_meat.second_minced_meat_kb import (
    add_second_minced_kb,
    back_to_main_menu,
    cheburashka_select_and_back,
    select_shocker,
)
from bot.keyboards.storekeeper.storekeeper_keyboards import shocker_storekeeper_actions
from bot.loader import dp
from bot.states.second_minced_meat import SecondMincedMeatMKO_1, SecondMincedMeatMKO_Release, SecondMincedMeatMKO_2_3
from asgiref.sync import sync_to_async


# start_action
@dp.callback_query_handler(Text(equals="add_second_minced_meat"))
async def add_second_minced_meat(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Что вы собираетесь сделать?", reply_markup=add_second_minced_kb())


# set_mko_1_weight
@dp.callback_query_handler(Text(equals="add_second_minced_meat_mko_1"))
async def add_second_minced_meat_mko_1(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await SecondMincedMeatMKO_1.set_weight.set()
    await call.message.answer("Введите вес полученного МКО1", reply_markup=back_to_main_menu())


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=SecondMincedMeatMKO_1.set_weight)
async def set_weight_mko_1(message: types.Message, state: FSMContext):
    await message.answer("Введите вес тележки", reply_markup=cheburashka_select_and_back())
    await SecondMincedMeatMKO_1.set_weight_cart.set()
    await state.update_data(weight=float(message.text))


@dp.callback_query_handler(Text(startswith="cheburashka"), state=SecondMincedMeatMKO_1.set_weight_cart)
async def set_weight_cart_second_minced_release_callback(call: types.CallbackQuery, state: FSMContext):
    chebur_id = int(call.data.split("_")[1])
    state_data = await state.get_data()
    cart_weight = 27 if chebur_id == 1 else 43
    await SecondMincedMeat.objects.acreate(**{"type": 1, "weight": state_data["weight"] - cart_weight})
    await call.message.answer("Вторфарш успешно выпущен", reply_markup=add_second_minced_kb())
    await state.finish()


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=SecondMincedMeatMKO_1.set_weight_cart)
async def set_weight_cart_mko_1(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    await SecondMincedMeat.objects.acreate(
        **{"type": 1, "weight": state_data["weight"], "additional_data": {"cart_weight": float(message.text)}}
    )
    await message.answer("МКО1 успешно добавлен", reply_markup=add_second_minced_kb())
    await state.finish()


# set_released_mko
@dp.callback_query_handler(Text(equals="release_second_minced_meat"))
async def release_second_minced_meat(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await SecondMincedMeatMKO_Release.set_weight.set()
    await call.message.answer("Введите вес вторфарша", reply_markup=back_to_main_menu())


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=SecondMincedMeatMKO_Release.set_weight)
async def set_release_second_minced_meat(message: types.Message, state: FSMContext):
    await message.answer("Введите вес тележки", reply_markup=cheburashka_select_and_back())
    await SecondMincedMeatMKO_Release.set_weight_cart.set()
    await state.update_data(weight=float(message.text))


@dp.callback_query_handler(Text(startswith="cheburashka"), state=SecondMincedMeatMKO_Release.set_weight_cart)
async def set_weight_cart_second_minced_release_callback_2(call: types.CallbackQuery, state: FSMContext):
    chebur_id = int(call.data.split("_")[1])
    state_data = await state.get_data()
    cart_weight = 27 if chebur_id == 1 else 43
    await SecondMincedMeat.objects.acreate(**{"type": 0, "weight": state_data["weight"] - cart_weight})
    await call.message.answer("Вторфарш успешно выпущен", reply_markup=add_second_minced_kb())
    await state.finish()


@dp.message_handler(
    lambda message: re.match(FLOAT_REGEX, message.text), state=SecondMincedMeatMKO_Release.set_weight_cart
)
async def set_weight_cart_second_minced_release(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    await SecondMincedMeat.objects.acreate(
        **{"type": 0, "weight": state_data["weight"], "additional_data": {"cart_weight": float(message.text)}}
    )
    await message.answer("Вторфарш успешно выпущен", reply_markup=add_second_minced_kb())
    await state.finish()


# set_mko_2
@dp.callback_query_handler(Text(equals="add_second_minced_meat_mko_2"))
async def set_second_minced_meat_mko_2(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await SecondMincedMeatMKO_2_3.set_pallet_num.set()
    await state.update_data({"type": 2})
    await call.message.answer("Введите номер палета", reply_markup=back_to_main_menu())


@sync_to_async
def get_pallets_ids():
    ids = []
    for mix_load in ShockerMixLoad.objects.all():
        if mix_load.additional_data:
            if not mix_load.status_unload:
                ids.append(int(mix_load.additional_data["pallet"]))
    return ids


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=SecondMincedMeatMKO_2_3.set_pallet_num)
async def set_pallet_num_mko_2_3(message: types.Message, state: FSMContext):
    pallet_ids = await get_pallets_ids()
    # await message.answer(f'список занятых номеров: {pallet_ids}')
    if int(message.text) in pallet_ids:
        return await message.answer(f"Этот номер уже занят. список занятых номеров: {pallet_ids}")
    await state.update_data(pallet=int(message.text))
    await message.answer("Введите вес паллеты", reply_markup=back_to_main_menu())
    await SecondMincedMeatMKO_2_3.set_pallet_weight.set()


@dp.message_handler(
    lambda message: re.match(FLOAT_REGEX, message.text), state=SecondMincedMeatMKO_2_3.set_pallet_weight
)
async def set_pallet_weight_num_mko_2_3(message: types.Message, state: FSMContext):
    await state.update_data(pallet_weight=int(message.text))
    await message.answer("Введите кол-во ящкиков", reply_markup=back_to_main_menu())
    await SecondMincedMeatMKO_2_3.set_box_count.set()


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=SecondMincedMeatMKO_2_3.set_box_count)
async def set_box_count_num_mko_2_3(message: types.Message, state: FSMContext):
    await state.update_data(box_count=int(message.text))
    await message.answer("Введите вес брутто", reply_markup=back_to_main_menu())
    await SecondMincedMeatMKO_2_3.set_brutto_weight.set()


@dp.message_handler(
    lambda message: re.match(FLOAT_REGEX, message.text), state=SecondMincedMeatMKO_2_3.set_brutto_weight
)
async def set_brutto_weight_mko_2_3(message: types.Message, state: FSMContext, roles: RolesModel):
    state_data = await state.get_data()
    await state.update_data(brutto_weight=int(message.text), weight=int(message.text))
    await state.update_data(net_weight=int(message.text) - state_data["box_count"] * 1.6 - state_data["pallet_weight"])
    shocker_list = sorted([key for key, val in ShockerCamera.get_available_shocker().items() if val > 0])
    if not shocker_list:
        await message.bot.send_message(
            roles.technologist.telegram_id,
            "Все щокеры заняты! Нету возможности загрузить новый вторфарш! Требуется ваше внимение!",
        )

    await message.answer("Выберите камеру шоковой заморозки", reply_markup=select_shocker())
    await SecondMincedMeatMKO_2_3.set_shock_chamber_num.set()


@dp.callback_query_handler(state=SecondMincedMeatMKO_2_3.set_shock_chamber_num)
async def set_shock_chamber_num_mko_2_3(call: types.CallbackQuery, state: FSMContext):
    shocker_id = int(call.data.split("-")[1])
    await state.update_data(shock_chamber_num=shocker_id)
    state_data = await state.get_data()
    keyboard = InlineKeyboardMarkup(row_width=2)
    second_minced_meat: SecondMincedMeat = await SecondMincedMeat.objects.acreate(
        type=state_data["type"], weight=state_data["net_weight"], additional_data=state_data
    )
    await call.message.answer(
        f'МКО{state_data["type"]} успешно добавлен', reply_markup=keyboard.add(*shocker_storekeeper_actions())
    )
    await ShockerMixLoad.objects.acreate(
        shocker_id=shocker_id, second_minced_meat_id=second_minced_meat.pk, additional_data=state_data
    )

    await state.reset_state()
    await call.message.delete()


# set_mko_3
@dp.callback_query_handler(Text(equals="add_second_minced_meat_mko_3"))
async def set_second_minced_meat_mko_3(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.update_data({"type": 3})
    await SecondMincedMeatMKO_2_3.set_pallet_num.set()
    await call.message.answer("Введите номер палета", reply_markup=back_to_main_menu())


# @dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text),
#                     state=SecondMincedMeatMKO_2_3.set_mko_3_weight)
# async def set_mko_3_weight(message: types.Message, state: FSMContext):
#     await state.update_data(weight=float(message.text))
#     await SecondMincedMeatMKO_2_3.set_pallet_num.set()
#     await message.answer('Введите номер палета', reply_markup=back_to_main_menu())


@dp.message_handler(state=SecondMincedMeatMKO_2_3.set_pallet_num)
@dp.message_handler(state=SecondMincedMeatMKO_2_3.set_box_count)
@dp.message_handler(state=SecondMincedMeatMKO_2_3.set_brutto_weight)
@dp.message_handler(state=SecondMincedMeatMKO_2_3.set_shock_chamber_num)
async def set_num_error(message: types.Message, state: FSMContext):
    await message.answer("Данный параметр должен быть числом!")


@dp.message_handler(state=SecondMincedMeatMKO_2_3.set_pallet_weight)
@dp.message_handler(state=SecondMincedMeatMKO_2_3.set_mko_3_weight)
@dp.message_handler(state=SecondMincedMeatMKO_Release.set_weight)
@dp.message_handler(state=SecondMincedMeatMKO_Release.set_weight_cart)
@dp.message_handler(state=SecondMincedMeatMKO_1.set_weight)
@dp.message_handler(state=SecondMincedMeatMKO_1.set_weight_cart)
async def set_weight_error(message: types.Message, state: FSMContext):
    await message.answer("Вес должен быть числом", reply_markup=back_to_main_menu())
