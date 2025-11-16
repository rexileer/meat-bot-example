from django.core.management.base import BaseCommand
from Web.CRM.models import MincedMeatBatchMix, MincedMeatBatchStatus, Status


class Command(BaseCommand):
    help = 'Исправление застрявших статусов замесов'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет исправлено без внесения изменений',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительно исправить все найденные проблемы',
        )
        parser.add_argument(
            '--batch-id',
            type=int,
            help='Исправить только замесы конкретной партии',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        batch_id = options.get('batch_id')
        
        self.stdout.write(self.style.SUCCESS('=== ИСПРАВЛЕНИЕ СТАТУСОВ ЗАМЕСОВ ===\n'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('РЕЖИМ ПРОСМОТРА - изменения не будут внесены\n'))
        
        # Фильтр по партии если указан
        mix_filter = {}
        if batch_id:
            mix_filter['minced_meat_batch_id'] = batch_id
            self.stdout.write(f'Обработка только партии {batch_id}\n')
        
        # 1. Замесы без статусов - добавить press_operator_mix_meat
        mixes_without_status = MincedMeatBatchMix.objects.filter(statuses__isnull=True, **mix_filter)
        if mixes_without_status.exists():
            self.stdout.write(f'Найдено замесов без статусов: {mixes_without_status.count()}')
            if not dry_run:
                press_operator_status = Status.objects.get(codename='press_operator_mix_meat')
                for mix in mixes_without_status:
                    MincedMeatBatchStatus.objects.create(
                        minced_meat_batch_mix=mix,
                        status=press_operator_status,
                        notify=True
                    )
                self.stdout.write(self.style.SUCCESS(f'Добавлен статус "press_operator_mix_meat" для {mixes_without_status.count()} замесов'))
            else:
                for mix in mixes_without_status:
                    self.stdout.write(f'  - ID: {mix.id}, Партия: {mix.minced_meat_batch_id} -> добавить статус "press_operator_mix_meat"')
        
        # 2. Замесы застрявшие после mixer_mix_meat_end - добавить mixer_tiller_mix_meat
        stuck_after_mixer_end = MincedMeatBatchMix.objects.filter(
            statuses__status__codename='mixer_mix_meat_end',
            **mix_filter
        ).exclude(
            statuses__status__codename__in=[
                'mixer_tiller_mix_meat', 'mixer_tiller_mix_meat_end', 
                'unloaded_to_packer', 'unloaded_to_packer_end',
                'to_shocker', 'to_shocker_finish', 'unload_shocker', 'unload_shocker_finish',
                'palletizing', 'palletizing_end', 'pallet_is_set'
            ]
        )
        if stuck_after_mixer_end.exists():
            self.stdout.write(f'Найдено замесов застрявших после mixer_mix_meat_end: {stuck_after_mixer_end.count()}')
            if not dry_run:
                tiller_status = Status.objects.get(codename='mixer_tiller_mix_meat')
                for mix in stuck_after_mixer_end:
                    MincedMeatBatchStatus.objects.create(
                        minced_meat_batch_mix=mix,
                        status=tiller_status,
                        notify=True
                    )
                self.stdout.write(self.style.SUCCESS(f'Добавлен статус "mixer_tiller_mix_meat" для {stuck_after_mixer_end.count()} замесов'))
            else:
                for mix in stuck_after_mixer_end:
                    self.stdout.write(f'  - ID: {mix.id}, Партия: {mix.minced_meat_batch_id} -> добавить статус "mixer_tiller_mix_meat"')
        
        # 3. Замесы застрявшие на unload_shocker_finish - добавить palletizing
        stuck_on_unload_shocker = MincedMeatBatchMix.objects.filter(
            statuses__status__codename='unload_shocker_finish',
            **mix_filter
        ).exclude(
            statuses__status__codename__in=['palletizing', 'palletizing_end', 'pallet_is_set']
        )
        if stuck_on_unload_shocker.exists():
            self.stdout.write(f'Найдено замесов застрявших после выгрузки из шокера: {stuck_on_unload_shocker.count()}')
            if not dry_run:
                palletizing_status = Status.objects.get(codename='palletizing')
                for mix in stuck_on_unload_shocker:
                    MincedMeatBatchStatus.objects.create(
                        minced_meat_batch_mix=mix,
                        status=palletizing_status,
                        notify=True
                    )
                self.stdout.write(self.style.SUCCESS(f'Добавлен статус "palletizing" для {stuck_on_unload_shocker.count()} замесов'))
            else:
                for mix in stuck_on_unload_shocker:
                    self.stdout.write(f'  - ID: {mix.id}, Партия: {mix.minced_meat_batch_id} -> добавить статус "palletizing"')
        
        # 4. Замесы застрявшие на palletizing - добавить palletizing_end
        stuck_on_palletizing = MincedMeatBatchMix.objects.filter(
            statuses__status__codename='palletizing',
            **mix_filter
        ).exclude(
            statuses__status__codename__in=['palletizing_end', 'pallet_is_set']
        )
        if stuck_on_palletizing.exists():
            self.stdout.write(f'Найдено замесов застрявших на паллетировании: {stuck_on_palletizing.count()}')
            if not dry_run:
                palletizing_end_status = Status.objects.get(codename='palletizing_end')
                for mix in stuck_on_palletizing:
                    MincedMeatBatchStatus.objects.create(
                        minced_meat_batch_mix=mix,
                        status=palletizing_end_status,
                        notify=False
                    )
                self.stdout.write(self.style.SUCCESS(f'Добавлен статус "palletizing_end" для {stuck_on_palletizing.count()} замесов'))
            else:
                for mix in stuck_on_palletizing:
                    self.stdout.write(f'  - ID: {mix.id}, Партия: {mix.minced_meat_batch_id} -> добавить статус "palletizing_end"')
        
        # 5. Принудительное исправление проблемных замесов
        if force:
            problematic_mixes = MincedMeatBatchMix.objects.filter(
                statuses__isnull=False,
                **mix_filter
            ).exclude(
                statuses__status__codename='work_is_finished'
            )
            if problematic_mixes.exists():
                self.stdout.write(f'Найдено проблемных замесов (принудительное исправление): {problematic_mixes.count()}')
                if not dry_run:
                    # Определяем правильный следующий статус для каждого замеса
                    for mix in problematic_mixes:
                        current_statuses = mix.statuses.all().values_list('status__codename', flat=True)
                        
                        # Логика определения следующего статуса
                        if 'press_operator_mix_meat_end' in current_statuses and 'mixer_mix_meat' not in current_statuses:
                            next_status = Status.objects.get(codename='mixer_mix_meat')
                        elif 'mixer_mix_meat_end' in current_statuses and 'mixer_tiller_mix_meat' not in current_statuses:
                            next_status = Status.objects.get(codename='mixer_tiller_mix_meat')
                        elif 'unload_shocker_finish' in current_statuses and 'palletizing' not in current_statuses:
                            next_status = Status.objects.get(codename='palletizing')
                        elif 'palletizing' in current_statuses and 'palletizing_end' not in current_statuses:
                            next_status = Status.objects.get(codename='palletizing_end')
                        else:
                            continue
                        
                        MincedMeatBatchStatus.objects.create(
                            minced_meat_batch_mix=mix,
                            status=next_status,
                            notify=True
                        )
                    self.stdout.write(self.style.SUCCESS(f'Принудительно исправлено {problematic_mixes.count()} замесов'))
                else:
                    for mix in problematic_mixes:
                        current_statuses = list(mix.statuses.all().values_list('status__codename', flat=True))
                        self.stdout.write(f'  - ID: {mix.id}, Партия: {mix.minced_meat_batch_id}, Текущие статусы: {current_statuses}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nДля применения изменений запустите команду без --dry-run'))
        else:
            self.stdout.write(self.style.SUCCESS('\nИсправление завершено'))

