from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("CRM", "0026_mix_consumption"),
    ]

    operations = [
        migrations.AddField(
            model_name="rawmeatbatch",
            name="buh_accounting",
            field=models.CharField(max_length=255, null=True, verbose_name="Тип для бух.учета"),
        ),
    ]