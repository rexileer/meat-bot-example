# Generated manually for MincedMeatBatchMixConsumptionSecondMeatBlank model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('CRM', '0027_add_buh_accounting_field'),
    ]

    operations = [
        migrations.CreateModel(
            name='MincedMeatBatchMixConsumptionSecondMeatBlank',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('minced_meat_batch_mix', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='consumption_second_meat_blank', to='CRM.mincedmeatbatchmix')),
                ('second_minced_meat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='CRM.secondmincedmeat')),
                ('weight', models.FloatField()),
            ],
            options={
                'verbose_name': 'Списание вторфарша по замесу',
                'verbose_name_plural': 'Списания вторфарша по замесам',
                'db_table': 'minced_meat_batch_mix_consumption_second_meat_blank',
                'managed': True,
            },
        ),
    ]
