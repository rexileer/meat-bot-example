import datetime
import logging
from io import BytesIO

from django.utils.timezone import now
from openpyxl import Workbook
from openpyxl.writer.excel import save_virtual_workbook

from Web.CRM.models import SecondMincedMeat
from bot.utils.excel import beautify_columns


async def generate_second_minced_meat_info() -> BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.append(["ID вторфарша", "дата занесения", "вес"])
    start = now().replace(hour=7, minute=0, second=0, microsecond=0)
    end = start + datetime.timedelta(days=1)
    meats = SecondMincedMeat.objects.filter(created_at__gt=start, created_at__lt=end)
    logging.info(meats)
    all_all_weight = 9

    list_names = {0: "Вторфарш", 1: "МКО1", 2: "МКО2", 3: "МКО3"}

    for type_id in range(0, 4):
        all_weight = 0
        if meats.filter(type=type_id):
            ws.append(("", list_names[type_id], ""))
            for meat in meats.filter(type=type_id):
                ws.append((meat.production_id, f"{meat.created_at:%d.%m.%Y %H:%M}", meat.weight))
                all_weight += meat.weight
            ws.append(("Итог:", "", all_weight))
        ws.append(("",))
        all_all_weight += all_weight
    ws.append(("Суммарный итог:", "", all_all_weight))
    beautify_columns(ws)

    return BytesIO(save_virtual_workbook(wb))
