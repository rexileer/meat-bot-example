from datetime import datetime, timedelta
from typing import Optional, Set

from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_minio_backend import MinioBackend

from Web.CRM.constans.positions import position_dict
from Web.CRM.dataclasses import RolesModel, from_dict


class CreatedModel(models.Model):
    """Абстрактная модель. Добавляет дату создания."""

    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата изменения")

    class Meta:
        abstract = True


class Recipe(CreatedModel):
    name = models.CharField(max_length=255, verbose_name="Название рецепта")

    def __str__(self):
        return self.name

    @staticmethod
    def get_by_date_range(start: datetime, end: datetime):
        recipes = Recipe.objects.filter(created_at__gt=start, created_at__lt=end).all()

        return recipes

    class Meta:
        managed = True
        verbose_name = "Рецепты"
        verbose_name_plural = "Рецепты"
        __tablename__ = "recipe"
        db_table = "recipe"


class MincedStandards(CreatedModel):
    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        related_name="RecipeName",
        verbose_name="Название рецепта",
    )

    protein_deviation_minus = models.FloatField(
        verbose_name="Отклонение белков -", default=0
    )
    protein = models.FloatField(verbose_name="Значение массовой доли белков")
    protein_deviation_plus = models.FloatField(
        verbose_name="Отклонение белков +", default=0
    )

    fats_deviation_minus = models.FloatField(
        verbose_name="Отклонение жиров -", default=0
    )
    fats = models.FloatField(verbose_name="Значение массовой доли жиров")
    fats_deviation_plus = models.FloatField(
        verbose_name="Отклонение жиров +", default=0
    )

    moisture_deviation_minus = models.FloatField(
        verbose_name="Отклонение влаги - ", default=0
    )
    moisture = models.FloatField(verbose_name="Значение массовой доли влаги")
    moisture_deviation_plus = models.FloatField(
        verbose_name="Отклонение влаги +", default=0
    )

    pitch_deviation_minus = models.FloatField(
        null=True, verbose_name="Отклонение смоле -", default=0, blank=True
    )
    pitch = models.FloatField(verbose_name="Отклонение по смоле", blank=True)
    pitch_deviation_plus = models.FloatField(
        verbose_name="Отклонение смоле +", default=0, blank=True
    )

    def get_deviation_protein(self):
        return (
            self.protein - self.protein_deviation_minus,
            self.protein + self.protein_deviation_plus,
        )

    def get_deviation_fats(self):
        return (
            self.fats - self.fats_deviation_minus,
            self.fats + self.fats_deviation_plus,
        )

    def get_deviation_moisture(self):
        return (
            self.moisture - self.moisture_deviation_minus,
            self.moisture + self.moisture_deviation_plus,
        )

    def get_deviation_pitch(self):
        return (
            self.pitch - self.pitch_deviation_minus,
            self.pitch + self.pitch_deviation_plus,
        )

    def __str__(self):
        return self.recipe.name

    class Meta:
        __tablename__ = "minced_standards"
        db_table = "minced_standards"
        verbose_name = "Эталонные значения фарша"
        verbose_name_plural = "Эталонные значения фарша"


class Status(CreatedModel):
    codename = models.CharField(max_length=254)
    name = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = "statuses"


class Position(CreatedModel):
    name = models.CharField(max_length=50, verbose_name="Должность", unique=True)
    code_name = models.CharField(
        max_length=50, verbose_name="кодовое название должности", default=None
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "Positions"
        verbose_name = "Должности"
        verbose_name_plural = "Должности"


class SecondMincedMeat(CreatedModel):
    type = models.SmallIntegerField()
    weight = models.FloatField(verbose_name="Вес", default=0)
    production_id = models.CharField(max_length=255, null=False, default="")
    additional_data = models.JSONField(verbose_name="Дополнительные данные", null=True)

    def save(self, *args, **kwargs):
        mko_sell = False
        if "Продажа" in str(self.production_id):
            mko_sell = True
        self.production_id = (
            f"{datetime.now():%d%m}/{SecondMincedMeat.objects.all().count() + 1}/"
            f"{'Вторфарш' if self.type == 0 else f'МКО{self.type}'}"
        )
        if mko_sell:
            self.production_id += " Продажа"
        super().save(*args, **kwargs)

    def get_available_weight(self):
        second_minced_meat_blank = MincedMeatBatchSecondMeatBlank.objects.filter(
            second_minced_meat=self
        )
        weight_minced_meat_blank = sum([i.weight for i in second_minced_meat_blank])
        return self.weight - weight_minced_meat_blank

    @staticmethod
    def get_available_second_minced_meat():
        second_minced_meat_blank = MincedMeatBatchSecondMeatBlank.objects.all()
        unvailable_ids = []
        for i in second_minced_meat_blank:
            if i.second_minced_meat.get_available_weight() <= 0:
                unvailable_ids.append(i.second_minced_meat.pk)
        return SecondMincedMeat.objects.filter(type=0).exclude(pk__in=unvailable_ids)

    @staticmethod
    def get_available_weight_second_minced_meat():
        second_minced_meats = SecondMincedMeat.get_available_second_minced_meat()
        return sum([i.get_available_weight() for i in second_minced_meats])

    @staticmethod
    def get_release_second_minced_meat():
        return SecondMincedMeat.objects.filter(type=0, weight__gt=0).all()

    def __str__(self):
        return f"Сырье {self.production_id}"

    class Meta:
        verbose_name = "Вторфарш"
        verbose_name_plural = "Вторфарш"
        db_table = "second_minced_meat"


class SecondMincedMeatStatus(CreatedModel):
    second_minced_meat = models.ForeignKey(
        SecondMincedMeat, on_delete=models.CASCADE, related_name="statuses"
    )

    status = models.ForeignKey(Status, on_delete=models.CASCADE)

    additional_data = models.JSONField(null=True)

    class Meta:
        managed = True
        db_table = "second_minced_meat_status"


class Company(models.Model):
    name = models.CharField(max_length=255)
    guid = models.CharField(max_length=1000)
    issuerid = models.CharField(max_length=1000)
    apikey = models.CharField(max_length=1000)
    api_login = models.CharField(max_length=255)
    api_pass = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        managed = True
        db_table = "company"
        verbose_name = "Компания"
        verbose_name_plural = "Компании"


class ShockerCamera(CreatedModel):
    shocker_id = models.IntegerField(
        null=False, verbose_name="Номер шокера", unique=True, primary_key=True
    )
    max_pallet_count = models.IntegerField(
        default=100, verbose_name="Максимальное кол-во паллетов в камере"
    )

    @staticmethod
    def get_available_shocker():
        shockers = ShockerCamera.objects.all()
        dict_shocker = {}
        for shocker in shockers:
            dict_shocker.update({shocker.shocker_id: shocker.max_pallet_count})

        loads_shocker = ShockerMixLoad.objects.filter(status_unload=False).all()
        for load in loads_shocker:
            dict_shocker.update({load.shocker_id: dict_shocker[load.shocker_id] - 1})
        return dict_shocker

    def __str__(self):
        return f"Шокер {self.shocker_id} ({self.max_pallet_count}/{self.get_available_shocker()[self.shocker_id]})"

    class Meta:
        verbose_name = "Настройка шокеров"
        verbose_name_plural = "Настройка шокеров"
        managed = True
        db_table = "shock_camera"


class RawMaterial(CreatedModel):
    type = models.CharField(max_length=255)
    name = models.CharField(max_length=255)

    custom = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        managed = True
        db_table = "raw_material"
        verbose_name = "виды сырья"
        verbose_name_plural = "виды сырья"


class TTNType(CreatedModel):
    type = models.CharField(
        max_length=255,
        verbose_name="Кодовое название",
        help_text="Должно быть на английском",
    )
    name = models.CharField(max_length=255, verbose_name="Название")
    custom = models.BooleanField(default=False, verbose_name="Добавлено через бота")

    def __str__(self):
        return self.name

    class Meta:
        managed = True
        db_table = "ttn_raw_material_type"
        verbose_name = "Номенклатуры сырья"
        verbose_name_plural = "Номенклатуры сырья"


class RawMaterialParams(CreatedModel):
    raw_material = models.ForeignKey(
        RawMaterial,
        on_delete=models.CASCADE,
        related_name="raw_material",
        verbose_name="Сырье",
    )
    defrost = models.FloatField(
        default=100, verbose_name="Значение дефростации (в процентах)"
    )
    second_minced_meat_exit = models.FloatField(
        default=100, verbose_name="Выход вторфаша (в процентах)"
    )

    def __str__(self):
        return f"Сырье {self.raw_material}"

    class Meta:
        verbose_name = "Параметры сырья"
        verbose_name_plural = "Параметры сырья"
        managed = True
        db_table = "material_parameters"


class RawMeatBatch(CreatedModel):
    choosing_meat_condition = (("frozen", "Замороженное"), ("chilled", "Охлажденное"))

    production_id = models.CharField(max_length=100, verbose_name="ID партии")

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, verbose_name="Компания"
    )

    photo_ref_truck = models.ImageField(
        storage=MinioBackend(bucket_name="backend-private"),
        upload_to="raw_meat_batch",
        null=True,
    )

    photo_body_temperature_truck = models.ImageField(
        storage=MinioBackend(bucket_name="backend-private"),
        upload_to="raw_meat_batch",
        null=True,
    )

    body_temperature_truck = models.CharField(
        max_length=255,
        verbose_name="температура в кузове в момент открытия машины",
        null=True,
    )
    condition = models.CharField(
        verbose_name="Кондиция", choices=choosing_meat_condition, max_length=255
    )
    raw_material = models.ForeignKey(
        RawMaterial, on_delete=models.CASCADE, verbose_name="тип сырья"
    )

    ttn_type = models.ForeignKey(
        TTNType,
        on_delete=models.CASCADE,
        null=True,
        verbose_name="Наименование номенклатуры",
    )

    photo_ypd = models.ImageField(
        storage=MinioBackend(bucket_name="backend-private"),
        upload_to="raw_meat_batch",
        null=True,
        verbose_name="Редактирование фото УПД",
    )
    photo_acceptance_certificate = models.ImageField(
        storage=MinioBackend(bucket_name="backend-private"),
        upload_to="raw_meat_batch",
        null=True,
    )
    acceptance_certificate = models.FileField(
        storage=MinioBackend(bucket_name="backend-private"),
        upload_to="raw_meat_batch",
        null=True,
    )
    photo_ttn = models.ImageField(
        storage=MinioBackend(bucket_name="backend-private"),
        upload_to="raw_meat_batch",
        null=True,
    )
    date_ttn = models.DateTimeField(null=True)

    number_ttn = models.CharField(
        max_length=255, verbose_name="номер ТТН", null=True, blank=True
    )

    link_vet = models.CharField(
        max_length=2500, verbose_name="Ссылка на ЭВСД", null=True, blank=True
    )

    photo_tn = models.ImageField(
        storage=MinioBackend(bucket_name="backend-private"),
        upload_to="raw_meat_batch",
        null=True,
    )
    photo_vet = models.ImageField(
        storage=MinioBackend(bucket_name="backend-private"),
        upload_to="raw_meat_batch",
        null=True,
    )
    document_number_vet = models.CharField(max_length=255, null=True)
    document_date_vet = models.CharField(max_length=255, null=True)
    manufacture_date_vet = models.CharField(
        max_length=255, verbose_name="дата производства", null=True
    )
    expiration_date_vet = models.CharField(max_length=255, null=True)
    weight_vet = models.FloatField(null=True)
    organization_vet = models.CharField(max_length=600, null=True)

    organization = models.CharField(max_length=600, verbose_name="поставщик", null=True)
    manufacturer = models.CharField(
        max_length=600, verbose_name="производитель", null=True
    )

    photo_temperature = models.ImageField(
        storage=MinioBackend(bucket_name="backend-private"),
        upload_to="raw_meat_batch",
        null=True,
    )
    temperature = models.CharField(max_length=255, null=True)
    photo_pallet = models.ImageField(
        storage=MinioBackend(bucket_name="backend-private"),
        upload_to="raw_meat_batch",
        null=True,
    )
    weight = models.FloatField(verbose_name="Оставшийся вес")
    weight_receipt = models.FloatField(verbose_name="Вес поступления", null=True)

    tags_number = models.IntegerField(verbose_name="Кол-во бирок")
    buh_accounting = models.CharField(
        max_length=255, null=True, verbose_name="Тип для бух.учета"
    )

    is_future_batch = models.BooleanField(default=False)

    @staticmethod
    def get_available_chilled():
        return set(
            RawMeatBatch.objects.filter(
                weight__gt=0, condition="chilled", is_future_batch=False
            ).all()
        )

    @staticmethod
    def generate_raw_meat_batch_year_number(raw_meat_batch):
        start_year = raw_meat_batch.created_at.replace(
            month=1, day=1, second=0, microsecond=0
        )
        end_year = raw_meat_batch.created_at.replace(
            month=12, day=31, second=0, microsecond=0
        )
        list_raws = RawMeatBatch.objects.filter(
            created_at__gt=start_year, created_at__lt=end_year
        ).all()
        for key, val in enumerate(list_raws, start=1):
            if val.pk == raw_meat_batch.pk:
                return key

    @staticmethod
    def get_by_date_range(start: datetime, end: datetime):
        raw_meat_batches = RawMeatBatch.objects.filter(
            created_at__gt=start, created_at__lt=end, weight__gt=0
        ).all()

        return raw_meat_batches

    @staticmethod
    def get_all_for_today():
        return RawMeatBatch.objects.all()

    @staticmethod
    def get_meat_blank_who_used_today(start=None, end=None):
        if not start and not end:
            start = datetime.utcnow().replace(hour=7, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        return MeatBlankRawMeatBatch.objects.filter(
            created_at__gt=start, created_at__lt=end
        ).all()

    @staticmethod
    def used_and_filtred_raw_meats_today(start=None, end=None):
        """
        Новая логика: считаем расход сырья сразу при создании фарша/заготовок,
        а не по мере потребления через consumption.
        
        Расход включает:
        1. Прямые списания сырья при создании фарша (MincedMeatBatchRawMeatBatch)
        2. Списания сырья при создании заготовок (MeatBlankRawMeatBatch)
        3. Списания через consumption (для совместимости)

        Возвращаем формат (raw_material_list, data) совместимый со старой функцией.
        """
        if not start and not end:
            start = datetime.utcnow().replace(hour=7, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)

        from collections import defaultdict

        # 1) Расход сырья при создании фарша в интервале
        used_by_raw_batch: dict[int, float] = defaultdict(float)
        
        # ИСПРАВЛЕНО: считаем расход ТОЛЬКО по замесам, принятым на склад ГП (palletizing_end)
        # Убрали подсчёт при создании партий фарша и заготовок — только через consumption после palletizing_end
        finished_qs = MincedMeatBatchStatus.objects.filter(
            status__codename="palletizing_end",
            created_at__gte=start,
            created_at__lte=end,
        )
        all_mix_ids = set(
            finished_qs.values_list("minced_meat_batch_mix_id", flat=True)
        )

        # Прямые списания сырья на замесы через consumption
        for row in (
            MincedMeatBatchMixConsumptionRaw.objects.filter(
                minced_meat_batch_mix_id__in=all_mix_ids
            )
            .values("raw_meat_batch_id")
            .annotate(w=Sum("weight"))
        ):
            used_by_raw_batch[row["raw_meat_batch_id"]] += float(row["w"] or 0)

        # Списания заготовок через consumption: разложить на сырьё по составу meat_blank
        for cons in MincedMeatBatchMixConsumptionMeatBlank.objects.filter(
            minced_meat_batch_mix_id__in=all_mix_ids
        ):
            components = MeatBlankRawMeatBatch.objects.filter(
                meat_blank=cons.meat_blank
            ).all()
            total_blank_weight = sum((c.weight for c in components)) or 0
            if total_blank_weight <= 0:
                continue
            for comp in components:
                share = (float(comp.weight) / float(total_blank_weight)) * float(
                    cons.weight
                )
                used_by_raw_batch[comp.raw_meat_batch_id] += share

        # 2) Приход сырья: партии, созданные в интервале
        arrived_by_raw_batch: dict[int, float] = {}
        arrived_batches = RawMeatBatch.objects.filter(
            created_at__gte=start, created_at__lte=end
        ).all()
        for batch in arrived_batches:
            arrived_by_raw_batch[batch.id] = float(batch.weight_receipt or 0)

        # 3) Готовим результат
        data: dict[str, dict] = {}
        raw_material_list: list[str] = []
        for raw_meat_batch in RawMeatBatch.objects.all().order_by("-condition"):
            key = f"{raw_meat_batch.raw_material.name}---{raw_meat_batch.company.name}---{raw_meat_batch.pk}"
            data[key] = {
                "cur_weight": raw_meat_batch.weight,
                "used_weight": used_by_raw_batch.get(raw_meat_batch.id, 0.0),
                "add_weight": arrived_by_raw_batch.get(raw_meat_batch.id, 0.0),
            }
            if raw_meat_batch.raw_material.name not in raw_material_list:
                raw_material_list.append(raw_meat_batch.raw_material.name)

        return raw_material_list, data

    @staticmethod
    def get_mixes_who_used_today(start=None, end=None):
        if not start and not end:
            start = datetime.utcnow().replace(hour=7, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        return MincedMeatBatchRawMeatBatch.objects.filter(
            created_at__gt=start, created_at__lt=end
        ).all()

    @staticmethod
    def generate_raw_meath_batch_production_id(
        start: Optional[datetime] = None, end: Optional[datetime] = None
    ) -> str:
        if not start:
            start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        if not end:
            end = start + timedelta(days=1)

        raw_meat_batch_count = RawMeatBatch.objects.filter(
            created_at__gt=start, created_at__lt=end
        ).count()

        # Отсчет начинаем с 3, так как {1, 2} - резервные id под кости
        passed = 2

        return f"{start.strftime('%d%m')}/{raw_meat_batch_count + passed + 1}"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.production_id = RawMeatBatch.generate_raw_meath_batch_production_id()
            self.weight_receipt = self.weight

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Партия {self.production_id}"

    class Meta:
        managed = True
        db_table = "raw_meat_batch"
        verbose_name = "сырье"
        verbose_name_plural = "сырье"


class RawMeatBatchStatus(CreatedModel):
    raw_meat_batch = models.ForeignKey(
        RawMeatBatch, on_delete=models.CASCADE, related_name="statuses"
    )
    status = models.ForeignKey(Status, on_delete=models.CASCADE)
    additional_data = models.JSONField(null=True)

    class Meta:
        managed = True
        db_table = "raw_meat_batch_status"


class RawMeatBatchFile(CreatedModel):
    raw_meat_batch = models.ForeignKey(
        RawMeatBatch, on_delete=models.CASCADE, related_name="files"
    )
    name = models.CharField(max_length=255)
    file_location = models.FileField(
        storage=MinioBackend(bucket_name="backend-private"),
        upload_to="raw_meat_batch",
        null=True,
    )

    class Meta:
        managed = True
        db_table = "raw_meat_batch_file"


class Users(CreatedModel):
    telegram_id = models.BigIntegerField(null=False, verbose_name="TGid планшета")
    name = models.CharField(
        max_length=50, verbose_name="Пользователь за которым закреплен планшет"
    )
    position = models.ForeignKey(
        "Position", on_delete=models.CASCADE, null=False, verbose_name="Должность"
    )

    @classmethod
    @property
    def list_roles(self) -> RolesModel:
        new_dict = {}
        for key, val in position_dict.items():
            tg_id = self.objects.filter(position__code_name=key).first()
            if tg_id:
                new_dict.update({key: tg_id})
        return from_dict(RolesModel, new_dict)

    def __str__(self):
        return f"{self.position} - {self.telegram_id} - {self.name}"

    class Meta:
        db_table = "Users"
        verbose_name = "Telegram аккаунты"
        verbose_name_plural = "Telegram аккаунты"


class MeatBlank(CreatedModel):
    production_id = models.CharField(max_length=255, verbose_name="ID заготовки")

    protein = models.FloatField(verbose_name="Белки", default=0)

    fat = models.FloatField(verbose_name="Жиры", default=0)

    moisture = models.FloatField(verbose_name="Влага", default=0)

    arrival_date = models.DateTimeField(verbose_name="Дата прихода в цех")

    type_meat_blank = models.IntegerField(verbose_name="Заготовка МКО")

    weight = models.FloatField(verbose_name="Вес заготовки", default=0)
    weight_receipt = models.FloatField(verbose_name="Вес заготовки", default=0)

    @staticmethod
    def get_available_chilled():
        return set(
            MeatBlank.objects.filter(statuses__status__codename="loaded_to_defroster")
            .filter(
                statuses__status__codename="unloaded_from_defroster",
                weight__gt=0,
                type_meat_blank=0,
            )
            .all()
        )

    @staticmethod
    def get_available_chilled_mko():
        return set(
            MeatBlank.objects.filter(
                statuses__status__codename="loaded_to_defroster",
                weight__gt=0,
                type_meat_blank=1,
            )
            .filter(statuses__status__codename="unloaded_from_defroster")
            .all()
        )

    @staticmethod
    def get_count_by_date(start: datetime, end: datetime):
        meat_blank = (
            MeatBlank.objects.filter(created_at__gt=start, created_at__lt=end)
            .all()
            .count()
        )
        return meat_blank

    @property
    def storage_status_date(self):
        status = (
            MeatBlankStatus.objects.filter(
                meat_blank=self.id, status__codename="storage"
            )
            .values("created_at")
            .first()
        )
        if status:
            return status["created_at"]
        else:
            return None

    @staticmethod
    def get_available_frozen(raw_material__name=None):
        if not raw_material__name:
            return RawMeatBatch.objects.filter(weight__gt=0, condition="frozen").all()
        else:
            return RawMeatBatch.objects.filter(
                weight__gt=0, condition="frozen", raw_material__name=raw_material__name
            ).all()

    def __str__(self):
        return f"Заготовка {self.production_id}"

    class Meta:
        managed = True
        db_table = "meat_blank"
        verbose_name = "заготовка"
        verbose_name_plural = "заготовки"


class MeatBlankRawMeatBatch(CreatedModel):
    meat_blank = models.ForeignKey(
        MeatBlank,
        on_delete=models.CASCADE,
        related_name="meat_blanks",
        verbose_name="Фарш",
    )
    raw_meat_batch = models.ForeignKey(
        RawMeatBatch,
        on_delete=models.CASCADE,
        related_name="raw_meat_batches",
        verbose_name="Партия",
    )

    weight = models.FloatField(verbose_name="Вес")

    class Meta:
        managed = True
        db_table = "meat_blank_raw_meat_batches"


class MeatBlankStatus(CreatedModel):
    meat_blank = models.ForeignKey(
        MeatBlank, on_delete=models.CASCADE, related_name="statuses"
    )
    status = models.ForeignKey(Status, on_delete=models.CASCADE)

    additional_data = models.JSONField(null=True)
    notify = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = "meat_blank_status"


class MincedMeatBatch(CreatedModel):
    production_id = models.CharField(max_length=255, verbose_name="ID заготовки")

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, verbose_name="рецепт")

    number_mix = models.IntegerField(verbose_name="предполагаемое количество замесов")

    protein = models.FloatField(verbose_name="Белки")

    fat = models.FloatField(verbose_name="Жиры")
    is_night = models.BooleanField(default=False, verbose_name="Ночная смена")
    line_type = models.SmallIntegerField(null=True)
    is_shocker = models.BooleanField(default=False, verbose_name="Проходит по шокеру?")
    type = models.CharField(max_length=255, null=True)

    moisture = models.FloatField(verbose_name="Влага")

    arrival_date = models.DateTimeField(verbose_name="Дата прихода в цех")

    @property
    def storage_status_date(self):
        status = (
            MincedMeatBatchStatus.objects.filter(
                minced_meat_batch_mix__minced_meat_batch=self.id,
                status__codename="storage",
            )
            .values("created_at")
            .first()
        )
        if status:
            return status["created_at"]
        else:
            return None

    @staticmethod
    def get_by_date_range(start: datetime, end: datetime):
        minced_meat_batch = MincedMeatBatch.objects.filter(
            created_at__gt=start, created_at__lt=end
        ).all()

        return minced_meat_batch

    @staticmethod
    def get_by_recipe(recipe_id: int):
        minced_meat_batch = MincedMeatBatch.objects.filter(recipe=recipe_id).first()
        if minced_meat_batch:
            return minced_meat_batch
        return None

    @staticmethod
    def get_by_recipe_all(recipe_id: int):
        minced_meat_batches = MincedMeatBatch.objects.filter(recipe=recipe_id).all()
        if minced_meat_batches:
            return minced_meat_batches
        return None

    def get_raw_meat_batches(self):
        raw_meat_batches = list()
        minced_meat_batch_raw_meat_batches = MincedMeatBatchRawMeatBatch.objects.filter(
            minced_meat_batch=self.id
        ).all()
        for minced_meat_batch_raw_meat_batch in minced_meat_batch_raw_meat_batches:
            raw_meat_batches.append(minced_meat_batch_raw_meat_batch.raw_meat_batch)
        if raw_meat_batches:
            return raw_meat_batches
        return None

    def __str__(self):
        return f"Фарш {self.production_id}"

    class Meta:
        managed = True
        db_table = "minced_meat_batch"
        verbose_name = "Фарш"
        verbose_name_plural = "Фарш"


class MincedMeatBatchRawMeatBatch(CreatedModel):
    minced_meat_batch = models.ForeignKey(
        MincedMeatBatch,
        on_delete=models.CASCADE,
        related_name="raw_meat_batches",
        blank=True,
    )
    raw_meat_batch = models.ForeignKey(
        RawMeatBatch, on_delete=models.CASCADE, blank=True
    )
    weight = models.FloatField(blank=True)

    class Meta:
        managed = True
        db_table = "minced_meat_batch_raw_meat_batch"


class MincedMeatBatchMeatBlank(CreatedModel):
    minced_meat_batch = models.ForeignKey(
        MincedMeatBatch, on_delete=models.CASCADE, related_name="meat_blanks"
    )
    meat_blank = models.ForeignKey(MeatBlank, on_delete=models.CASCADE)
    weight = models.FloatField(blank=True)

    class Meta:
        managed = True
        db_table = "minced_meat_batch_meat_blank"


class MincedMeatBatchSecondMeatBlank(CreatedModel):
    minced_meat_batch = models.ForeignKey(
        MincedMeatBatch, on_delete=models.CASCADE, related_name="second_minced_meat"
    )
    second_minced_meat = models.ForeignKey(SecondMincedMeat, on_delete=models.CASCADE)
    weight = models.FloatField(blank=True)

    class Meta:
        managed = True
        db_table = "minced_meat_batch_second_meat_blank"


# --- Новые модели учета потребления сырья по замесам ---


class MincedMeatBatchMixConsumptionRaw(CreatedModel):
    """Фиксация списания сырья на конкретный замес.

    Создается при завершении замеса, чтобы последующие корректировки рецепта
    не влияли на уже произведенные замесы.
    """

    minced_meat_batch_mix = models.ForeignKey(
        "MincedMeatBatchMix", on_delete=models.CASCADE, related_name="consumption_raw"
    )
    raw_meat_batch = models.ForeignKey("RawMeatBatch", on_delete=models.CASCADE)
    weight = models.FloatField()

    class Meta:
        managed = True
        db_table = "minced_meat_batch_mix_consumption_raw"
        verbose_name = "Списание сырья по замесу"
        verbose_name_plural = "Списания сырья по замесам"


class MincedMeatBatchMixConsumptionMeatBlank(CreatedModel):
    """Фиксация списания заготовок на конкретный замес."""

    minced_meat_batch_mix = models.ForeignKey(
        "MincedMeatBatchMix",
        on_delete=models.CASCADE,
        related_name="consumption_meat_blank",
    )
    meat_blank = models.ForeignKey("MeatBlank", on_delete=models.CASCADE)
    weight = models.FloatField()

    class Meta:
        managed = True
        db_table = "minced_meat_batch_mix_consumption_meat_blank"
        verbose_name = "Списание заготовки по замесу"
        verbose_name_plural = "Списания заготовок по замесам"


class MincedMeatBatchMixConsumptionSecondMeatBlank(CreatedModel):
    """Фиксация списания вторфарша на конкретный замес."""

    minced_meat_batch_mix = models.ForeignKey(
        "MincedMeatBatchMix",
        on_delete=models.CASCADE,
        related_name="consumption_second_meat_blank",
    )
    second_minced_meat = models.ForeignKey("SecondMincedMeat", on_delete=models.CASCADE)
    weight = models.FloatField()

    class Meta:
        managed = True
        db_table = "minced_meat_batch_mix_consumption_second_meat_blank"
        verbose_name = "Списание вторфарша по замесу"
        verbose_name_plural = "Списания вторфарша по замесам"


class MincedMeatBatchMix(CreatedModel):
    minced_meat_batch = models.ForeignKey(
        MincedMeatBatch, on_delete=models.CASCADE, related_name="mixes", null=True
    )
    remake = models.BooleanField(default=False)
    production_id = models.CharField(max_length=255)
    line_type = models.SmallIntegerField(null=True, default=None)

    @staticmethod
    def get_by_date_range(start: datetime, end: datetime):
        qs = MincedMeatBatchMix.objects
        qs = qs.filter(created_at__gte=start, created_at__lte=end)

        minced_meat_batch_mixes = qs.all()

        return minced_meat_batch_mixes

    def get_mix_number(self):
        """Извлекает номер замеса из production_id (формат: DDMM/NN/i)."""
        try:
            return int(str(self.production_id).split("/")[-1])
        except (ValueError, IndexError):
            return 0

    def __str__(self):
        return self.production_id

    class Meta:
        verbose_name = "Склад ГП"
        verbose_name_plural = "Склад ГП"
        managed = True
        db_table = "minced_meat_batch_mix"


class MincedMeatBatchStatus(CreatedModel):
    minced_meat_batch_mix = models.ForeignKey(
        MincedMeatBatchMix, on_delete=models.CASCADE, related_name="statuses"
    )

    status = models.ForeignKey(Status, on_delete=models.CASCADE)

    additional_data = models.JSONField(null=True)
    notify = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = "minced_meat_batch_mix_status"


# --- Сигнал: при завершении замеса фиксируем списание сырья/заготовок ---


@receiver(post_save, sender=MincedMeatBatchStatus)
def on_mix_completed_create_consumption(
    sender, instance: "MincedMeatBatchStatus", created: bool, **kwargs
):
    """При появлении статуса загрузки в плиточник/шокер/паллет создаём записи списаний для этого замеса.

    Критерии списания: status.codename in {"mixer_tiller_mix_meat", "to_shocker_finish", "pallet_is_set"}.
    Распределение: равномерно по оставшимся замесам на момент загрузки текущего.
    """
    if not created:
        return
    if instance.status.codename not in {
        "mixer_tiller_mix_meat",
        "to_shocker_finish",
        "pallet_is_set",
    }:
        return
    mix = instance.minced_meat_batch_mix
    if not mix or not mix.minced_meat_batch:
        return

    batch = mix.minced_meat_batch

    # Пропускаем, если уже есть любые записи списаний по этому замесу
    if (
        MincedMeatBatchMixConsumptionRaw.objects.filter(
            minced_meat_batch_mix=mix
        ).exists()
        or MincedMeatBatchMixConsumptionMeatBlank.objects.filter(
            minced_meat_batch_mix=mix
        ).exists()
    ):
        return

    total_mixes = batch.number_mix or 0
    if total_mixes <= 0:
        return

    # Сколько замесов уже имеют зафиксированное списание в этой партии
    consumed_mix_ids_raw: Set[int] = set(
        MincedMeatBatchMixConsumptionRaw.objects.filter(
            minced_meat_batch_mix__minced_meat_batch=batch
        ).values_list("minced_meat_batch_mix_id", flat=True)
    )
    consumed_mix_ids_blank: Set[int] = set(
        MincedMeatBatchMixConsumptionMeatBlank.objects.filter(
            minced_meat_batch_mix__minced_meat_batch=batch
        ).values_list("minced_meat_batch_mix_id", flat=True)
    )
    produced_count = len(consumed_mix_ids_raw.union(consumed_mix_ids_blank))

    remaining_mixes_before = max(total_mixes - produced_count, 0)
    if remaining_mixes_before == 0:
        return

    # 1) Сырьё, привязанное напрямую к партии фарша
    raw_rels = MincedMeatBatchRawMeatBatch.objects.filter(minced_meat_batch=batch).all()
    for rel in raw_rels:
        consumed_sum = (
            MincedMeatBatchMixConsumptionRaw.objects.filter(
                minced_meat_batch_mix__minced_meat_batch=batch,
                raw_meat_batch=rel.raw_meat_batch,
            ).aggregate(w=Sum("weight"))["w"]
            or 0.0
        )
        remaining_weight = max(float(rel.weight) - float(consumed_sum), 0.0)
        if remaining_weight <= 0:
            continue
        share = remaining_weight / float(remaining_mixes_before)
        if share > 0:
            MincedMeatBatchMixConsumptionRaw.objects.create(
                minced_meat_batch_mix=mix,
                raw_meat_batch=rel.raw_meat_batch,
                weight=share,
            )

    # 2) Заготовки, привязанные к партии фарша
    blank_rels = MincedMeatBatchMeatBlank.objects.filter(minced_meat_batch=batch).all()
    for rel in blank_rels:
        consumed_sum = (
            MincedMeatBatchMixConsumptionMeatBlank.objects.filter(
                minced_meat_batch_mix__minced_meat_batch=batch,
                meat_blank=rel.meat_blank,
            ).aggregate(w=Sum("weight"))["w"]
            or 0.0
        )
        remaining_weight = max(float(rel.weight) - float(consumed_sum), 0.0)
        if remaining_weight <= 0:
            continue
        share = remaining_weight / float(remaining_mixes_before)
        if share > 0:
            MincedMeatBatchMixConsumptionMeatBlank.objects.create(
                minced_meat_batch_mix=mix, meat_blank=rel.meat_blank, weight=share
            )

    # 3) Вторфарш, привязанный к партии фарша
    second_meat_rels = MincedMeatBatchSecondMeatBlank.objects.filter(minced_meat_batch=batch).all()
    for rel in second_meat_rels:
        consumed_sum = (
            MincedMeatBatchMixConsumptionSecondMeatBlank.objects.filter(
                minced_meat_batch_mix__minced_meat_batch=batch,
                second_minced_meat=rel.second_minced_meat,
            ).aggregate(w=Sum("weight"))["w"]
            or 0.0
        )
        remaining_weight = max(float(rel.weight) - float(consumed_sum), 0.0)
        if remaining_weight <= 0:
            continue
        share = remaining_weight / float(remaining_mixes_before)
        if share > 0:
            MincedMeatBatchMixConsumptionSecondMeatBlank.objects.create(
                minced_meat_batch_mix=mix, second_minced_meat=rel.second_minced_meat, weight=share
            )


class TotalMincedMeatBatchStatus(CreatedModel):
    minced_meat_batch = models.ForeignKey(
        MincedMeatBatch, on_delete=models.CASCADE, related_name="statuses"
    )

    status = models.ForeignKey(Status, on_delete=models.CASCADE)

    additional_data = models.JSONField(null=True)

    class Meta:
        managed = True
        db_table = "minced_meat_batch_status"


class Shipment(CreatedModel):
    customer = models.CharField(max_length=255, verbose_name="Кому отгрузили")

    def __str__(self):
        return f"Отгрузка №{self.id}"

    @staticmethod
    def get_by_date_range(start: datetime, end: datetime):
        shipments = Shipment.objects.filter(
            created_at__gt=start, created_at__lt=end
        ).all()

        return shipments

    class Meta:
        managed = True
        db_table = "shipment"
        verbose_name = "Отгрузка"
        verbose_name_plural = "Отгрузки"


class ShipmentPallet(CreatedModel):
    minced_meat_batch_mix = models.ForeignKey(
        MincedMeatBatchMix, on_delete=models.CASCADE, related_name="shipment_pallets"
    )
    shipment = models.ForeignKey(
        Shipment, on_delete=models.CASCADE, related_name="pallets"
    )

    number = models.CharField(max_length=255)
    weight = models.FloatField()

    class Meta:
        managed = True
        db_table = "shipment_pallet"


class Tilers(CreatedModel):
    minced_meat_batch_mix = models.ForeignKey(
        MincedMeatBatchMix,
        on_delete=models.SET_NULL,
        related_name="mixes",
        null=True,
        blank=True,
        verbose_name="Замес",
    )
    status = models.BooleanField(default=True, blank=True, verbose_name="Свободен")

    class Meta:
        managed = True
        db_table = "tilers"
        verbose_name = "Плиточник"
        verbose_name_plural = "Плиточники"


class MincedMeatBatchFile(CreatedModel):
    minced_meat_batch = models.ForeignKey(MincedMeatBatch, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    file_location = models.FileField(
        storage=MinioBackend(bucket_name="backend-private"),
        upload_to="photo_marked_and_storing",
        null=True,
    )

    class Meta:
        managed = True
        db_table = "minced_meat_batch_file"


class SecondMincedMeatBatchFile(CreatedModel):
    second_minced_meat = models.ForeignKey(
        SecondMincedMeat, on_delete=models.CASCADE, null=True
    )
    name = models.CharField(max_length=255)
    file_location = models.FileField(
        storage=MinioBackend(bucket_name="backend-private"),
        upload_to="photo_marked_and_storing_second_meat",
        null=True,
    )

    class Meta:
        managed = True
        db_table = "second_minced_meat_batch_file"


class ShockerMixLoad(CreatedModel):
    minced_meat_batch_mix = models.ForeignKey(
        MincedMeatBatchMix,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mix",
        verbose_name="Фарш",
    )
    second_minced_meat = models.ForeignKey(
        SecondMincedMeat,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="second_meat",
        verbose_name="Вторфарш",
    )
    shocker = models.ForeignKey(
        ShockerCamera,
        on_delete=models.SET_NULL,
        related_name="shocker",
        null=True,
        verbose_name="Номер шокера",
    )
    additional_data = models.JSONField(null=True, verbose_name="Доп. данные")
    status_unload = models.BooleanField(default=False, verbose_name="Статус отгрузки")

    def __str__(self):
        if self.second_minced_meat:
            return f"Загрузка в шокер {self.second_minced_meat.production_id}"
        else:
            return (
                "Загрузка в шокер "
                f"{self.minced_meat_batch_mix.production_id if self.minced_meat_batch_mix else 'None'}"
            )

    class Meta:
        managed = True
        verbose_name = "Загрузки в шокере"
        verbose_name_plural = "Загрузки в шокере"
        db_table = "shocker_mix_pallet_list"


class BufferPalletMars(CreatedModel):
    pallet_id = models.IntegerField(verbose_name="ID паллета")
    box_count = models.IntegerField(verbose_name="Кол-во ящиков")
    brutto_weight = models.FloatField(verbose_name="Вес брутто")
    netto_weight = models.FloatField(verbose_name="Вес нетто")
    pallet_weight = models.FloatField(verbose_name="Вес паллета")

    def __str__(self):
        return f"{self.pallet_id}"

    class Meta:
        verbose_name = "Паллеты с остатками от фарша Марс"
        verbose_name_plural = "Паллеты с остатками от фарша Марс"
        db_table = "buffer_pallets_mars"


class WarehouseResponses(models.Model):
    res_date = models.DateField(null=True, verbose_name="Дата")

    def __str__(self):
        return str(self.res_date)

    class Meta:
        verbose_name = "Отчет"
        verbose_name_plural = "Отчеты"
        db_table = "warehouse_responses"
