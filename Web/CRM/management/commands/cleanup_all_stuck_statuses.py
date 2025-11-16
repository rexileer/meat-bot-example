from django.core.management.base import BaseCommand
from Web.CRM.models import MeatBlank, MeatBlankStatus, MincedMeatBatchMix, MincedMeatBatchStatus, Status


class Command(BaseCommand):
    help = 'Принудительная очистка всех застрявших статусов'

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

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write(self.style.SUCCESS('=== ПРИНУДИТЕЛЬНАЯ ОЧИСТКА СТАТУСОВ ===\n'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('РЕЖИМ ПРОСМОТРА - изменения не будут внесены\n'))
        
        total_fixed = 0
        
        # 1. Исправление заготовок
        self.stdout.write(self.style.WARNING('=== ИСПРАВЛЕНИЕ ЗАГОТОВОК ==='))
        
        # Заготовки без статусов
        blanks_without_status = MeatBlank.objects.filter(statuses__isnull=True)
        if blanks_without_status.exists():
            self.stdout.write(f'Заготовки без статусов: {blanks_without_status.count()}')
            if not dry_run:
                defrosting_status = Status.objects.get(codename='defrosting')
                for blank in blanks_without_status:
                    MeatBlankStatus.objects.create(
                        meat_blank=blank,
                        status=defrosting_status,
                        notify=True
                    )
                total_fixed += blanks_without_status.count()
                self.stdout.write(self.style.SUCCESS(f'Исправлено: {blanks_without_status.count()} заготовок'))
        
        # Застрявшие на storekeeper_output
        stuck_on_output = MeatBlank.objects.filter(
            statuses__status__codename='storekeeper_output'
        ).exclude(
            statuses__status__codename='storekeeper_outputed'
        )
        if stuck_on_output.exists():
            self.stdout.write(f'Застрявшие на вводе веса: {stuck_on_output.count()}')
            if not dry_run:
                outputed_status = Status.objects.get(codename='storekeeper_outputed')
                for blank in stuck_on_output:
                    MeatBlankStatus.objects.create(
                        meat_blank=blank,
                        status=outputed_status,
                        notify=False
                    )
                total_fixed += stuck_on_output.count()
                self.stdout.write(self.style.SUCCESS(f'Исправлено: {stuck_on_output.count()} заготовок'))
        
        # 2. Исправление замесов
        self.stdout.write(self.style.WARNING('\n=== ИСПРАВЛЕНИЕ ЗАМЕСОВ ==='))
        
        # Замесы без статусов
        mixes_without_status = MincedMeatBatchMix.objects.filter(statuses__isnull=True)
        if mixes_without_status.exists():
            self.stdout.write(f'Замесы без статусов: {mixes_without_status.count()}')
            if not dry_run:
                press_operator_status = Status.objects.get(codename='press_operator_mix_meat')
                for mix in mixes_without_status:
                    MincedMeatBatchStatus.objects.create(
                        minced_meat_batch_mix=mix,
                        status=press_operator_status,
                        notify=True
                    )
                total_fixed += mixes_without_status.count()
                self.stdout.write(self.style.SUCCESS(f'Исправлено: {mixes_without_status.count()} замесов'))
        
        # Застрявшие после mixer_mix_meat_end
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
        if stuck_after_mixer_end.exists():
            self.stdout.write(f'Застрявшие после mixer_mix_meat_end: {stuck_after_mixer_end.count()}')
            if not dry_run:
                tiller_status = Status.objects.get(codename='mixer_tiller_mix_meat')
                for mix in stuck_after_mixer_end:
                    MincedMeatBatchStatus.objects.create(
                        minced_meat_batch_mix=mix,
                        status=tiller_status,
                        notify=True
                    )
                total_fixed += stuck_after_mixer_end.count()
                self.stdout.write(self.style.SUCCESS(f'Исправлено: {stuck_after_mixer_end.count()} замесов'))
        
        # Застрявшие на unload_shocker_finish
        stuck_on_unload_shocker = MincedMeatBatchMix.objects.filter(
            statuses__status__codename='unload_shocker_finish'
        ).exclude(
            statuses__status__codename__in=['palletizing', 'palletizing_end', 'pallet_is_set']
        )
        if stuck_on_unload_shocker.exists():
            self.stdout.write(f'Застрявшие после выгрузки из шокера: {stuck_on_unload_shocker.count()}')
            if not dry_run:
                palletizing_status = Status.objects.get(codename='palletizing')
                for mix in stuck_on_unload_shocker:
                    MincedMeatBatchStatus.objects.create(
                        minced_meat_batch_mix=mix,
                        status=palletizing_status,
                        notify=True
                    )
                total_fixed += stuck_on_unload_shocker.count()
                self.stdout.write(self.style.SUCCESS(f'Исправлено: {stuck_on_unload_shocker.count()} замесов'))
        
        # Застрявшие на palletizing
        stuck_on_palletizing = MincedMeatBatchMix.objects.filter(
            statuses__status__codename='palletizing'
        ).exclude(
            statuses__status__codename__in=['palletizing_end', 'pallet_is_set']
        )
        if stuck_on_palletizing.exists():
            self.stdout.write(f'Застрявшие на паллетировании: {stuck_on_palletizing.count()}')
            if not dry_run:
                palletizing_end_status = Status.objects.get(codename='palletizing_end')
                for mix in stuck_on_palletizing:
                    MincedMeatBatchStatus.objects.create(
                        minced_meat_batch_mix=mix,
                        status=palletizing_end_status,
                        notify=False
                    )
                total_fixed += stuck_on_palletizing.count()
                self.stdout.write(self.style.SUCCESS(f'Исправлено: {stuck_on_palletizing.count()} замесов'))
        
        # 3. Принудительное исправление проблемных записей
        if force:
            self.stdout.write(self.style.WARNING('\n=== ПРИНУДИТЕЛЬНОЕ ИСПРАВЛЕНИЕ ==='))
            
            # Проблемные заготовки
            problematic_blanks = MeatBlank.objects.filter(
                statuses__isnull=False
            ).exclude(
                statuses__status__codename__in=[
                    'defrosting', 'to_defroster', 'loaded_to_defroster', 
                    'unloaded_from_defroster', 'storekeeper_output', 'storekeeper_outputed',
                    'rastarshik_unload_meat_blank', 'rastarshik_unload_meat_blank_end'
                ]
            )
            if problematic_blanks.exists():
                self.stdout.write(f'Проблемные заготовки: {problematic_blanks.count()}')
                if not dry_run:
                    defrosting_status = Status.objects.get(codename='defrosting')
                    for blank in problematic_blanks:
                        # Удаляем все статусы кроме defrosting
                        blank.statuses.exclude(status__codename='defrosting').delete()
                        # Добавляем defrosting если его нет
                        if not blank.statuses.filter(status__codename='defrosting').exists():
                            MeatBlankStatus.objects.create(
                                meat_blank=blank,
                                status=defrosting_status,
                                notify=True
                            )
                    total_fixed += problematic_blanks.count()
                    self.stdout.write(self.style.SUCCESS(f'Принудительно исправлено: {problematic_blanks.count()} заготовок'))
            
            # Проблемные замесы
            problematic_mixes = MincedMeatBatchMix.objects.filter(
                statuses__isnull=False
            ).exclude(
                statuses__status__codename='work_is_finished'
            )
            if problematic_mixes.exists():
                self.stdout.write(f'Проблемные замесы: {problematic_mixes.count()}')
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
                    total_fixed += problematic_mixes.count()
                    self.stdout.write(self.style.SUCCESS(f'Принудительно исправлено: {problematic_mixes.count()} замесов'))
        
        # 4. Итоговая статистика
        self.stdout.write(self.style.WARNING('\n=== ИТОГОВАЯ СТАТИСТИКА ==='))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('РЕЖИМ ПРОСМОТРА - изменения не были внесены'))
            self.stdout.write('Для применения изменений запустите команду без --dry-run')
        else:
            self.stdout.write(self.style.SUCCESS(f'Всего исправлено записей: {total_fixed}'))
            self.stdout.write('Рекомендуется перезапустить бота для применения изменений')
        
        self.stdout.write(self.style.SUCCESS('\nОчистка завершена'))

