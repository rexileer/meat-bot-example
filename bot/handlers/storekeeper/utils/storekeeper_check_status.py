from itertools import chain

from Web.CRM.models import MeatBlank, MeatBlankStatus, MincedMeatBatchMix, SecondMincedMeat, Status, Users


def check_prev_status():
    meat_blanks = MeatBlankStatus.objects.filter(status__codename="storekeeper_output").all()
    meat_blanks_finished = MeatBlankStatus.objects.filter(status__codename="storekeeper_outputed").all()
    mix_palleting = MincedMeatBatchMix.objects.filter(statuses__status__codename="palletizing").all()
    mix_palleting_finished = MincedMeatBatchMix.objects.filter(statuses__status__codename="palletizing_end").all()
    print("meat_blanks", meat_blanks.count())
    print("meat_blanks_finished", meat_blanks_finished.count())
    print("mix_palleting", mix_palleting.count())
    print("mix_palleting_finished", mix_palleting_finished.count())
    return (
        meat_blanks_finished.count() == meat_blanks.count() and mix_palleting.count() == mix_palleting_finished.count()
    )


async def check_work_storekeeper():
    from bot.handlers.storekeeper.storekeeper_mix_finish import storekeeper_notify_mix_meat

    new_meat_blanks = MeatBlank.objects.filter(statuses__status__codename__isnull=True).all().order_by("created_at")
    new_mixes = (
        MincedMeatBatchMix.objects.filter(
            statuses__status__codename__in=["unloaded_to_packer_end", "unload_shocker_finish"]
        )
        .all()
        .order_by("created_at")
    )
    second_minced_meats = SecondMincedMeat.objects.filter(statuses__status__codename="unload_shocker_finish").order_by(
        "created_at"
    )
    result_list = list(chain(new_mixes, new_meat_blanks, second_minced_meats))
    # print("new_meat_blanks ", new_meat_blanks)
    # print("new_mixes ", new_mixes)
    # print("second_minced_meats ", second_minced_meats)
    # print("result_list ", result_list)
    for res in result_list:
        if isinstance(res, MeatBlank):
            if check_prev_status():
                res.statuses.get_or_create(status_id=Status.objects.get(codename="storekeeper_output").pk, notify=True)
                from bot.handlers.meat_blank.new_meat_blank import storkeepe_notify_meat_blank

                return await storkeepe_notify_meat_blank(res.pk, Users.list_roles)

        elif isinstance(res, MincedMeatBatchMix):
            if res.statuses.filter(status__codename__in=["unloaded_to_packer_end", "unload_shocker_finish"]).first():
                if (
                    not res.statuses.filter(status__codename="palletizing").first()
                    and res.statuses.filter(status__codename="mixer_tiller_mix_meat_end").first()
                    and check_prev_status()
                ):
                    res.statuses.get_or_create(status_id=Status.objects.get(codename="palletizing").pk, notify=False)
                    await storekeeper_notify_mix_meat(res.pk, Users.list_roles)

        # elif isinstance(res, SecondMincedMeat):
        #     if res.statuses.filter(status__codename__in=['unload_shocker_finish']).first():
        #         if not res.statuses.filter(status__codename='palletizing').first() and check_prev_status():
        #             await res.statuses.aget_or_create(status_id=Status.objects.get(codename="palletizing").pk)
        #             await storekeeper_notify_mix_meat_second(res.pk, Users.list_roles)
