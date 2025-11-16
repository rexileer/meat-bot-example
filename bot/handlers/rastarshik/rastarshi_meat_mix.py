from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from bot.keyboards.rastarshik import rastarshik_minced_meat_keyboard
from bot.loader import bot, dp
from bot.utils.text_info import generate_recipe_for_minced_meat_mix_bobo
from Web.CRM.dataclasses import RolesModel
from Web.CRM.models import MincedMeatBatchMix, Status


async def rastarshik_notify_mix_meat(mix_id, roles: RolesModel):
    mix = MincedMeatBatchMix.objects.get(pk=mix_id)

    await mix.statuses.aget_or_create(status=Status.objects.get(codename="rastarshik_unload_mix_meat"))
    remake = mix.remake

    text = f"""
<b>Линия - {mix.minced_meat_batch.line_type if mix.minced_meat_batch.line_type in [1,2]
            else f"Обе {mix.line_type}"}</b>
Был создан новый замес - <b>{mix.minced_meat_batch.recipe.name} замес - {mix.production_id.split("/")[::-1][0]}</b>

ID фарша: {mix.minced_meat_batch.production_id}
Рецепт: {mix.minced_meat_batch.recipe.name}

Используемое сырье и заготовки:
{await generate_recipe_for_minced_meat_mix_bobo(mix.minced_meat_batch.pk)}

"""
    if remake:
        text = "<b>Рецепт фарша был изменен. Данный замес отправлен повторно</b>\n\n" + text
    if mix.line_type in [1] or mix.line_type is None:
        await bot.send_message(
            chat_id=roles.rastarshchik.telegram_id, text=text, reply_markup=rastarshik_minced_meat_keyboard(mix_id)
        )
    elif mix.line_type in [2] and mix.minced_meat_batch.type == "ММО":
        await bot.send_message(
            chat_id=roles.rastarshchik_line_2.telegram_id,
            text=text,
            reply_markup=rastarshik_minced_meat_keyboard(mix_id),
        )
    elif mix.line_type in [2] and mix.minced_meat_batch.type == "МКО":
        await bot.send_message(
            chat_id=roles.mko_manager_line_2.telegram_id,
            text=text,
            reply_markup=rastarshik_minced_meat_keyboard(mix_id),
        )


@dp.callback_query_handler(Text(startswith="a_minc_mix-"))
async def accept_minced_meat_batch_mix(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    mix_id = int(call.data.split("-")[1])
    mix = MincedMeatBatchMix.objects.get(pk=mix_id)
    await mix.statuses.acreate(status=Status.objects.get(codename="rastarshik_unload_mix_meat_end"))
