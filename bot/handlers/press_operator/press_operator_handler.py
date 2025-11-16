from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from Web.CRM.dataclasses import RolesModel
from Web.CRM.models import MincedMeatBatchMix, Status
from bot.handlers.mixer.utils.mixer_check_status import check_last_status_mixer
from bot.keyboards.press_operator.press_operator_kbs import press_operator_minced_meat_keyboard
from bot.loader import bot, dp
from bot.utils.text_info import generate_recipe_for_minced_meat_mix_bobo


async def press_operator_notify_mix_meat(mix_id, roles: RolesModel, alarm=""):
    mix = MincedMeatBatchMix.objects.get(pk=mix_id)

    text = f"""
<b>Линия - {mix.minced_meat_batch.line_type if mix.minced_meat_batch.line_type in [1,2]
            else f"Обе {mix.line_type}"}</b>

{alarm}Был создан новый замес - <b>{mix.minced_meat_batch.recipe.name} замес -
 {mix.production_id.split("/")[::-1][0]}</b>



ID фарша: {mix.minced_meat_batch.production_id}
Рецепт: {mix.minced_meat_batch.recipe.name}

Используемое сырье и заготовки -
{await generate_recipe_for_minced_meat_mix_bobo(mix.minced_meat_batch.pk)}

"""
    if mix.minced_meat_batch.line_type in [1, 10]:
        await bot.send_message(
            chat_id=roles.press_operator_line_1.telegram_id,
            text=text,
            reply_markup=press_operator_minced_meat_keyboard(mix_id),
        )

    elif mix.minced_meat_batch.line_type in [2] and mix.minced_meat_batch.type == "ММО":
        await bot.send_message(
            chat_id=roles.press_operator_line_2.telegram_id,
            text=text,
            reply_markup=press_operator_minced_meat_keyboard(mix_id),
        )

    elif mix.line_type in [2] and mix.minced_meat_batch.type == "МКО":
        await bot.send_message(
            chat_id=roles.mko_manager_line_2.telegram_id,
            text=text,
            reply_markup=press_operator_minced_meat_keyboard(mix_id),
        )


@dp.callback_query_handler(Text(startswith="a_press_mix"))
async def accept_minced_meat_batch_mix(call: types.CallbackQuery, state: FSMContext, roles: RolesModel):
    try:
        await call.message.delete()
    except Exception:
        pass
    mix_id = int(call.data.split("-")[1])
    mix = MincedMeatBatchMix.objects.get(pk=mix_id)
    if not check_last_status_mixer(mix_id, mix.line_type):
        return await press_operator_notify_mix_meat(
            mix_id, roles, "Фаршесоставитель еще не закончил c прошлым замесом, ЖДИ!\n"
        )
    await mix.statuses.acreate(status=Status.objects.get(codename="press_operator_mix_meat_end"))
