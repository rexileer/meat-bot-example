import asyncio
import datetime
import traceback

from loguru import logger

from data.constants import DATE_FORMAT
from bot.keyboards.shared import skip_keyboard, return_keyboard
from bot.keyboards.vet_doc_slider import set_slider_page
from bot.states.new_raw_meat_batch_form import NewRawMeatBatchForm
from bot.utils.api.vet import fetch_vet
from bot.utils.api.vetis_api import VET_DOC_TEMPLATE_URL


async def extract_data(message, data, state):
    responses = list()
    for uuid in data:
        vet_url = f"{VET_DOC_TEMPLATE_URL}{uuid}"

        try:
            response = await fetch_vet(vet_url)
        except Exception:
            logger.error(traceback.format_exc())
            logger.info(vet_url)
            return await message.answer(
                "Ошибка при выгрузке данных. Проверьте правильность ссылки и повторите попытку",
                reply_markup=skip_keyboard(),
            )
        if isinstance(response.document_date, datetime.datetime):
            response.document_date = response.document_date.strftime(DATE_FORMAT)
        responses.append(response)

    await state.update_data(slider_data=[response.json() for response in responses])
    await state.update_data(chosen_responses=list())


async def get_data_from_mercury(state, message):
    running = 60
    notify = False
    while running:
        data = await state.get_data()
        if data.get("skip_getting_docs"):
            break
        if data.get("vet_docs_list").__class__ == list:
            await extract_data(message, data.get("vet_docs_list"), state)
            msg, keyboard = await set_slider_page(0, state)
            await message.answer(text=msg, reply_markup=keyboard)
            await NewRawMeatBatchForm.set_choice_vet_doc.set()
            break
        elif data.get("vet_docs_list") == 0:
            await message.answer("Заявка на получение ЭВСД отклонена")
            await message.answer("Введите поставщика", reply_markup=return_keyboard())
            await NewRawMeatBatchForm.set_organization.set()
            break
        elif data.get("vet_docs_list") == 1:
            await message.answer("ЭВСД не найдены")
            await message.answer("Введите поставщика", reply_markup=return_keyboard())
            await NewRawMeatBatchForm.set_organization.set()
            break
        else:
            if not notify:
                notify = True
                await message.answer(
                    "Данные о ЭВСД пока не получены, пожалуйста подождите", reply_markup=skip_keyboard()
                )
        await asyncio.sleep(5)
        running -= 1

    if not running:
        await message.answer("Не удалось получить ЭВСД")
        await message.answer("Введите поставщика", reply_markup=return_keyboard())
        await NewRawMeatBatchForm.set_organization.set()
