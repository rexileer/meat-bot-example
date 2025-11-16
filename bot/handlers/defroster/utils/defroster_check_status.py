from Web.CRM.models import MeatBlankStatus, Users, MeatBlank


async def check_last_status_defroster__meat_blank():
    status_list_storekeeper = MeatBlankStatus.objects.filter(status__codename="loaded_to_defroster")
    status_list_storekeeper_outputed = status_list_storekeeper.filter(status__codename="unloaded_from_defroster")
    return status_list_storekeeper.count() == status_list_storekeeper_outputed.count()


async def check_new_meat_blanks_defroster():
    from bot.handlers.storekeeper.storekeeper_actual_meat_blank_weight import rastarshik_notify_meat_blank

    status_list_storekeeper: MeatBlank = MeatBlank.objects.filter(
        statuses__status__codename="rastarshik_unload_meat_blank_end"
    ).all()
    for blank in status_list_storekeeper:
        next = blank.statuses.filter(status__codename="loaded_to_defroster").first()
        if not next:
            return await rastarshik_notify_meat_blank(blank.pk, Users.list_roles)
