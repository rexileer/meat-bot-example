from django.core.management.base import BaseCommand
from django.db import transaction

from Web.CRM.models import (
    RawMeatBatch,
    RawMeatBatchStatus,
    RawMeatBatchFile,
    MeatBlank,
    MeatBlankRawMeatBatch,
    MeatBlankStatus,
    MincedMeatBatch,
    MincedMeatBatchRawMeatBatch,
    MincedMeatBatchMeatBlank,
    MincedMeatBatchSecondMeatBlank,
    MincedMeatBatchMixConsumptionRaw,
    MincedMeatBatchMixConsumptionMeatBlank,
    MincedMeatBatchMixConsumptionSecondMeatBlank,
    MincedMeatBatchMix,
    MincedMeatBatchStatus,
    TotalMincedMeatBatchStatus,
    MincedMeatBatchFile,
    SecondMincedMeat,
    SecondMincedMeatStatus,
    SecondMincedMeatBatchFile,
    ShockerMixLoad,
    Shipment,
    ShipmentPallet,
    Tilers,
    BufferPalletMars,
    WarehouseResponses,
)


class Command(BaseCommand):
    help = (
        "Удаляет операционные данные (сырьё, заготовки, партии/замесы фарша, статусы, загрузки в шокер, отгрузки)\n"
        "Сохраняет справочники и настройки (Users, Position, Status, Recipe, MincedStandards, ShockerCamera, RawMaterial, TTNType, RawMaterialParams, Company).\n"
        "По умолчанию выводит только план удаления. Используйте --apply для выполнения."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Применить удаление (по умолчанию только dry-run)",
        )
        parser.add_argument(
            "--keep-shipments",
            action="store_true",
            help="Не удалять Shipment и ShipmentPallet",
        )

    def handle(self, *args, **options):
        apply_changes: bool = options["apply"]
        keep_shipments: bool = options["keep_shipments"]

        self.stdout.write(self.style.SUCCESS("=== СБРОС ОПЕРАЦИОННЫХ ДАННЫХ (dry-run по умолчанию) ==="))

        # Считаем объёмы к удалению
        counts = {
            "consumption_raw": MincedMeatBatchMixConsumptionRaw.objects.count(),
            "consumption_blank": MincedMeatBatchMixConsumptionMeatBlank.objects.count(),
            "consumption_second": MincedMeatBatchMixConsumptionSecondMeatBlank.objects.count(),
            "mix_files": MincedMeatBatchFile.objects.count(),
            "second_files": SecondMincedMeatBatchFile.objects.count(),
            "mix_status": MincedMeatBatchStatus.objects.count(),
            "mix_total_status": TotalMincedMeatBatchStatus.objects.count(),
            "mix": MincedMeatBatchMix.objects.count(),
            "minced_links_raw": MincedMeatBatchRawMeatBatch.objects.count(),
            "minced_links_blank": MincedMeatBatchMeatBlank.objects.count(),
            "minced_links_second": MincedMeatBatchSecondMeatBlank.objects.count(),
            "minced": MincedMeatBatch.objects.count(),
            "second": SecondMincedMeat.objects.count(),
            "second_status": SecondMincedMeatStatus.objects.count(),
            "meat_blank_status": MeatBlankStatus.objects.count(),
            "meat_blank_links": MeatBlankRawMeatBatch.objects.count(),
            "meat_blank": MeatBlank.objects.count(),
            "raw_files": RawMeatBatchFile.objects.count(),
            "raw_status": RawMeatBatchStatus.objects.count(),
            "raw": RawMeatBatch.objects.count(),
            "shocker_loads": ShockerMixLoad.objects.count(),
            "buffer_pallet_mars": BufferPalletMars.objects.count(),
            "warehouse_responses": WarehouseResponses.objects.count(),
            "tilers_linked": Tilers.objects.filter(minced_meat_batch_mix__isnull=False).count(),
            "shipments": Shipment.objects.count(),
            "shipment_pallets": ShipmentPallet.objects.count(),
        }

        # Выводим план
        for key, value in counts.items():
            self.stdout.write(f"{key}: {value}")

        if not apply_changes:
            self.stdout.write(self.style.WARNING("Dry-run завершён. Запустите с --apply для удаления."))
            return

        # Удаление в правильном порядке, в транзакции
        with transaction.atomic():
            # Освободить плиточники (ресурсы), не удаляя их
            tilers_to_reset = Tilers.objects.select_for_update().all()
            tilers_to_reset.update(minced_meat_batch_mix=None, status=True)

            # Отгрузки (опционально)
            if not keep_shipments:
                ShipmentPallet.objects.all().delete()
                Shipment.objects.all().delete()

            # Шокерные загрузки
            ShockerMixLoad.objects.all().delete()

            # Consumption
            MincedMeatBatchMixConsumptionRaw.objects.all().delete()
            MincedMeatBatchMixConsumptionMeatBlank.objects.all().delete()
            MincedMeatBatchMixConsumptionSecondMeatBlank.objects.all().delete()

            # Файлы
            MincedMeatBatchFile.objects.all().delete()
            SecondMincedMeatBatchFile.objects.all().delete()

            # Статусы и сущности фарша
            MincedMeatBatchStatus.objects.all().delete()
            TotalMincedMeatBatchStatus.objects.all().delete()
            MincedMeatBatchMix.objects.all().delete()
            MincedMeatBatchRawMeatBatch.objects.all().delete()
            MincedMeatBatchMeatBlank.objects.all().delete()
            MincedMeatBatchSecondMeatBlank.objects.all().delete()
            SecondMincedMeatStatus.objects.all().delete()
            SecondMincedMeat.objects.all().delete()
            MincedMeatBatch.objects.all().delete()

            # Заготовки и связи
            MeatBlankStatus.objects.all().delete()
            MeatBlankRawMeatBatch.objects.all().delete()
            MeatBlank.objects.all().delete()

            # Сырьё, статусы и файлы
            RawMeatBatchStatus.objects.all().delete()
            RawMeatBatchFile.objects.all().delete()
            RawMeatBatch.objects.all().delete()

            # Прочее оперативное
            BufferPalletMars.objects.all().delete()
            WarehouseResponses.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("Удаление завершено. Операционные данные очищены."))


