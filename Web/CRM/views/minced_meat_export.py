from django.http import HttpResponse


def process_export_minced_meat(request, date):
    from bot.utils.datatables import generate_meat_batch_datatable

    datatable = generate_meat_batch_datatable(date)

    response = HttpResponse(
        datatable.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="Отчёт.xlsx"'.encode("utf-8")
    return response
