import re
from datetime import datetime

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import Message, CallbackQuery

from Web.CRM.models import RawMaterial, Company, RawMeatBatch, RawMeatBatchFile, Users, TTNType
from Web.CRM.utils import translit_letters
from bot.handlers.technologist.utils.technologist_check import set_technologist_check_message
from bot.keyboards.main_menu import main_menu_keyboard
from bot.keyboards.raw_meat_batch.raw_meat_keyboards import (
    raw_material_keyboard,
    set_condition_keyboard,
    set_photo_ttn_keyboard,
    set_weight_keyboard,
    set_photo_vet_keyboard,
    set_companies_keyboard,
    set_buh_accounting_keyboard,
)
from bot.keyboards.shared import skip_keyboard, return_keyboard
from bot.keyboards.technologist.technologist_check_keyboard import set_technologist_check_keyboard
from bot.loader import dp, bot
from bot.states.new_raw_meat_batch_form import NewRawMeatBatchForm
from bot.utils.api.get_vet_docs import get_data_from_mercury
from bot.utils.api.vetis_api import start_process
from bot.utils.file_storage import save_file_from_telegram
from data.constants import DATE_FORMAT, FLOAT_REGEX


@dp.callback_query_handler(Text(startswith="main_menu_new_raw_meat_batch"))
async def new_raw_meat_batch_handler(call: CallbackQuery, state: FSMContext):
    await call.message.answer(text="Выберите компанию", reply_markup=set_companies_keyboard())
    await NewRawMeatBatchForm.set_company.set()


@dp.message_handler(state=NewRawMeatBatchForm.set_check)
async def set_wait_handler(message: Message):
    await message.answer("Приёмка временно запрещена. Дождитесь ответа технолога, что бы продолжить.")


@dp.message_handler(state=NewRawMeatBatchForm.set_company)
async def set_company_handler(message: Message, state: FSMContext):
    company = Company.objects.filter(name=message.text).first()
    if not company:
        await message.answer(text="Пожалуйста выберите компанию")
        return

    await state.update_data(company_id=company.id)
    raw_materials = RawMaterial.objects.all()
    await message.answer(text=" Выберите тип сырья", reply_markup=raw_material_keyboard(raw_materials))
    await NewRawMeatBatchForm.set_raw_material.set()


@dp.message_handler(state=NewRawMeatBatchForm.set_raw_material)
async def set_raw_material_handler(message: Message, state: FSMContext):
    raw_material = RawMaterial.objects.filter(name__icontains=message.text).first()
    if not raw_material:
        raw_material, _ = await RawMaterial.objects.aget_or_create(
            type=translit_letters(message.text), name=message.text, custom=True
        )

    await state.update_data(raw_material_id=raw_material.pk)

    raw_materials = TTNType.objects.all()
    await message.answer(text="Выберите тип сырья по номенклатуре", reply_markup=raw_material_keyboard(raw_materials))
    await NewRawMeatBatchForm.set_ttntype_raw_material.set()


@dp.message_handler(state=NewRawMeatBatchForm.set_ttntype_raw_material)
async def set_ttntype_raw_material_handler(message: Message, state: FSMContext):
    ttn_type = TTNType.objects.filter(name__icontains=message.text).first()
    if not ttn_type:
        ttn_type, _ = await TTNType.objects.aget_or_create(
            type=translit_letters(message.text), name=message.text, custom=True
        )

    await state.update_data(ttn_type_id=ttn_type.pk)

    await message.answer(text="Выберите кондицию", reply_markup=set_condition_keyboard())
    await NewRawMeatBatchForm.set_condition.set()


@dp.message_handler(text=["Охлажденное", "Замороженое"], state=NewRawMeatBatchForm.set_condition)
async def set_condition_handler(message: Message, state: FSMContext):
    condition_mapping = {"Охлажденное": "chilled", "Замороженое": "frozen"}

    await state.update_data(condition=condition_mapping[message.text])
    await message.answer(text="Пришлите фото рефа фуры", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_photo_ref_truck.set()


# NEW BLOCKS


@dp.message_handler(text="Пропустить", state=NewRawMeatBatchForm.set_photo_ref_truck)
async def set_photo_ref_truck_skip_handler(message: Message, state: FSMContext):
    await message.answer(
        "Пришлите фото замера температры в кузове в момент открытия машины", reply_markup=skip_keyboard()
    )
    await NewRawMeatBatchForm.set_photo_body_temperature_truck.set()


@dp.message_handler(content_types=["photo"], state=NewRawMeatBatchForm.set_photo_ref_truck)
async def set_photo_ref_truck_handler(message: Message, state: FSMContext):
    object_name = await save_file_from_telegram(
        file_id=message.photo[-1].file_id, dir_name="raw_meat_batch", file_type=".jpeg"
    )
    await state.update_data(photo_ref_truck=object_name)

    await message.answer(
        "Пришлите фото замера температры в кузове в момент открытия машины", reply_markup=skip_keyboard()
    )
    await NewRawMeatBatchForm.set_photo_body_temperature_truck.set()


@dp.message_handler(state=NewRawMeatBatchForm.set_photo_ref_truck)
async def set_photo_ref_truck_content_type_error_handler(message: Message, state: FSMContext):
    await message.answer("Необходимо отправить фотографию", reply_markup=skip_keyboard())


@dp.message_handler(text="Пропустить", state=NewRawMeatBatchForm.set_photo_body_temperature_truck)
async def set_photo_body_temperature_truck_handler(message: Message, state: FSMContext):
    await message.answer("Введите температру в кузове в момент открытия машины", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_body_temperature_truck.set()


@dp.message_handler(content_types=["photo"], state=NewRawMeatBatchForm.set_photo_body_temperature_truck)
async def set_photo_body_temperature_truck_handler_2(message: Message, state: FSMContext):
    object_name = await save_file_from_telegram(
        file_id=message.photo[-1].file_id, dir_name="raw_meat_batch", file_type=".jpeg"
    )
    await state.update_data(photo_body_temperature_truck=object_name)

    await message.answer("Введите температру в кузове в момент открытия машины", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_body_temperature_truck.set()


@dp.message_handler(state=NewRawMeatBatchForm.set_photo_body_temperature_truck)
async def set_photo_body_temperature_truck_content_type_error_handler(message: Message, state: FSMContext):
    await message.answer("Необходимо отправить фотографию", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_body_temperature_truck.set()


@dp.message_handler(text="Пропустить", state=NewRawMeatBatchForm.set_body_temperature_truck)
async def set_body_temperature_truck_skip_handler(message: Message):
    await message.answer(text="Введите дату производства (пример: 20.01.2022)", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_manufacture_date.set()


@dp.message_handler(content_types=["text"], state=NewRawMeatBatchForm.set_body_temperature_truck)
async def set_body_temperature_truck_handler(message: Message, state: FSMContext):
    try:
        temperature = float(message.text)
        state_data = await state.get_data()
        condition = state_data.get("condition")
        if (condition == "frozen" and temperature <= float(-8)) or (
            condition == "chilled" and float(-2) <= temperature <= float(4)
        ):
            await state.update_data(body_temperature_truck=str(temperature))
        else:
            material_id = state_data.get("raw_material_id")
            raw_material = RawMaterial.objects.get(id=material_id)
            msg = await set_technologist_check_message(
                raw_material.name, condition, "body_temperature_truck", temperature
            )
            await bot.send_message(
                Users.objects.get(position__code_name="technologist").telegram_id,
                msg,
                reply_markup=set_technologist_check_keyboard(
                    message.from_user.id, "body_temperature_truck", temperature
                ),
            )
            await message.answer("Приёмка временно запрещена. Дождитесь ответа технолога, что бы продолжить.")
            await NewRawMeatBatchForm.set_check.set()
            return
    except ValueError:
        return await message.answer("Температура должна быть числом")

    await message.answer(text="Введите дату производства (пример: 20.01.2022)", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_manufacture_date.set()


@dp.message_handler(text="Пропустить", state=NewRawMeatBatchForm.set_manufacture_date)
async def set_manufacture_date_skip_handler(message: Message):
    await message.answer(text="Введите номер ТТН", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_number_ttn.set()


@dp.message_handler(content_types=["text"], state=NewRawMeatBatchForm.set_manufacture_date)
async def set_manufacture_date_handler(message: Message, state: FSMContext):
    try:
        datetime.strptime(message.text, DATE_FORMAT)
    except ValueError:
        return await message.answer(
            "Дата производства введена в неверном формате, попробуйте снова (пример: 20.01.2022)"
        )

    await state.update_data(manufacture_date=message.text)

    await message.answer(text="Введите номер ТТН", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_number_ttn.set()


###


@dp.message_handler(text="Пропустить", state=NewRawMeatBatchForm.set_number_ttn)
async def set_number_ttn_skip_handler(message: Message, state: FSMContext):
    await message.answer("Пришлите фото УПД", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_photo_ypd.set()


@dp.message_handler(content_types=["text"], state=NewRawMeatBatchForm.set_number_ttn)
async def set_number_ttn_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.update_data(number_ttn=message.text)
    company = Company.objects.get(pk=data.get("company_id"))
    await message.answer("Пришлите фото УПД", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_photo_ypd.set()
    await start_process(state, message.text, company)


@dp.message_handler(content_types=["photo", "video"], state=NewRawMeatBatchForm.set_number_ttn)
async def set_number_ttn_content_type_error_handler(message: Message, state: FSMContext):
    await message.answer("Необходимо отправить текстовое сообщение", reply_markup=skip_keyboard())


@dp.message_handler(text="Пропустить", state=NewRawMeatBatchForm.set_photo_ypd)
async def set_photo_ypd_skip_handler(message: Message, state: FSMContext):
    await state.update_data(photos_ttn=[])
    await message.answer("Пришлите фото ТТН", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_photo_ttn.set()


@dp.message_handler(content_types=["photo"], state=NewRawMeatBatchForm.set_photo_ypd)
async def set_photo_ypd_handler(message: Message, state: FSMContext):
    object_name = await save_file_from_telegram(
        file_id=message.photo[-1].file_id, dir_name="raw_meat_batch", file_type=".jpeg"
    )
    await state.update_data(photo_ypd=object_name, photos_ttn=[])

    await message.answer("Пришлите фото ТТН", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_photo_ttn.set()


@dp.message_handler(state=NewRawMeatBatchForm.set_photo_ypd)
async def set_photo_ypd_content_type_error_handler(message: Message, state: FSMContext):
    await message.answer("Необходимо отправить фотографию", reply_markup=skip_keyboard())


@dp.message_handler(text="Пропустить", state=NewRawMeatBatchForm.set_photo_ttn)
async def set_photo_ttn_skip_handler(message: Message, state: FSMContext):
    await message.answer("Пришлите фото ТН", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_photo_tn.set()


@dp.message_handler(content_types=["photo"], state=NewRawMeatBatchForm.set_photo_ttn)
async def set_photo_ttn_handler(message: Message, state: FSMContext):
    object_name = await save_file_from_telegram(
        file_id=message.photo[-1].file_id, dir_name="raw_meat_batch", file_type=".jpeg"
    )
    state_data = await state.get_data()
    state_data["photos_ttn"].append(object_name)
    await state.set_data(state_data)
    await message.answer(
        'Фото ТТН успешно загружено. Загрузите еще или нажмите "Подтвердить", чтобы продолжить',
        reply_markup=set_photo_ttn_keyboard(),
    )


@dp.message_handler(text="Подтвердить", content_types=["text"], state=NewRawMeatBatchForm.set_photo_ttn)
async def set_photo_ttn_confirm_handler(message: Message, state: FSMContext):
    await message.answer("Пришлите фото ТН", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_photo_tn.set()


@dp.message_handler(state=NewRawMeatBatchForm.set_photo_ttn)
async def set_photo_ttn_content_type_error_handler(message: Message, state: FSMContext):
    await message.answer("Необходимо отправить фотографию", reply_markup=skip_keyboard())


@dp.message_handler(text="Пропустить", state=NewRawMeatBatchForm.set_photo_tn)
async def set_buh_accounting_handlerpass(message: Message, state: FSMContext):
    await state.update_data(photos_vet=[])
    await message.answer("Пришлите фото ЭВСД", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_photo_vet.set()


@dp.message_handler(content_types=["photo"], state=NewRawMeatBatchForm.set_photo_tn)
async def set_buh_accounting_handler(message: Message, state: FSMContext):
    object_name = await save_file_from_telegram(
        file_id=message.photo[-1].file_id, dir_name="raw_meat_batch", file_type=".jpeg"
    )
    await state.update_data(photo_tn=object_name)
    await state.update_data(photos_vet=[])

    await message.answer("Пришлите фото ЭВСД", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_photo_vet.set()


@dp.message_handler(content_types=["text"], state=NewRawMeatBatchForm.set_buh_accounting)
async def set_photo_tn_handler(message: Message, state: FSMContext):
    await state.update_data(buh_accounting=message.text)
    await message.answer("Введите общую массу", reply_markup=return_keyboard())
    await NewRawMeatBatchForm.set_weight.set()


@dp.message_handler(state=NewRawMeatBatchForm.set_photo_tn)
async def set_photo_tn_content_type_error_handler(message: Message, state: FSMContext):
    await message.answer("Необходимо отправить фотографию", reply_markup=skip_keyboard())


@dp.message_handler(text="Пропустить", state=NewRawMeatBatchForm.set_photo_vet)
async def set_photo_vet_skip_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("number_ttn"):
        await NewRawMeatBatchForm.set_wait.set()
        await get_data_from_mercury(state, message)
    else:
        await message.answer("Введите поставщика", reply_markup=return_keyboard())
        await NewRawMeatBatchForm.set_organization.set()


@dp.message_handler(content_types=["photo"], state=NewRawMeatBatchForm.set_photo_vet)
async def set_photo_vet_handler(message: Message, state: FSMContext):
    object_name = await save_file_from_telegram(
        file_id=message.photo[-1].file_id, dir_name="raw_meat_batch", file_type=".jpeg"
    )
    state_data = await state.get_data()
    state_data["photos_vet"].append(object_name)
    await state.set_data(state_data)
    await message.answer(
        'Фото ЭВСД успешно загружено. Загрузите еще или нажмите "Подтвердить", чтобы продолжить',
        reply_markup=set_photo_vet_keyboard(),
    )


@dp.message_handler(text="Подтвердить", content_types=["text"], state=NewRawMeatBatchForm.set_photo_vet)
async def set_photo_vet_confirm_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("number_ttn"):
        await NewRawMeatBatchForm.set_wait.set()
        await get_data_from_mercury(state, message)
    else:
        await message.answer("Введите поставщика", reply_markup=return_keyboard())
        await NewRawMeatBatchForm.set_organization.set()


@dp.message_handler(text="Пропустить", state=NewRawMeatBatchForm.set_wait)
async def set_wait_skip_handler(message: Message, state: FSMContext):
    await state.update_data(skip_getting_docs=True)
    await message.answer("Введите поставщика", reply_markup=return_keyboard())
    await NewRawMeatBatchForm.set_organization.set()


@dp.message_handler(state=NewRawMeatBatchForm.set_wait)
async def set_wait_handler_2(message: Message):
    await message.answer("Данные о ЭВСД пока не получены, пожалуйста подождите", reply_markup=skip_keyboard())


@dp.message_handler(state=NewRawMeatBatchForm.set_photo_vet)
async def set_photo_vet_content_type_error_handler(message: Message, state: FSMContext):
    await message.answer("Необходимо отправить фотографию", reply_markup=skip_keyboard())


@dp.message_handler(text="Совпадает", state=NewRawMeatBatchForm.set_organization)
async def set_organization_match_vet(message: Message, state: FSMContext):
    state_data = await state.get_data()
    await state.update_data(organization=state_data["organization_vet"])

    if state_data.get("weight_vet"):
        text = f'Объем продукции в ЭСВД: {state_data["weight_vet"]} кг\nСовпадает с реальным?'

        await message.answer(text, reply_markup=set_weight_keyboard())
    else:
        # await message.answer('Введите общую массу', reply_markup=return_keyboard())
        await message.answer("Укажите тип для бух.учета", reply_markup=set_buh_accounting_keyboard())
    await NewRawMeatBatchForm.set_buh_accounting.set()
    # await NewRawMeatBatchForm.set_weight.set()


@dp.message_handler(text="Не совпадает", state=NewRawMeatBatchForm.set_organization)
async def set_organization_not_match_vet(message: Message, state: FSMContext):
    await message.answer("Введите поставщика", reply_markup=skip_keyboard())


@dp.message_handler(state=NewRawMeatBatchForm.set_organization)
async def set_organization_handler(message: Message, state: FSMContext):
    await state.update_data(organization=message.text)

    state_data = await state.get_data()

    if state_data.get("weight_vet"):
        await message.answer(
            f"Объем продукции в ЭСВД: {state_data['weight_vet']} кг \nСовпадает с реальным?",
            reply_markup=set_weight_keyboard(),
        )
    else:
        # await message.answer('Введите общую массу', reply_markup=return_keyboard())
        await message.answer("Укажите тип для бух.учета", reply_markup=set_buh_accounting_keyboard())
    await NewRawMeatBatchForm.set_buh_accounting.set()
    # await NewRawMeatBatchForm.set_weight.set()


@dp.message_handler(text="Совпадает", state=NewRawMeatBatchForm.set_weight)
async def set_weight_match_vet(message: Message, state: FSMContext):
    state_data = await state.get_data()
    await state.update_data(weight=state_data["weight_vet"])

    await message.answer("Пришлите фото температурного режима продукции", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_photo_temperature.set()


@dp.message_handler(text="Не совпадает", state=NewRawMeatBatchForm.set_weight)
async def set_weight_not_match_vet(message: Message, state: FSMContext):
    await message.answer("Введите общую массу", reply_markup=skip_keyboard())


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=NewRawMeatBatchForm.set_weight)
async def set_weight_handler(message: Message, state: FSMContext):
    await state.update_data(weight=message.text.replace(",", "."))

    await message.answer("Пришлите фото температурного режима продукции", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_photo_temperature.set()


@dp.message_handler(state=NewRawMeatBatchForm.set_weight)
async def set_weight_decimal_error_handler(message: Message, state: FSMContext):
    await message.answer(text="Масса должна быть числом", reply_markup=return_keyboard())


@dp.message_handler(text="Пропустить", state=NewRawMeatBatchForm.set_photo_temperature)
async def set_photo_temperature_skip_handler(message: Message, state: FSMContext):
    await message.answer("Укажите температуру сырья при поступлении на склад", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_temperature.set()


@dp.message_handler(content_types=["photo"], state=NewRawMeatBatchForm.set_photo_temperature)
async def set_photo_temperature_handler(message: Message, state: FSMContext):
    object_name = await save_file_from_telegram(
        file_id=message.photo[-1].file_id, dir_name="raw_meat_batch", file_type=".jpeg"
    )
    await state.update_data(photo_temperature=object_name)

    await message.answer("Укажите температуру сырья при поступлении на склад", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_temperature.set()


@dp.message_handler(text="Пропустить", state=NewRawMeatBatchForm.set_temperature)
async def set_temperature_skip_handler(message: Message):
    await message.answer("Пришлите фотографию паллеты", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_photo_pallet.set()


@dp.message_handler(content_types=["text"], state=NewRawMeatBatchForm.set_temperature)
async def set_temperature_handler(message: Message, state: FSMContext):
    try:
        temperature = int(message.text)
        state_data = await state.get_data()
        condition = state_data.get("condition")
        if (condition == "frozen" and temperature <= -8) or (condition == "chilled" and -2 <= temperature <= 4):
            await state.update_data(temperature=str(temperature))
        else:
            material_id = state_data.get("raw_material_id")
            raw_material = RawMaterial.objects.get(id=material_id)
            msg = await set_technologist_check_message(raw_material.name, condition, "temperature", temperature)
            await bot.send_message(
                Users.objects.get(position__code_name="technologist").telegram_id,
                msg,
                reply_markup=set_technologist_check_keyboard(message.from_user.id, "temperature", temperature),
            )
            await message.answer("Приёмка временно запрещена. Дождитесь ответа технолога, что бы продолжить.")
            await NewRawMeatBatchForm.set_check.set()
            return
    except ValueError:
        return await message.answer("Температура должна быть числом")

    await message.answer("Пришлите фотографию паллеты", reply_markup=skip_keyboard())
    await NewRawMeatBatchForm.set_photo_pallet.set()


@dp.message_handler(state=NewRawMeatBatchForm.set_photo_temperature)
async def set_photo_temperature_content_type_error_handler(message: Message, state: FSMContext):
    await message.answer("Необходимо отправить фотографию", reply_markup=skip_keyboard())


@dp.message_handler(text="Пропустить", state=NewRawMeatBatchForm.set_photo_pallet)
async def set_photo_pallet_skip_handler(message: Message, state: FSMContext):
    await message.answer("Введите необходимое количество бирок", reply_markup=return_keyboard())
    await NewRawMeatBatchForm.set_tags_number.set()


@dp.message_handler(content_types=["photo"], state=NewRawMeatBatchForm.set_photo_pallet)
async def set_photo_pallet_handler(message: Message, state: FSMContext):
    object_name = await save_file_from_telegram(
        file_id=message.photo[-1].file_id, dir_name="raw_meat_batch", file_type=".jpeg"
    )
    await state.update_data(photo_pallet=object_name)

    await message.answer("Введите необходимое количество бирок", reply_markup=return_keyboard())
    await NewRawMeatBatchForm.set_tags_number.set()


@dp.message_handler(state=NewRawMeatBatchForm.set_photo_temperature)
async def set_photo_pallet_content_type_error_handler(message: Message, state: FSMContext):
    await message.answer("Необходимо отправить фотографию", reply_markup=skip_keyboard())


@dp.message_handler(lambda message: message.text.isdigit(), state=NewRawMeatBatchForm.set_tags_number)
async def set_tags_number_handler(message: Message, state: FSMContext):
    await state.update_data(tags_number=int(message.text))
    state_data = await state.get_data()
    if state_data.get("raw_meat_batch_id"):
        raw_meat_batch = RawMeatBatch.objects.get(id=state_data.get("raw_meat_batch_id"))
        raw_meat_batch = RawMeatBatch.objects.filter(raw_meat_batch).update(
            photo_ref_truck=state_data.get("photo_ref_truck"),
            photo_body_temperature_truck=state_data.get("photo_body_temperature_truck"),
            body_temperature_truck=state_data.get("body_temperature_truck"),
            photo_ypd=state_data.get("photo_ypd"),
            organization_vet=state_data.get("organization_vet"),
            manufacturer=state_data.get("manufacturer"),
            number_ttn=state_data.get("number_ttn"),
            photo_tn=state_data.get("photo_tn"),
            photo_vet=state_data.get("photo_vet"),
            link_vet=state_data.get("link_vet"),
            weight_vet=state_data.get("weight_vet"),
            organization=state_data.get("organization"),
            buh_accounting=state_data.get("buh_accounting"),
            condition=state_data.get("condition"),
            weight=state_data.get("weight"),
            photo_temperature=state_data.get("photo_temperature"),
            temperature=state_data.get("temperature"),
            photo_pallet=state_data.get("photo_pallet"),
            tags_number=state_data.get("tags_number"),
            document_number_vet=state_data.get("document_number_vet"),
            document_date_vet=state_data["document_date_vet"] if state_data.get("document_date_vet") else None,
            manufacture_date_vet=state_data["manufacture_date"] if state_data.get("manufacture_date") else None,
            expiration_date_vet=state_data["expiration_date_vet"] if state_data.get("document_date_vet") else None,
        )
    else:
        raw_meat_batch = await RawMeatBatch.objects.acreate(
            company_id=state_data.get("company_id"),
            photo_ref_truck=state_data.get("photo_ref_truck"),
            photo_body_temperature_truck=state_data.get("photo_body_temperature_truck"),
            body_temperature_truck=state_data.get("body_temperature_truck"),
            raw_material_id=state_data.get("raw_material_id"),
            ttn_type_id=state_data.get("ttn_type_id"),
            organization_vet=state_data.get("organization_vet"),
            manufacturer=state_data.get("manufacturer"),
            photo_ypd=state_data.get("photo_ypd"),
            number_ttn=state_data.get("number_ttn"),
            photo_tn=state_data.get("photo_tn"),
            photo_vet=state_data.get("photo_vet"),
            link_vet=state_data.get("link_vet"),
            weight_vet=state_data.get("weight_vet"),
            organization=state_data.get("organization"),
            buh_accounting=state_data.get("buh_accounting"),
            condition=state_data.get("condition"),
            weight=state_data.get("weight"),
            weight_receipt=state_data.get("weight"),
            photo_temperature=state_data.get("photo_temperature"),
            temperature=state_data.get("temperature"),
            photo_pallet=state_data.get("photo_pallet"),
            tags_number=state_data.get("tags_number"),
            document_number_vet=state_data.get("document_number_vet"),
            document_date_vet=state_data["document_date_vet"] if state_data.get("document_date_vet") else None,
            manufacture_date_vet=state_data["manufacture_date"] if state_data.get("manufacture_date") else None,
            expiration_date_vet=state_data["expiration_date_vet"] if state_data.get("document_date_vet") else None,
        )

    if state_data.get("photos_ttn"):
        for photo_ttn in state_data["photos_ttn"]:
            await RawMeatBatchFile.objects.acreate(
                raw_meat_batch_id=raw_meat_batch.pk, name="photo_ttn", file_location=photo_ttn
            )

    if state_data.get("photos_vet"):
        for photo_vet in state_data["photos_vet"]:
            await RawMeatBatchFile.objects.acreate(
                raw_meat_batch_id=raw_meat_batch.pk, name="photo_vet", file_location=photo_vet
            )

    new_raw_meat_batch_form_success = f"""
    Партия успешно зарегистрирована.
    ID: {raw_meat_batch.production_id}
    ОСГ: {state_data.get('min_osg') if state_data.get('min_osg') else ""}"""

    await message.answer(new_raw_meat_batch_form_success, reply_markup=main_menu_keyboard(message.from_user.id))
    await state.finish()

    for user in Users.objects.filter(position__code_name__in=["storekeeper", "labaratory"]):
        new_raw_meat_batch_storekeeper_notify = f"""    Зарегистрирована новая партия.
    Сырье: {raw_meat_batch.raw_material.name}
    ID: {raw_meat_batch.production_id}
    ОСГ: {state_data.get('min_osg') if state_data.get('min_osg') else ""},
    Масса: {state_data.get('weight')} кг
    Количество бирок: {raw_meat_batch.tags_number}"""

        await bot.send_message(
            chat_id=user.telegram_id,
            text=new_raw_meat_batch_storekeeper_notify,
            reply_markup=None if user.position.code_name == "labaratory" else None,
        )


@dp.message_handler(state=NewRawMeatBatchForm.set_tags_number)
async def set_tags_number_digit_error_handler(message: Message, state: FSMContext):
    await message.answer(text="Количество бирок должно быть числом", reply_markup=skip_keyboard())
