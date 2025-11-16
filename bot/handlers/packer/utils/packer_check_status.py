from django.utils.timezone import now

from bot.handlers.packer.packer import packer_notify_mix_meat_unload_shocker
from Web.CRM.models import MincedMeatBatchMix, ShockerMixLoad, Status, Users


def check_last_status_packer():
    status_list_packer = MincedMeatBatchMix.objects.filter(statuses__status__codename="unloaded_to_packer")
    status_list_packer_finish = MincedMeatBatchMix.objects.filter(statuses__status__codename="unloaded_to_packer_end")

    status_list_packer_shocker = MincedMeatBatchMix.objects.filter(statuses__status__codename="unload_shocker")
    status_list_packer_finish_shocker = MincedMeatBatchMix.objects.filter(
        statuses__status__codename="unload_shocker_finish"
    )
    return (
        status_list_packer.count() == status_list_packer_finish.count()
        and status_list_packer_shocker.count() == status_list_packer_finish_shocker.count()
    )


async def check_work_packer():
    mixes = (
        MincedMeatBatchMix.objects.filter(statuses__status__codename__in=["mixer_mix_meat_end"])
        .all()
        .exclude(statuses__status__codename="unloaded_to_packer_end")
        .exclude(statuses__status__codename="unload_shocker_finish")
    )
    for res in mixes:
        if (
            now() - res.statuses.filter(status__codename="mixer_mix_meat_end").first().created_at
        ).total_seconds() >= 10:  # 300
            if check_last_status_packer():
                if res.statuses.filter(status__codename="mixer_tiller_mix_meat_end").first():
                    # if res.minced_meat_batch.
                    await res.statuses.aget_or_create(
                        status_id=Status.objects.get(codename="unloaded_to_packer").pk, notify=True
                    )
                    from bot.handlers.packer.packer import packer_notify_mix_meat

                    return await packer_notify_mix_meat(res.pk, Users.list_roles)
                elif res.statuses.filter(status__codename="to_shocker_finish").first():
                    await res.statuses.aget_or_create(
                        status_id=Status.objects.get(codename="unload_shocker").pk, notify=True
                    )
                    from bot.handlers.packer.packer import packer_notify_mix_meat

                    return await packer_notify_mix_meat_unload_shocker(res.pk, Users.list_roles)

    second_minced_meats = ShockerMixLoad.objects.filter(
        status_unload=False, second_minced_meat__isnull=False, minced_meat_batch_mix_id__isnull=True
    ).exclude(second_minced_meat__statuses__status__codename="unload_shocker")

    for second_meat in second_minced_meats:
        if (now() - second_meat.created_at).total_seconds() >= 300:
            if check_last_status_packer():
                await second_meat.second_minced_meat.statuses.aget_or_create(
                    status_id=Status.objects.get(codename="unload_shocker").pk
                )
                from bot.handlers.packer.packer import packer_notify_second_mix_meat

                return await packer_notify_second_mix_meat(second_meat.pk, Users.list_roles)
