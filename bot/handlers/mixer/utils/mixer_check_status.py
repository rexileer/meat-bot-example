from Web.CRM.models import MincedMeatBatchMix, Users, Status


def check_last_status_mixer(minced_meat_mix, line_type):
    mix = MincedMeatBatchMix.objects.get(pk=minced_meat_mix).minced_meat_batch_id

    status_list_mixer = MincedMeatBatchMix.objects.filter(
        statuses__status__codename="mixer_mix_meat",
        minced_meat_batch_id=mix,
        line_type=line_type,
    )
    status_list_mixer_finish = MincedMeatBatchMix.objects.filter(
        statuses__status__codename="mixer_mix_meat_end",
        minced_meat_batch_id=mix,
        line_type=line_type,
    )
    status_list_mixer_load_to_pallet = MincedMeatBatchMix.objects.filter(
        statuses__status__codename="pallet_is_set",
        minced_meat_batch_id=mix,
        line_type=line_type,
    )
    return (
        status_list_mixer.count() == status_list_mixer_finish.count()
        or status_list_mixer.count() == status_list_mixer_load_to_pallet.count()
    )


async def check_work_mixer():
    mixes = sorted(
        MincedMeatBatchMix.objects.filter(
            statuses__status__codename="press_operator_mix_meat_end"
        )
        .all()
        .exclude(statuses__status__codename="mixer_mix_meat_end")
        .exclude(statuses__status__codename="pallet_is_set")
        .exclude(statuses__status__codename="mixer_mix_meat"),
        key=lambda m: m.get_mix_number(),
    )
    for res in mixes:
        if check_last_status_mixer(res.pk, res.line_type):
            await res.statuses.aget_or_create(
                status_id=Status.objects.get(codename="mixer_mix_meat").pk, notify=True
            )
            from bot.handlers.mixer.mixer import mixer_notify_mix_meat

            return await mixer_notify_mix_meat(res.pk, Users.list_roles)
