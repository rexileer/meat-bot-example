from django.core.management.base import BaseCommand
from Web.CRM.models import MincedMeatBatchMix, MincedMeatBatchStatus, Status


class Command(BaseCommand):
    help = 'Диагностика проблем со статусами замесов'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Показать детальную информацию о каждом замесе',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== ДИАГНОСТИКА СТАТУСОВ ЗАМЕСОВ ===\n'))
        
        # 1. Замесы без статусов
        mixes_without_status = MincedMeatBatchMix.objects.filter(statuses__isnull=True)
        self.stdout.write(f'Замесы без статусов: {mixes_without_status.count()}')
        if options['detailed'] and mixes_without_status.exists():
            for mix in mixes_without_status:
                self.stdout.write(f'  - ID: {mix.id}, Партия: {mix.minced_meat_batch_id}, Линия: {mix.line_type}')
        
        # 2. Замесы застрявшие после завершения перемешивания и анализа
        stuck_after_mixer_end = MincedMeatBatchMix.objects.filter(
            statuses__status__codename='mixer_mix_meat_end'
        ).exclude(
            statuses__status__codename__in=[
                'mixer_tiller_mix_meat', 'mixer_tiller_mix_meat_end', 
                'unloaded_to_packer', 'unloaded_to_packer_end',
                'to_shocker', 'to_shocker_finish', 'unload_shocker', 'unload_shocker_finish',
                'palletizing', 'palletizing_end', 'pallet_is_set'
            ]
        )
        self.stdout.write(f'Замесы застрявшие после mixer_mix_meat_end: {stuck_after_mixer_end.count()}')
        if options['detailed'] and stuck_after_mixer_end.exists():
            for mix in stuck_after_mixer_end:
                statuses = mix.statuses.all().values_list('status__codename', flat=True)
                self.stdout.write(f'  - ID: {mix.id}, Партия: {mix.minced_meat_batch_id}, Статусы: {list(statuses)}')
        
        # 3. Замесы застрявшие на palletizing
        stuck_on_palletizing = MincedMeatBatchMix.objects.filter(
            statuses__status__codename='palletizing'
        ).exclude(
            statuses__status__codename__in=['palletizing_end', 'pallet_is_set']
        )
        self.stdout.write(f'Замесы застрявшие на паллетировании: {stuck_on_palletizing.count()}')
        
        # 4. Замесы застрявшие на unload_shocker_finish
        stuck_on_unload_shocker = MincedMeatBatchMix.objects.filter(
            statuses__status__codename='unload_shocker_finish'
        ).exclude(
            statuses__status__codename__in=['palletizing', 'palletizing_end', 'pallet_is_set']
        )
        self.stdout.write(f'Замесы застрявшие после выгрузки из шокера: {stuck_on_unload_shocker.count()}')
        
        # 5. Замесы с неполным потоком (не дошли до work_is_finished)
        incomplete_flow = MincedMeatBatchMix.objects.filter(
            statuses__isnull=False
        ).exclude(
            statuses__status__codename='work_is_finished'
        )
        self.stdout.write(f'Замесы с неполным потоком: {incomplete_flow.count()}')
        
        # 6. Статистика по статусам замесов
        self.stdout.write('\n=== СТАТИСТИКА ПО СТАТУСАМ ЗАМЕСОВ ===')
        status_counts = {}
        for status in Status.objects.filter(mincedmeatbatchstatus__isnull=False).distinct():
            count = MincedMeatBatchStatus.objects.filter(status=status).count()
            status_counts[status.codename] = count
            if count > 0:
                self.stdout.write(f'{status.codename}: {count}')
        
        # 7. Проблемные замесы по партиям
        self.stdout.write('\n=== ПРОБЛЕМНЫЕ ЗАМЕСЫ ПО ПАРТИЯМ ===')
        problematic_batches = MincedMeatBatchMix.objects.filter(
            statuses__isnull=False
        ).exclude(
            statuses__status__codename='work_is_finished'
        ).values_list('minced_meat_batch_id', flat=True).distinct()
        
        for batch_id in problematic_batches:
            batch_mixes = MincedMeatBatchMix.objects.filter(minced_meat_batch_id=batch_id)
            incomplete_count = batch_mixes.exclude(statuses__status__codename='work_is_finished').count()
            total_count = batch_mixes.count()
            self.stdout.write(f'Партия {batch_id}: {incomplete_count}/{total_count} незавершенных замесов')
        
        if stuck_after_mixer_end.exists() or stuck_on_palletizing.exists() or stuck_on_unload_shocker.exists():
            self.stdout.write('\nРекомендуется выполнить: python manage.py fix_mix_statuses')
        
        self.stdout.write(self.style.SUCCESS('\nДиагностика завершена'))

