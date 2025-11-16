from typing import List
from django.db import models

from aiogram.dispatcher import FSMContext

from Web.CRM.models import (
    RawMeatBatch,
    MeatBlank,
    MeatBlankRawMeatBatch,
    MincedMeatBatch,
    MincedMeatBatchMeatBlank,
    MincedMeatBatchRawMeatBatch,
    MincedMeatBatchSecondMeatBlank,
    MincedMeatBatchMixConsumptionRaw,
    MincedMeatBatchMixConsumptionMeatBlank,
)
from bot.handlers.raw_meat_batch.utils.raw_meat_batch import get_bzv


def raw_meat_batch_for_lab(raw_meat_batch: RawMeatBatch):
    return f"""    Сырье: {raw_meat_batch.raw_material.name}
    ID: {raw_meat_batch.production_id}
    Масса: {raw_meat_batch.weight} кг"""


async def meat_blank_list_for_new(state: FSMContext) -> str:
    final_weight = 0
    b, z, v = 0, 0, 0
    state_data = await state.get_data()
    raw_meat_batch_preview = ""
    for i, raw_meat_batch_state in enumerate(state_data["raw_meat_batches"]):
        weight = float(raw_meat_batch_state["weight"])
        final_weight += weight
        raw_meat_batch = await RawMeatBatch.objects.filter(pk=raw_meat_batch_state["id"]).afirst()
        bzv = await get_bzv(raw_meat_batch)
        b += (bzv[0] / 100) * weight
        z += (bzv[1] / 100) * weight
        v += (bzv[2] / 100) * weight
        raw_meat_batch_preview += (
            f"{i + 1}. {raw_meat_batch.production_id} ({raw_meat_batch.raw_material.name}) - "
            f"{raw_meat_batch_state['weight']} кг\n"
        )
    p = final_weight / 100
    await state.update_data(protein=round(b / p, 2), fat=round(z / p, 2), moisture=round(v / p, 2))
    raw_meat_batch_preview += f"\nБ - {round(b / p, 2)}\n" f"Ж - {round(z / p, 2)}\n" f"В - {round(v / p, 2)}\n"
    return raw_meat_batch_preview


async def raw_meat_blank_text_final(meat_blank_id) -> str:
    raw_meat_batches: List[MeatBlankRawMeatBatch] = MeatBlankRawMeatBatch.objects.filter(
        meat_blank_id=meat_blank_id
    ).all()
    raw_meat_batch_preview = ""
    for i, raw_meat_batch in enumerate(raw_meat_batches, 1):
        raw_meat_batch_preview += (
            f"{i}. {raw_meat_batch.raw_meat_batch.production_id} "
            f"({raw_meat_batch.raw_meat_batch.raw_material.name}) - "
            f"{raw_meat_batch.weight} кг\n"
        )

    raw_meat_batch_preview += (
        f"\nБ - {raw_meat_batches[0].meat_blank.protein}\n"
        f"Ж - {raw_meat_batches[0].meat_blank.fat}\n"
        f"В - {raw_meat_batches[0].meat_blank.moisture}\n"
    )
    return raw_meat_batch_preview


async def get_meat_blank_text_before_storekeepr(meat_blank_id):
    raw_materials_info = await raw_meat_blank_text_final(meat_blank_id)
    meat_blank: MeatBlank = await MeatBlank.objects.aget(pk=meat_blank_id)
    status = await meat_blank.statuses.filter(status__codename="storekeeper_outputed").afirst()
    text = "\n".join(
        [
            "Была создана новая заготовка",
            "ID заготовки: {meat_blank.production_id}",
            "Используемое сырье:",
            f"{raw_materials_info}",
            f'\nСуммарный вес {status.additional_data["all_weight"]}',
        ]
    )
    return text


async def generate_recipe_second_meat_and_meat_blanks_text(state: FSMContext) -> str:
    final_weight = 0
    b, z, v = 0, 0, 0
    preview_text = ""
    state_data = await state.get_data()
    meat_blanks_state = state_data.get("meat_blanks", None)
    second_minced_meat_weight = state_data.get("second_minced_meat_weight", None)
    if meat_blanks_state:
        preview_text += "\nЗаготовки\n"
        for i, meat_blank_state in enumerate(meat_blanks_state, 1):
            weight = float(meat_blank_state["weight"])
            final_weight += weight
            meat_blank = MeatBlank.objects.get(pk=meat_blank_state["id"])
            b += (float(meat_blank.protein) / 100) * weight
            z += (float(meat_blank.fat) / 100) * weight
            v += (float(meat_blank.moisture) / 100) * weight
            preview_text += f"{i}. {meat_blank.production_id} - {meat_blank_state['weight']} кг\n"

    if second_minced_meat_weight:
        preview_text += f"\nВторварш\nИспользовано {second_minced_meat_weight} кг"
        final_weight += second_minced_meat_weight

    p = final_weight / 100
    await state.update_data(protein=round(b / p, 2), fat=round(z / p, 2), moisture=round(v / p, 2))
    preview_text += f"\nБ - {round(b / p, 2)}\n" f"Ж - {round(z / p, 2)}\n" f"В - {round(v / p, 2)}\n"

    return preview_text


async def generate_recipe_raw_meat_batches_and_meat_blanks_text(state: FSMContext) -> str:
    final_weight = 0
    b, z, v = 0, 0, 0
    preview_text = ""
    state_data = await state.get_data()
    meat_blanks_state = state_data["meat_blanks"]
    raw_meat_batches_state = state_data["raw_meat_batches"]
    if meat_blanks_state:
        preview_text += "\nЗаготовки\n"
        for i, meat_blank_state in enumerate(meat_blanks_state, 1):
            weight = float(meat_blank_state["weight"])
            final_weight += weight
            meat_blank = MeatBlank.objects.get(pk=meat_blank_state["id"])
            b += (float(meat_blank.protein) / 100) * weight
            z += (float(meat_blank.fat) / 100) * weight
            v += (float(meat_blank.moisture) / 100) * weight
            preview_text += f"{i}. {meat_blank.production_id} - {meat_blank_state['weight']} кг\n"

    if raw_meat_batches_state:
        preview_text += "\nСырьё\n"
        for i, raw_meat_batch_state in enumerate(raw_meat_batches_state, 1):
            weight = float(raw_meat_batch_state["weight"])
            final_weight += weight
            raw_meat_batch = RawMeatBatch.objects.get(pk=raw_meat_batch_state["id"])
            bzv = await get_bzv(raw_meat_batch)
            b += (bzv[0] / 100) * weight
            z += (bzv[1] / 100) * weight
            v += (bzv[2] / 100) * weight
            preview_text += (
                f"{i}. {raw_meat_batch.production_id} ({raw_meat_batch.raw_material.name}) - "
                f"{raw_meat_batch_state['weight']} кг\n"
            )

    p = final_weight / 100
    await state.update_data(protein=round(b / p, 2), fat=round(z / p, 2), moisture=round(v / p, 2))
    preview_text += f"\nБ - {round(b / p, 2)}\n" f"Ж - {round(z / p, 2)}\n" f"В - {round(v / p, 2)}\n"

    return preview_text


async def generate_recipe_for_minced_meat_mix(minced_meat_id, pfm_show=True) -> str:
    preview_text = ""
    minced_meat = MincedMeatBatch.objects.filter(pk=minced_meat_id).first()
    minced_meat_blanks = MincedMeatBatchMeatBlank.objects.filter(minced_meat_batch_id=minced_meat.pk).all()
    minced_meat_raw_blanks = MincedMeatBatchRawMeatBatch.objects.filter(minced_meat_batch_id=minced_meat.pk).all()
    minced_meat_second_meat_blanks = MincedMeatBatchSecondMeatBlank.objects.filter(
        minced_meat_batch_id=minced_meat.pk
    ).all()

    if minced_meat_blanks:
        preview_text += "Заготовки\n"
        for i, meat_blank in enumerate(minced_meat_blanks, 1):
            preview_text += f"{i}. {meat_blank.meat_blank.production_id} - {round(float(meat_blank.weight), 1)} кг\n"

    if not minced_meat_second_meat_blanks:
        if minced_meat_raw_blanks:
            preview_text += "\nСырьё\n"
            for i, raw_meat_batch in enumerate(minced_meat_raw_blanks, 1):
                preview_text += (
                    f"{i}. {raw_meat_batch.raw_meat_batch.production_id} "
                    f"({raw_meat_batch.raw_meat_batch.raw_material.name}) - "
                    f"{round(float(raw_meat_batch.weight), 1)} кг\n"
                )
    else:
        amount = 0
        for i, meat in enumerate(minced_meat_second_meat_blanks, 1):
            amount += round(float(meat.weight), 1)
        preview_text += f"\nВторфарш - {amount} кг\n"

    if pfm_show:
        preview_text += f"\nБ - {minced_meat.protein}\n" f"Ж - {minced_meat.fat}\n" f"В - {minced_meat.moisture}\n"
    return preview_text


async def generate_recipe_for_minced_meat_mix_bobo(minced_meat_id) -> str:
    preview_text = ""
    minced_meat = MincedMeatBatch.objects.filter(pk=minced_meat_id).first()
    minced_meat_blanks = MincedMeatBatchMeatBlank.objects.filter(minced_meat_batch_id=minced_meat.pk).all()
    minced_meat_raw_blanks = MincedMeatBatchRawMeatBatch.objects.filter(minced_meat_batch_id=minced_meat.pk).all()
    minced_meat_second_meat_blanks = MincedMeatBatchSecondMeatBlank.objects.filter(
        minced_meat_batch_id=minced_meat.pk
    ).all()

    # Определяем произведенные замесы по наличию зафиксированного списания
    produced_mix_ids_raw = set(
        MincedMeatBatchMixConsumptionRaw.objects.filter(
            minced_meat_batch_mix__minced_meat_batch=minced_meat
        ).values_list("minced_meat_batch_mix_id", flat=True)
    )
    produced_mix_ids_blank = set(
        MincedMeatBatchMixConsumptionMeatBlank.objects.filter(
            minced_meat_batch_mix__minced_meat_batch=minced_meat
        ).values_list("minced_meat_batch_mix_id", flat=True)
    )
    produced = len(produced_mix_ids_raw.union(produced_mix_ids_blank))
    total_mixes = minced_meat.number_mix or 0
    remaining_mixes = max(total_mixes - produced, 0)
    divisor = remaining_mixes if remaining_mixes > 0 else (total_mixes if total_mixes > 0 else 1)

    if minced_meat_blanks:
        preview_text += "Заготовки\n"
        for i, rel in enumerate(minced_meat_blanks, 1):
            consumed = (
                MincedMeatBatchMixConsumptionMeatBlank.objects.filter(
                    minced_meat_batch_mix__minced_meat_batch=minced_meat, meat_blank=rel.meat_blank
                ).aggregate(w_sum=models.Sum("weight"))
            )["w_sum"] or 0
            remaining = max(float(rel.weight) - float(consumed), 0.0)
            per_mix = round(remaining / divisor, 1)
            preview_text += f"{i}. {rel.meat_blank.production_id} - {per_mix} кг\n"

    if not minced_meat_second_meat_blanks:
        if minced_meat_raw_blanks:
            preview_text += "\nСырьё\n"
            for i, rel in enumerate(minced_meat_raw_blanks, 1):
                consumed = (
                    MincedMeatBatchMixConsumptionRaw.objects.filter(
                        minced_meat_batch_mix__minced_meat_batch=minced_meat, raw_meat_batch=rel.raw_meat_batch
                    ).aggregate(w_sum=models.Sum("weight"))
                )["w_sum"] or 0
                remaining = max(float(rel.weight) - float(consumed), 0.0)
                per_mix = round(remaining / divisor, 1)
                preview_text += f"{i}. {rel.raw_meat_batch.raw_material} - {per_mix} кг\n"
    else:
        amount = 0
        for i, meat in enumerate(minced_meat_second_meat_blanks, 1):
            amount += round(float(meat.weight), 1)
        per_mix = round(amount / divisor, 1)
        preview_text += f"\nВторфарш - {per_mix} кг\n"

    return preview_text
