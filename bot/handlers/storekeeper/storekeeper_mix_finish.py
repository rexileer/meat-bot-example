import logging
import re

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from django.utils import timezone

from bot.handlers.packer.packer import get_all_pallets_ids, get_pallet_id
from bot.keyboards.main_menu import main_menu_keyboard
from bot.keyboards.mixer.mixer_kb import start_storekeeper_and_mark_keyboard
from bot.keyboards.technologist.technologist_check_keyboard import (
    finish_storekeepers_minced_meat, next_from_photo_storekeepers)
from bot.loader import bot, dp
from bot.utils.file_storage import save_file_from_telegram
from data.constants import FLOAT_REGEX
from Web.CRM.dataclasses import RolesModel
from Web.CRM.models import (MincedMeatBatchMix, MincedMeatBatchStatus,
                            SecondMincedMeat, SecondMincedMeatBatchFile,
                            Status)


class StoreKeepeStoringAndMarking(StatesGroup):
    block_count = State()
    all_weight = State()
    weight_pallet = State()
    weight_pack = State()
    photos = State()
    confirm = State()
    date = State()
    number_pallet = State()


async def storekeeper_notify_mix_meat(mix_id, roles: RolesModel):
    mix = MincedMeatBatchMix.objects.get(pk=mix_id)
    data = (
        mix.statuses.filter(status__codename="mixer_tiller_mix_meat_end")
        .exclude(status__codename="palletizing_end")
        .first()
    )
    if not data:
        return
        # data  = ShockerMixLoad.objects.filter(minced_meat_batch_mix_id=mix.pk).first()
    text = f"""Название фарша - {mix.minced_meat_batch.recipe.name}

        ID замеса {mix.production_id}

        № паллета {data.additional_data['pallet']}
        """

    await bot.send_message(
        chat_id=roles.storekeeper.telegram_id, text=text, reply_markup=start_storekeeper_and_mark_keyboard(mix_id)
    )


@dp.callback_query_handler(Text(startswith="unload_meat"))
async def unload_meat(call: types.CallbackQuery, state: FSMContext):
    buttons = [
        [
            InlineKeyboardButton(text="Принять фарш Марс", callback_data="__unload_meat:mars"),
        ],
        [
            InlineKeyboardButton(text="Принять МКО", callback_data="__unload_meat:mko"),
        ],
        [
            InlineKeyboardButton(text="Принять МКО (продажа)", callback_data="__unload_meat:mko_sell"),
        ],
        [
            InlineKeyboardButton(text="Принять Вторфарш", callback_data="__unload_meat:sec_meat"),
        ],
        [
            InlineKeyboardButton(text="Назад", callback_data="return"),
        ],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_reply_markup(reply_markup=keyboard)


@dp.callback_query_handler(Text(startswith="__unload_meat"))
async def unload_meat_2(call: types.CallbackQuery, state: FSMContext):
    await StoreKeepeStoringAndMarking.date.set()
    await state.update_data(meat_type=call.data.split(":")[1])
    await call.message.edit_text("Введите дату производства в формате 11.11.2024")


@dp.message_handler(
    lambda message: re.match(r"[0-9]{2}\.[0-9]{2}\.[0-9]{4}", message.text), state=StoreKeepeStoringAndMarking.date
)
async def set_date_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()
    if state_data["meat_type"] == "mars":
        prod_id = f"{message.text[0]}{message.text[1]}{message.text[3]}{message.text[4]}/1/Марс"
        mix = await MincedMeatBatchMix.objects.acreate(production_id=prod_id)
        await state.update_data(minced_meat_id=mix.id, msg_id=message.message_id)
    if state_data["meat_type"] in ["mko", "mko_sell"]:
        prod_id = f"{message.text[0]}{message.text[1]}{message.text[3]}{message.text[4]}/1/МКО"
        if state_data["meat_type"] == "mko_sell":
            prod_id += " Продажа"
        sec_mix = await SecondMincedMeat.objects.acreate(production_id=prod_id, type=1)
        await state.update_data(second_meat_id=sec_mix.id, is_second=True, msg_id=message.message_id)
    if state_data["meat_type"] in ["sec_meat"]:
        prod_id = f"{message.text[0]}{message.text[1]}{message.text[3]}{message.text[4]}/1/"
        sec_mix = await SecondMincedMeat.objects.acreate(production_id=prod_id, type=0)
        await state.update_data(second_meat_id=sec_mix.id, is_second=True, msg_id=message.message_id)
    await StoreKeepeStoringAndMarking.number_pallet.set()
    await message.answer("Введите номер паллеты")


@dp.message_handler(lambda message: str(message.text).isnumeric(), state=StoreKeepeStoringAndMarking.number_pallet)
async def set_number_pallet_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()
    
    # Проверяем, создали ли мы новый замес через "Принять фарш Марс" или работаем с существующим
    if state_data.get("minced_meat_id"):
        # Это был новый замес "Принять фарш Марс" → ищем существующий по паллету
        pallet_num = int(message.text)
        # Ищем замес с таким паллетом (pallet_is_set или mixer_tiller_mix_meat_end)
        existing_mix = MincedMeatBatchMix.objects.filter(
            statuses__status__codename__in=["pallet_is_set", "mixer_tiller_mix_meat_end"],
            statuses__additional_data__contains={"pallet": pallet_num}
        ).order_by("-created_at").first()
        
        if existing_mix:
            # Нашли существующий замес → удаляем созданный и работаем с найденным
            await MincedMeatBatchMix.objects.filter(pk=state_data["minced_meat_id"]).adelete()
            await state.update_data(minced_meat_id=existing_mix.pk)
        else:
            # Не нашли → работаем с новым, ставим mixer_tiller_mix_meat_end
            await MincedMeatBatchStatus.objects.acreate(
                minced_meat_batch_mix_id=state_data["minced_meat_id"],
                status=Status.objects.get(codename="mixer_tiller_mix_meat_end"),
                additional_data={"pallet": pallet_num},
            )
    
    elif state_data.get("is_second"):
        second = SecondMincedMeat.objects.get(pk=state_data["second_meat_id"])
        second.additional_data = {"pallet": int(message.text)}
        second.save()
    
    await StoreKeepeStoringAndMarking.block_count.set()
    await message.answer("Введите кол-во блоков")


@dp.callback_query_handler(Text(startswith="second_meat"))
async def sto_mar_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    second_meat_id = int(call.data.split("-")[1])
    await state.update_data(second_meat_id=second_meat_id, is_second=True, msg_id=call.message.message_id)
    await StoreKeepeStoringAndMarking.block_count.set()
    await call.message.answer("Введите кол-во блоков")


@dp.callback_query_handler(Text(startswith="sto_mar"))
async def sto_mar_start_2(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    minced_meat_id = int(call.data.split("-")[1])
    await state.update_data(minced_meat_id=minced_meat_id, msg_id=call.message.message_id)
    await StoreKeepeStoringAndMarking.block_count.set()
    await call.message.answer("Введите кол-во блоков")


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=StoreKeepeStoringAndMarking.block_count)
async def set_all_weight_handler(message: Message, state: FSMContext):
    await state.update_data(block_count=int(message.text))
    await StoreKeepeStoringAndMarking.all_weight.set()
    await message.answer("Введите общий вес")


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=StoreKeepeStoringAndMarking.all_weight)
async def set_weight_pallet_handler(message: Message, state: FSMContext):
    await state.update_data(all_weight=float(message.text))
    await StoreKeepeStoringAndMarking.weight_pallet.set()
    await message.answer("Введите вес паллеты")


@dp.message_handler(
    lambda message: re.match(FLOAT_REGEX, message.text), state=StoreKeepeStoringAndMarking.weight_pallet
)
async def set_weight_pallet_handler_2(message: Message, state: FSMContext):
    await state.update_data(weight_pallet=float(message.text))
    await StoreKeepeStoringAndMarking.weight_pack.set()
    await message.answer("Введите вес упаковочного материала")


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=StoreKeepeStoringAndMarking.weight_pack)
async def set_pallet_photos_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()
    if (float(state_data["all_weight"]) - float(state_data["weight_pallet"]) - float(message.text)) < 0:
        await state.reset_state()
        if not state_data.get("is_second"):
            await state.update_data(minced_meat_id=state_data["minced_meat_id"], msg_id=state_data["msg_id"])
        else:
            await state.update_data(
                second_meat_id=state_data["second_meat_id"], is_second=True, msg_id=state_data["msg_id"]
            )
        await StoreKeepeStoringAndMarking.block_count.set()
        await message.answer("Ошибка. Вес нетто не должен быть отрицательным. Введите значения заново")
        return await message.answer("Введите кол-во блоков")
    await state.update_data(weight_pack=float(message.text))
    await StoreKeepeStoringAndMarking.photos.set()
    await message.answer("Прикрепите фото температурного режима и палетного листа")
    await state.update_data(photos=[])


@dp.message_handler(state=StoreKeepeStoringAndMarking.block_count)
@dp.message_handler(state=StoreKeepeStoringAndMarking.all_weight)
@dp.message_handler(state=StoreKeepeStoringAndMarking.weight_pallet)
@dp.message_handler(state=StoreKeepeStoringAndMarking.weight_pack)
async def set_protein_proportion_decimal_error_handler(message: Message, state: FSMContext):
    await message.answer("Данный параметр должен быть числом!")


@dp.message_handler(content_types=["photo"], state=StoreKeepeStoringAndMarking.photos)
async def set_photo_handler(message: Message, state: FSMContext):
    object_name = await save_file_from_telegram(
        file_id=message.photo[-1].file_id, dir_name="minced_batch_files", file_type=".jpeg"
    )

    state_data = await state.get_data()
    if "photos" not in state_data:
        state_data.update({"photos": []})
    state_data["photos"].append(object_name)
    await state.set_data(state_data)
    await message.answer(
        (
            "Фото температурного режима и палетного листа успешно загружено. "
            'Загрузите еще или нажмите "Подтвердить", чтобы продолжить'
        ),
        reply_markup=next_from_photo_storekeepers(),
    )


@dp.callback_query_handler(Text(startswith="sto_mar_continue_photo"), state=StoreKeepeStoringAndMarking.photos)
async def sto_mar_continue_photo(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    state_data = await state.get_data()
    if not state_data.get("is_second"):
        mix = MincedMeatBatchMix.objects.get(pk=state_data["minced_meat_id"])
    else:
        second = SecondMincedMeat.objects.get(pk=state_data["second_meat_id"])

    text = f"""    Проверьте правильность введенных данных

    {f'Фарш -{mix.production_id}' if not state_data.get('is_second') else f'Вторфарш -{second.production_id}'}
    {''}
    Вес бутто - {state_data['all_weight']} кг
    Вес палеты - {state_data['weight_pallet']} кг
    Вес упаковки - {state_data['weight_pack']} кг
    Вес нетто - {float(state_data['all_weight']) - float(state_data['weight_pallet']) - float(
        state_data['weight_pack'])} кг

"""

    await state.update_data(
        weight_raw=float(state_data["all_weight"])
        - float(state_data["weight_pallet"])
        - float(state_data["weight_pack"])
    )
    await call.message.answer(text, reply_markup=finish_storekeepers_minced_meat())
    await StoreKeepeStoringAndMarking.confirm.set()


@dp.callback_query_handler(Text(startswith="sto_mar_finish"), state=StoreKeepeStoringAndMarking.confirm)
async def sto_mar_finish_handler(call: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    try:
        await bot.edit_message_reply_markup(
            chat_id=call.from_user.id, message_id=state_data["msg_id"], reply_markup=None
        )
    except Exception as e:
        logging.error(e)
    state_data.update(
        weight_raw=float(state_data["all_weight"])
        - float(state_data["weight_pallet"])
        - float(state_data["weight_pack"])
    )
    if not state_data.get("is_second"):
        mix = MincedMeatBatchMix.objects.get(pk=state_data["minced_meat_id"])
        if not mix.statuses.filter(status__codename="palletizing").first():
            await mix.statuses.acreate(status_id=Status.objects.get(codename="palletizing").pk, additional_data=state_data)
        # Ставим palletizing_end с данными (weight_raw и т.п.)
        await mix.statuses.acreate(status_id=Status.objects.get(codename="palletizing_end").pk, additional_data=state_data)
        # Ставим work_is_finished для финализации
        await mix.statuses.acreate(status_id=Status.objects.get(codename="work_is_finished").pk)
        # if state_data.get("photos"):
        # for photo in state_data['photos']:
        #     await MincedMeatBatchFile.objects.acreate(
        #         minced_meat_batch_id=mix.minced_meat_batch.pk,
        #         name="photo_marked_and_storing", file_location=photo
        #     )
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.answer("Работа с фаршем закончена", reply_markup=main_menu_keyboard(call.from_user.id))
    else:
        second = SecondMincedMeat.objects.get(pk=state_data["second_meat_id"])
        await second.statuses.acreate(
            status=Status.objects.get(codename="palletizing_end"), additional_data=state_data
        )
        if state_data.get("photos"):
            for photo in state_data["photos"]:
                await SecondMincedMeatBatchFile.objects.acreate(
                    second_minced_meat_id=second.pk, name="photo_marked_and_storing_second_meat", file_location=photo
                )
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.answer("Работа с вторфашем закончена", reply_markup=main_menu_keyboard(call.from_user.id))
        await second.statuses.acreate(status=Status.objects.get(codename="work_is_finished"))
    await state.finish()


@dp.callback_query_handler(Text(startswith="sto_mar_reset"), state=StoreKeepeStoringAndMarking.confirm)
async def sto_mar_reset_handler(call: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    await state.reset_state()
    await call.message.delete()
    if not state_data.get("is_second"):
        await state.update_data(minced_meat_id=state_data["minced_meat_id"], msg_id=state_data["msg_id"])
    else:
        await state.update_data(
            second_meat_id=state_data["second_meat_id"], is_second=True, msg_id=state_data["msg_id"]
        )
    await StoreKeepeStoringAndMarking.block_count.set()
    await call.message.answer("Введите кол-во блоков")
