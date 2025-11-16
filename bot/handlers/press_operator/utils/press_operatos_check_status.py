from django.db.models import Q

from Web.CRM.models import MincedMeatBatchMix, Users, Status, MincedMeatBatchStatus
from bot.handlers.press_operator.press_operator_handler import press_operator_notify_mix_meat


def check_last_status_press_operator__mix(minced_meat_mix):
    mix = MincedMeatBatchMix.objects.get(pk=minced_meat_mix).minced_meat_batch_id

    status_list_press_operator = MincedMeatBatchMix.objects.filter(
        statuses__status__codename="press_operator_mix_meat", minced_meat_batch_id=mix
    )
    status_list_press_operator_finish = MincedMeatBatchMix.objects.filter(
        statuses__status__codename="press_operator_mix_meat_end", minced_meat_batch_id=mix
    )
    return status_list_press_operator.count() == status_list_press_operator_finish.count()


def check_available_line(minced_meat_mix):
    mix: MincedMeatBatchMix = MincedMeatBatchMix.objects.get(pk=minced_meat_mix)
    for i in range(1, 3):
        line_mixes_not_finished = MincedMeatBatchStatus.objects.filter(
            Q(status__codename="press_operator_mix_meat")
            & Q(minced_meat_batch_mix__minced_meat_batch_id=mix.minced_meat_batch.pk)
            & Q(minced_meat_batch_mix__line_type=i)
        )
        line_mixes_finished = MincedMeatBatchStatus.objects.filter(
            Q(status__codename="press_operator_mix_meat_end")
            & Q(minced_meat_batch_mix__minced_meat_batch_id=mix.minced_meat_batch.pk)
            & Q(minced_meat_batch_mix__line_type=i)
        )
        if line_mixes_not_finished.count() == line_mixes_finished.count():
            if mix.minced_meat_batch.line_type == 10:
                return i
            elif mix.minced_meat_batch.line_type != 10 and mix.minced_meat_batch.line_type == i:
                return i
    return False


async def check_work_press_operator():
    mixes = (
        MincedMeatBatchMix.objects.filter(statuses__status__codename="rastarshik_unload_mix_meat_end")
        .all()
        .exclude(statuses__status__codename="press_operator_mix_meat_end")
        .exclude(statuses__status__codename="press_operator_mix_meat")
        .order_by("created_at")
    )
    for res in mixes:
        line = check_available_line(res.pk)
        if check_last_status_press_operator__mix(res.pk) or line:
            if res.minced_meat_batch.line_type == 10:
                if line:
                    await res.statuses.aget_or_create(
                        status_id=Status.objects.get(codename="press_operator_mix_meat").pk, notify=True
                    )
                    res.line_type = line
                    res.save()
                    return await press_operator_notify_mix_meat(res.pk, Users.list_roles)
            else:
                res.line_type = line
                res.save()
                await res.statuses.aget_or_create(
                    status_id=Status.objects.get(codename="press_operator_mix_meat").pk, notify=True
                )
                return await press_operator_notify_mix_meat(res.pk, Users.list_roles)
