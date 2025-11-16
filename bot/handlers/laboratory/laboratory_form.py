import re
from datetime import datetime

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, InputFile, Message, ReplyKeyboardRemove

from bot.handlers.laboratory.utils.documents import generate_acceptance_certificate
from bot.keyboards.laboratory.laboratory_form import (
    laboratory_antibiotic_keyboard,
    laboratory_compiles_keyboard,
    laboratory_confirm_keyboard,
    laboratory_set_broth_quality_keyboard,
    set_organoleptic_photos_keyboard,
    set_responsible_keyboard,
)
from bot.keyboards.main_menu import main_menu_keyboard
from bot.keyboards.shared import return_keyboard, set_separator_mode_keyboard, set_separator_name_keyboard
from bot.loader import dp
from bot.states.laboratory_form import LaboratoryAnalyzeForm
from bot.utils.file_storage import save_file_from_bytesio, save_file_from_telegram
from data.constants import DATE_FORMAT, FLOAT_REGEX
from Web.CRM.constans.responsible import RESPONSIBLE
from Web.CRM.constans.separator import SEPARATOR_MODES, SEPARATORS
from Web.CRM.models import RawMeatBatch, RawMeatBatchStatus, Status


@dp.callback_query_handler(Text(equals="analyze_raw_meat_batch"))
async def analyze_raw_meat_batch(call: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    batch_id = state_data.get("batch_id", None)
    if batch_id:
        await state.update_data(raw_meat_batch_id=batch_id)
        await call.message.answer("Выберите ответственного", reply_markup=set_responsible_keyboard())
        await LaboratoryAnalyzeForm.set_responsible.set()
    else:
        await call.message.answer(
            "Партии с указанным ID не существует или уже проанализирован!", reply_markup=return_keyboard()
        )
    await call.message.delete()


@dp.message_handler(state=LaboratoryAnalyzeForm.set_responsible)
async def set_meat_batch_responsible_handler(message: Message, state: FSMContext):
    if message.text in RESPONSIBLE:
        await state.update_data(responsible=message.text)

        await message.answer("Укажите дату ТТН (пример: 20.01.2022)", reply_markup=return_keyboard())
        await LaboratoryAnalyzeForm.set_ttn_date.set()
    else:
        await message.answer("Такого ответственного нет в списке")


@dp.message_handler(content_types=["text"], state=LaboratoryAnalyzeForm.set_ttn_date)
async def set_ttn_date_handler(message: Message, state: FSMContext):
    try:
        datetime.strptime(message.text, DATE_FORMAT)
    except ValueError:
        return await message.answer("Дата ТТН введена в неверном формате, попробуйте снова (пример: 20.01.2022)")

    await state.update_data(ttn_date=message.text)

    await message.answer("Выберите сепаратор", reply_markup=set_separator_name_keyboard())
    await LaboratoryAnalyzeForm.set_separator_name.set()


@dp.message_handler(state=LaboratoryAnalyzeForm.set_separator_name)
async def set_separator_name_handler(message: Message, state: FSMContext):
    if message.text in SEPARATORS:
        await state.update_data(separator_name=message.text)
        await message.answer(text="Выберите режим сепаратора", reply_markup=set_separator_mode_keyboard())
        await LaboratoryAnalyzeForm.set_separator_mode.set()
    else:
        await message.answer(
            text="Выбранный вариант не существует. Попробуйте еще раз", reply_markup=set_separator_name_keyboard()
        )


@dp.message_handler(state=LaboratoryAnalyzeForm.set_separator_mode)
async def set_separator_mode_handler(message: Message, state: FSMContext):
    if message.text in SEPARATOR_MODES:
        await state.update_data(separator_mode=message.text)
        await message.answer("Введите массовую долю жиров", reply_markup=return_keyboard())
        await LaboratoryAnalyzeForm.set_fat_proportion.set()
    else:
        await message.answer(
            text="Выбранный вариант не существует. Попробуйте еще раз", reply_markup=set_separator_mode_keyboard()
        )


@dp.message_handler(
    lambda message: re.match(FLOAT_REGEX, message.text), state=LaboratoryAnalyzeForm.set_fat_proportion
)
async def set_fat_proportion_handler(message: Message, state: FSMContext):
    await state.update_data(fat_proportion=message.text)

    await message.answer("Введите массовую долю белков", reply_markup=return_keyboard())
    await LaboratoryAnalyzeForm.set_protein_proportion.set()


@dp.message_handler(state=LaboratoryAnalyzeForm.set_fat_proportion)
async def set_fat_proportion_decimal_error_handler(message: Message, state: FSMContext):
    await message.answer("Массовая доля жиров должна быть числом", reply_markup=return_keyboard())


@dp.message_handler(
    lambda message: re.match(FLOAT_REGEX, message.text), state=LaboratoryAnalyzeForm.set_protein_proportion
)
async def set_protein_proportion_handler(message: Message, state: FSMContext):
    await state.update_data(protein_proportion=message.text)

    await message.answer("Введите массовую долю влаги", reply_markup=return_keyboard())
    await LaboratoryAnalyzeForm.set_moisture_proportion.set()


@dp.message_handler(state=LaboratoryAnalyzeForm.set_protein_proportion)
async def set_protein_proportion_decimal_error_handler(message: Message, state: FSMContext):
    await message.answer("Массовая доля белков должна быть числом", reply_markup=return_keyboard())


@dp.message_handler(
    lambda message: re.match(FLOAT_REGEX, message.text), state=LaboratoryAnalyzeForm.set_moisture_proportion
)
async def set_moisture_proportion_handler(message: Message, state: FSMContext):
    await state.update_data(moisture_proportion=message.text)

    await message.answer(
        "Внешний вид соответствует требования согласно НТД?", reply_markup=laboratory_compiles_keyboard()
    )
    await LaboratoryAnalyzeForm.set_appearance.set()


@dp.message_handler(state=LaboratoryAnalyzeForm.set_moisture_proportion)
async def set_moisture_proportion_decimal_error_handler(message: Message, state: FSMContext):
    await message.answer("Массовая доля влаги должна быть числом", reply_markup=return_keyboard())


@dp.message_handler(text=["Соответствует", "Не соответствует"], state=LaboratoryAnalyzeForm.set_appearance)
async def set_appearance_handler(message: Message, state: FSMContext):
    if message.text == "Соответствует":
        await state.update_data(appearance=True)
    elif message.text == "Не соответствует":
        await state.update_data(appearance=False)

    await message.answer("Запах соответствует требования согласно НТД?", reply_markup=laboratory_compiles_keyboard())
    await LaboratoryAnalyzeForm.set_smell.set()


@dp.message_handler(text=["Соответствует", "Не соответствует"], state=LaboratoryAnalyzeForm.set_smell)
async def set_smell_handler(message: Message, state: FSMContext):
    if message.text == "Соответствует":
        await state.update_data(smell=True)
    elif message.text == "Не соответствует":
        await state.update_data(smell=False)

    await message.answer("Цвет соответствует требования согласно НТД?", reply_markup=laboratory_compiles_keyboard())
    await LaboratoryAnalyzeForm.set_color.set()


@dp.message_handler(text=["Соответствует", "Не соответствует"], state=LaboratoryAnalyzeForm.set_color)
async def set_color_handler(message: Message, state: FSMContext):
    if message.text == "Соответствует":
        await state.update_data(color=True)
    elif message.text == "Не соответствует":
        await state.update_data(color=False)

    await message.answer(
        "Качество бульона при варке соответствует требования согласно НТД?",
        reply_markup=laboratory_set_broth_quality_keyboard(),
    )
    await LaboratoryAnalyzeForm.set_broth_quality.set()


@dp.message_handler(text=["Мутный", "Светлый", "Полупрозрачный"], state=LaboratoryAnalyzeForm.set_broth_quality)
async def set_broth_quality_handler(message: Message, state: FSMContext):
    await state.update_data(broth_quality=message.text)

    await message.answer(
        "Аромат бульона соответствует требованиям согласно НТД?", reply_markup=laboratory_compiles_keyboard()
    )
    await LaboratoryAnalyzeForm.set_broth_flavor.set()


@dp.message_handler(text=["Соответствует", "Не соответствует"], state=LaboratoryAnalyzeForm.set_broth_flavor)
async def set_broth_flavor_handler(message: Message, state: FSMContext):
    if message.text == "Соответствует":
        await state.update_data(broth_flavor=True, organoleptic_photos=[])
    elif message.text == "Не соответствует":
        await state.update_data(broth_flavor=False, organoleptic_photos=[])

    await message.answer(
        "Результаты исследования - Бетта-лактамы (мг/кг)", reply_markup=laboratory_antibiotic_keyboard()
    )
    await LaboratoryAnalyzeForm.set_betta_lactams.set()


@dp.message_handler(text=["Положительное", "Отрицательное"], state=LaboratoryAnalyzeForm.set_betta_lactams)
async def set_betta_lactams_handler(message: Message, state: FSMContext):
    await state.update_data(betta_lactams=message.text)

    await message.answer(
        "Результаты исследования - Хлорамфениколы (мг/кг)", reply_markup=laboratory_antibiotic_keyboard()
    )
    await LaboratoryAnalyzeForm.set_chloramphenicols.set()


@dp.message_handler(state=LaboratoryAnalyzeForm.set_betta_lactams)
async def set_betta_lactams_error_handler(message: Message, state: FSMContext):
    await message.answer("Результат исследования введен некорректно", reply_markup=laboratory_antibiotic_keyboard())


@dp.message_handler(text=["Положительное", "Отрицательное"], state=LaboratoryAnalyzeForm.set_chloramphenicols)
async def set_chloramphenicols_handler(message: Message, state: FSMContext):
    await state.update_data(chloramphenicols=message.text)

    await message.answer(
        "Результаты исследования - Тетрациклины (мг/кг)", reply_markup=laboratory_antibiotic_keyboard()
    )
    await LaboratoryAnalyzeForm.set_tetracyclines.set()


@dp.message_handler(state=LaboratoryAnalyzeForm.set_chloramphenicols)
async def set_chloramphenicols_decimal_error_handler(message: Message, state: FSMContext):
    await message.answer("Результат исследования введен некорректно", reply_markup=laboratory_antibiotic_keyboard())


@dp.message_handler(text=["Положительное", "Отрицательное"], state=LaboratoryAnalyzeForm.set_tetracyclines)
async def set_tetracyclines_handler(message: Message, state: FSMContext):
    await state.update_data(tetracyclines=message.text)

    await message.answer(
        "Результаты исследования - Стрептомицины (мг/кг)", reply_markup=laboratory_antibiotic_keyboard()
    )
    await LaboratoryAnalyzeForm.set_streptomycins.set()


@dp.message_handler(state=LaboratoryAnalyzeForm.set_tetracyclines)
async def set_tetracyclines_decimal_error_handler(message: Message, state: FSMContext):
    await message.answer("Результат исследования введен некорректно", reply_markup=laboratory_antibiotic_keyboard())


@dp.message_handler(text=["Положительное", "Отрицательное"], state=LaboratoryAnalyzeForm.set_streptomycins)
async def set_streptomycins_handler(message: Message, state: FSMContext):
    await state.update_data(streptomycins=message.text)

    await message.answer("Пришлите фотографии органолептических данных", reply_markup=return_keyboard())
    await LaboratoryAnalyzeForm.set_organoleptic_photos.set()


@dp.message_handler(state=LaboratoryAnalyzeForm.set_streptomycins)
async def set_streptomycins_decimal_error_handler(message: Message, state: FSMContext):
    await message.answer("Результат исследования введен некорректно", reply_markup=laboratory_antibiotic_keyboard())


@dp.message_handler(content_types=["photo"], state=LaboratoryAnalyzeForm.set_organoleptic_photos)
async def set_organoleptic_photos_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()

    object_name = await save_file_from_telegram(
        file_id=message.photo[-1].file_id, dir_name="raw_meat_batch", file_type=".jpeg"
    )

    await state.update_data(organoleptic_photos=state_data["organoleptic_photos"] + [object_name])

    await message.answer(
        "Фотография с органолептическими данными сохранена. Вы можете прислать еще несколько штук или продолжить",
        reply_markup=set_organoleptic_photos_keyboard(),
    )


@dp.message_handler(text="Продолжить", state=LaboratoryAnalyzeForm.set_organoleptic_photos)
async def set_organoleptic_photos_next_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()

    additional_data = {
        "fat_proportion": state_data["fat_proportion"],
        "protein_proportion": state_data["protein_proportion"],
        "moisture_proportion": state_data["moisture_proportion"],
        "appearance": state_data["appearance"],
        "smell": state_data["smell"],
        "color": state_data["color"],
        "broth_quality": state_data["broth_quality"],
        "broth_flavor": state_data["broth_flavor"],
        "betta_lactams": state_data["betta_lactams"],
        "chloramphenicols": state_data["chloramphenicols"],
        "tetracyclines": state_data["tetracyclines"],
        "streptomycins": state_data["streptomycins"],
        "organoleptic_photos": state_data["organoleptic_photos"],
        "separator_mode": state_data["separator_mode"],
        "separator_name": state_data["separator_name"],
        "responsible": state_data["responsible"],
    }

    lab_analyze_status = Status.objects.get(codename="laboratory_analyze")

    raw_meat_batch_status = RawMeatBatchStatus.objects.filter(
        raw_meat_batch_id=state_data["raw_meat_batch_id"], status=lab_analyze_status
    ).first()

    if raw_meat_batch_status:
        raw_meat_batch_status.additional_data = additional_data
        raw_meat_batch_status.save()
    else:
        raw_meat_batch_status = await RawMeatBatchStatus.objects.acreate(
            raw_meat_batch_id=state_data["raw_meat_batch_id"],
            status=lab_analyze_status,
            additional_data=additional_data,
        )

    RawMeatBatch.objects.filter(pk=raw_meat_batch_status.raw_meat_batch.pk).update(
        date_ttn=datetime.strptime(state_data["ttn_date"], DATE_FORMAT)
    )

    raw_meat_batch = RawMeatBatch.objects.get(pk=state_data["raw_meat_batch_id"])
    document = generate_acceptance_certificate(raw_meat_batch=raw_meat_batch)

    await message.answer_document(
        caption="Проверьте акт входного контроля",
        document=InputFile(path_or_bytesio=document, filename="Акт входного контроля.docx"),
        reply_markup=laboratory_confirm_keyboard(),
    )
    await LaboratoryAnalyzeForm.confirm.set()


@dp.message_handler(text="Подтвердить", state=LaboratoryAnalyzeForm.confirm)
async def confirm_yes_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()

    raw_meat_batch = RawMeatBatch.objects.get(pk=state_data["raw_meat_batch_id"])
    document = generate_acceptance_certificate(raw_meat_batch=raw_meat_batch)

    object_name = save_file_from_bytesio(bytesio=document, dir_name="raw_meat_batch", file_type=".docx")

    RawMeatBatch.objects.filter(pk=state_data["raw_meat_batch_id"]).update(acceptance_certificate=object_name)

    await message.answer(
        "Данные по ФХП анализу успешно сохранены", reply_markup=main_menu_keyboard(message.from_user.id)
    )
    await state.finish()


@dp.message_handler(text="Отправить измененный", state=LaboratoryAnalyzeForm.confirm)
async def confirm_no_handler(message: Message, state: FSMContext):
    await message.answer("Отправьте акт входного контроля в формате .docx", reply_markup=ReplyKeyboardRemove())
    await LaboratoryAnalyzeForm.set_acceptance_certificate.set()


@dp.message_handler(
    lambda message: message.document.file_name.lower().endswith(".docx"),
    content_types=["document"],
    state=LaboratoryAnalyzeForm.set_acceptance_certificate,
)
async def set_acceptance_certificate_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()

    object_name = await save_file_from_telegram(
        file_id=message.document.file_id, dir_name="raw_meat_batch", file_type=".docx"
    )

    RawMeatBatch.objects.filter(pk=state_data["raw_meat_batch_id"]).update(acceptance_certificate=object_name)

    await message.answer(
        "Данные по ФХП анализу успешно сохранены", reply_markup=main_menu_keyboard(message.from_user.id)
    )
    await state.finish()


@dp.message_handler(
    content_types=["text", "video", "photo", "document", "video_note"],
    state=LaboratoryAnalyzeForm.set_acceptance_certificate,
)
async def set_acceptance_certificate_content_type_error_handler(message: Message, state: FSMContext):
    await message.answer("Неверный тип файла. Отправьте .docx")


@dp.message_handler(content_types=["text"], state=LaboratoryAnalyzeForm.set_organoleptic_photos)
async def set_organoleptic_photos_content_type_error_handler(message: Message, state: FSMContext):
    await message.answer("Необходимо прислать фотографии")
