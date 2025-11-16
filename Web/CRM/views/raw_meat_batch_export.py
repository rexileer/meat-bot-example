from django.http import HttpResponse

from bot.utils.datatables import generate_raw_meat_used


def process_export_raw_meat_batch(request):
    datatable = generate_raw_meat_used()

    response = HttpResponse(
        datatable.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="Отчёт.xlsx"'.encode("utf-8")
    return response
