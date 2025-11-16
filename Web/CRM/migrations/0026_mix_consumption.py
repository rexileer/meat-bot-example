from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("CRM", "0025_mincedmeatbatch_is_shocker_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="MincedMeatBatchMixConsumptionRaw",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Дата изменения")),
                ("weight", models.FloatField()),
                (
                    "minced_meat_batch_mix",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="consumption_raw",
                        to="CRM.mincedmeatbatchmix",
                    ),
                ),
                ("raw_meat_batch", models.ForeignKey(on_delete=models.deletion.CASCADE, to="CRM.rawmeatbatch")),
            ],
            options={
                "managed": True,
                "db_table": "minced_meat_batch_mix_consumption_raw",
                "verbose_name": "Списание сырья по замесу",
                "verbose_name_plural": "Списания сырья по замесам",
            },
        ),
        migrations.CreateModel(
            name="MincedMeatBatchMixConsumptionMeatBlank",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Дата изменения")),
                ("weight", models.FloatField()),
                (
                    "minced_meat_batch_mix",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="consumption_meat_blank",
                        to="CRM.mincedmeatbatchmix",
                    ),
                ),
                ("meat_blank", models.ForeignKey(on_delete=models.deletion.CASCADE, to="CRM.meatblank")),
            ],
            options={
                "managed": True,
                "db_table": "minced_meat_batch_mix_consumption_meat_blank",
                "verbose_name": "Списание заготовки по замесу",
                "verbose_name_plural": "Списания заготовок по замесам",
            },
        ),
        # В БД поле уже существует, добавляем его только в состояние миграций,
        # чтобы избежать попытки повторного добавления столбца.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="rawmeatbatch",
                    name="buh_accounting",
                    field=models.CharField(max_length=255, null=True, verbose_name="Тип для бух.учета"),
                )
            ],
            database_operations=[],
        ),
    ]



