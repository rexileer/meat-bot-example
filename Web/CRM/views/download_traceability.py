from datetime import timedelta

from django.http import HttpResponse

from bot.utils.datatables import generate_traceability_datatable


def download_traceability(request, date):

    end = date + timedelta(seconds=86399)

    datatable = generate_traceability_datatable(start=date, end=end)
    response = HttpResponse(
        datatable.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="Прослеживаемость за текущий день.xlsx"'.encode("utf-8")
    return response
