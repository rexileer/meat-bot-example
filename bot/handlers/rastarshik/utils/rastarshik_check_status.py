from itertools import chain

# from django.db.models import Q

from Web.CRM.models import (
    MeatBlankStatus,
    Users,
    MeatBlank,
    MincedMeatBatchMix,
    Status,
    MincedMeatBatchStatus,
)
from bot.handlers.rastarshik.rastarshi_meat_mix import rastarshik_notify_mix_meat


def check_prev_status_meat_blank():
    meat_blanks_rastarshik = MeatBlankStatus.objects.filter(
        status__codename="rastarshik_unload_meat_blank"
    ).all()
    meat_blanks_finished_rastarshik = MeatBlankStatus.objects.filter(
        status__codename="rastarshik_unload_meat_blank_end"
    ).all()
    return meat_blanks_rastarshik.count() == meat_blanks_finished_rastarshik.count()


def check_prev_status_mix(minced_meat_mix):
    mix: MincedMeatBatchMix = MincedMeatBatchMix.objects.get(pk=minced_meat_mix)
    mix_rastarshik = MincedMeatBatchStatus.objects.filter(
        status__codename="rastarshik_unload_mix_meat",
        minced_meat_batch_mix__minced_meat_batch_id=mix.minced_meat_batch.pk,
    ).all()
    mix_finished_rastarshik = MincedMeatBatchStatus.objects.filter(
        status__codename="rastarshik_unload_mix_meat_end",  # mixer_tiller_mix_meat_end
        minced_meat_batch_mix__minced_meat_batch_id=mix.minced_meat_batch.pk,
    ).all()
    return mix_rastarshik.count() == mix_finished_rastarshik.count()


def check_status_mix_mko_schoker(minced_meat_mix, mix):
    if not (mix.line_type in [2] and mix.minced_meat_batch.type == "МКО"):
        return True
    mix: MincedMeatBatchMix = MincedMeatBatchMix.objects.get(pk=minced_meat_mix)
    mix_rastarshik = MincedMeatBatchStatus.objects.filter(
        status__codename="rastarshik_unload_mix_meat",
        minced_meat_batch_mix__minced_meat_batch_id=mix.minced_meat_batch.pk,
    ).all()
    mix_finished_rastarshik = MincedMeatBatchStatus.objects.filter(
        status__codename="mixer_mix_meat_end",
        minced_meat_batch_mix__minced_meat_batch_id=mix.minced_meat_batch.pk,
    ).all()
    return mix_rastarshik.count() == mix_finished_rastarshik.count()


def check_available_line(minced_meat_mix, type_m):
    mix: MincedMeatBatchMix = MincedMeatBatchMix.objects.get(pk=minced_meat_mix)
    for i in range(1, 3):
        # HACK Для марса на второй линии оставляем по старому
        if mix.minced_meat_batch.is_shocker:
            print(">>>>>>>>>>>>>>МЫ ВШОКЕРЕ>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            line_mixes_not_finished = MincedMeatBatchStatus.objects.filter(
                status__codename="rastarshik_unload_mix_meat",
                minced_meat_batch_mix__minced_meat_batch_id=mix.minced_meat_batch.pk,
                minced_meat_batch_mix__line_type=i,
            )
            if type_m == "МКО" and mix.minced_meat_batch.line_type != 2:
                codename = "unloaded_to_packer_end"
            elif type_m == "МКО" and mix.minced_meat_batch.line_type == 2:
                codename = "pallet_is_set"
            else:
                codename = "rastarshik_unload_mix_meat_end"  # Растарка замеса завершена
            line_mixes_finished = MincedMeatBatchStatus.objects.filter(
                status__codename=codename,  # unloaded_to_packer_end
                minced_meat_batch_mix__minced_meat_batch_id=mix.minced_meat_batch.pk,
                minced_meat_batch_mix__line_type=i,
            )
            if line_mixes_not_finished.count() == line_mixes_finished.count():
                print(
                    "line_mixes_not_finished.count()", line_mixes_not_finished.count()
                )
                print("line_mixes_finished.count()", line_mixes_finished.count())
                if mix.minced_meat_batch.line_type == 10:
                    return i
                elif mix.minced_meat_batch.line_type == i:
                    return i
        # HACK Для остальных смотрим по выходу с растарки
        else:
            print(">>>>>>>>>>>>>>МЫ В ОСТАЛЬНЫХ>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            line_mixes_not_finished = MincedMeatBatchStatus.objects.filter(
                status__codename="rastarshik_unload_mix_meat",  # Растарка замеса
                minced_meat_batch_mix__minced_meat_batch_id=mix.minced_meat_batch.pk,
                minced_meat_batch_mix__line_type=i,
            )
            line_mixes_finished = MincedMeatBatchStatus.objects.filter(
                status__codename="rastarshik_unload_mix_meat_end",  # Растарка замеса завершена
                minced_meat_batch_mix__minced_meat_batch_id=mix.minced_meat_batch.pk,
                minced_meat_batch_mix__line_type=i,
            )
            print("line_mixes_not_finished.count()", line_mixes_not_finished.count())
            print("line_mixes_finished.count()", line_mixes_finished.count())
            if line_mixes_not_finished.count() <= line_mixes_finished.count():
                if mix.minced_meat_batch.line_type == 10:
                    return i
                elif mix.minced_meat_batch.line_type == i:
                    return i

    return False


async def check_work_rastarshik():
    meat_blanks = (
        MeatBlank.objects.filter(statuses__status__codename="storekeeper_outputed")
        .all()
        .exclude(statuses__status__codename="rastarshik_unload_meat_blank_end")
    )

    mixes = sorted(
        MincedMeatBatchMix.objects.filter(statuses__isnull=True).all(),
        key=lambda m: m.get_mix_number(),
    )
    result_list = list(chain(mixes, meat_blanks))
    for res in result_list:
        if isinstance(res, MeatBlank):
            if check_prev_status_meat_blank():
                res.statuses.get_or_create(
                    status_id=Status.objects.get(
                        codename="rastarshik_unload_meat_blank"
                    ).pk,
                    notify=True,
                )
                from bot.handlers.storekeeper.storekeeper_actual_meat_blank_weight import (
                    rastarshik_notify_meat_blank,
                )

                return await rastarshik_notify_meat_blank(res.pk, Users.list_roles)

        elif isinstance(res, MincedMeatBatchMix):
            if not res.minced_meat_batch:
                continue
            line = check_available_line(res.pk, res.minced_meat_batch.type)
            if check_prev_status_mix(res.pk) or line:
                if res.minced_meat_batch.line_type == 10:
                    if line:
                        res.line_type = line
                        res.save()
                        return await rastarshik_notify_mix_meat(
                            res.pk, Users.list_roles
                        )
                else:
                    if line:
                        res.line_type = line
                        res.save()
                        await res.statuses.aget_or_create(
                            status_id=Status.objects.get(
                                codename="rastarshik_unload_mix_meat"
                            ).pk,
                            notify=True,
                        )

                        return await rastarshik_notify_mix_meat(
                            res.pk, Users.list_roles
                        )
