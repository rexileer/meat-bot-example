from django.core.management.base import BaseCommand
from Web.CRM.models import MeatBlank, MeatBlankStatus, MincedMeatBatchMix, MincedMeatBatchStatus, Status


class Command(BaseCommand):
    help = 'Полная диагностика всех проблем со статусами'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Показать детальную информацию',
        )

    def handle(self, *args, **options):
        detailed = options['detailed']
        
        self.stdout.write(self.style.SUCCESS('=== ПОЛНАЯ ДИАГНОСТИКА СТАТУСОВ ===\n'))
        
        # 1. Общая статистика
        total_blanks = MeatBlank.objects.count()
        total_mixes = MincedMeatBatchMix.objects.count()
        total_blank_statuses = MeatBlankStatus.objects.count()
        total_mix_statuses = MincedMeatBatchStatus.objects.count()
        
        self.stdout.write(f'Всего заготовок: {total_blanks}')
        self.stdout.write(f'Всего замесов: {total_mixes}')
        self.stdout.write(f'Всего статусов заготовок: {total_blank_statuses}')
        self.stdout.write(f'Всего статусов замесов: {total_mix_statuses}\n')
        
        # 2. Проблемы с заготовками
        self.stdout.write(self.style.WARNING('=== ПРОБЛЕМЫ С ЗАГОТОВКАМИ ==='))
        
        blanks_without_status = MeatBlank.objects.filter(statuses__isnull=True)
        self.stdout.write(f'Заготовки без статусов: {blanks_without_status.count()}')
        
        stuck_on_output = MeatBlank.objects.filter(
            statuses__status__codename='storekeeper_output'
        ).exclude(
            statuses__status__codename='storekeeper_outputed'
        )
        self.stdout.write(f'Застрявшие на вводе веса: {stuck_on_output.count()}')
        
        stuck_on_defrosting = MeatBlank.objects.filter(
            statuses__status__codename='defrosting'
        ).exclude(
            statuses__status__codename__in=['to_defroster', 'loaded_to_defroster']
        )
        self.stdout.write(f'Застрявшие на дефросте: {stuck_on_defrosting.count()}')
        
        # 3. Проблемы с замесами
        self.stdout.write(self.style.WARNING('\n=== ПРОБЛЕМЫ С ЗАМЕСАМИ ==='))
        
        mixes_without_status = MincedMeatBatchMix.objects.filter(statuses__isnull=True)
        self.stdout.write(f'Замесы без статусов: {mixes_without_status.count()}')
        
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
        self.stdout.write(f'Застрявшие после mixer_mix_meat_end: {stuck_after_mixer_end.count()}')
        
        stuck_on_palletizing = MincedMeatBatchMix.objects.filter(
            statuses__status__codename='palletizing'
        ).exclude(
            statuses__status__codename__in=['palletizing_end', 'pallet_is_set']
        )
        self.stdout.write(f'Застрявшие на паллетировании: {stuck_on_palletizing.count()}')
        
        stuck_on_unload_shocker = MincedMeatBatchMix.objects.filter(
            statuses__status__codename='unload_shocker_finish'
        ).exclude(
            statuses__status__codename__in=['palletizing', 'palletizing_end', 'pallet_is_set']
        )
        self.stdout.write(f'Застрявшие после выгрузки из шокера: {stuck_on_unload_shocker.count()}')
        
        # 4. Анализ причин застревания
        self.stdout.write(self.style.WARNING('\n=== АНАЛИЗ ПРИЧИН ЗАСТРЕВАНИЯ ==='))
        
        # Проверяем периодические задачи
        self.stdout.write('Возможные причины застревания:')
        self.stdout.write('1. Периодические задачи (APScheduler) не работают или работают некорректно')
        self.stdout.write('2. Условия в check_prev_status() не выполняются')
        self.stdout.write('3. Ошибки в логике переходов между статусами')
        self.stdout.write('4. Проблемы с уведомлениями (notify=True блокирует переходы)')
        self.stdout.write('5. Отсутствие необходимых статусов в базе данных')
        
        # 5. Рекомендации по исправлению
        self.stdout.write(self.style.WARNING('\n=== РЕКОМЕНДАЦИИ ==='))
        
        if blanks_without_status.exists() or stuck_on_output.exists() or stuck_on_defrosting.exists():
            self.stdout.write('Для заготовок:')
            self.stdout.write('  python manage.py fix_meat_blank_statuses --dry-run')
            self.stdout.write('  python manage.py fix_meat_blank_statuses')
        
        if mixes_without_status.exists() or stuck_after_mixer_end.exists() or stuck_on_palletizing.exists() or stuck_on_unload_shocker.exists():
            self.stdout.write('Для замесов:')
            self.stdout.write('  python manage.py fix_mix_statuses --dry-run')
            self.stdout.write('  python manage.py fix_mix_statuses')
        
        # 6. Проверка целостности данных
        self.stdout.write(self.style.WARNING('\n=== ПРОВЕРКА ЦЕЛОСТНОСТИ ==='))
        
        # Проверяем наличие всех необходимых статусов
        required_statuses = [
            'defrosting', 'to_defroster', 'loaded_to_defroster', 'unloaded_from_defroster',
            'storekeeper_output', 'storekeeper_outputed', 'rastarshik_unload_meat_blank',
            'press_operator_mix_meat', 'press_operator_mix_meat_end', 'mixer_mix_meat',
            'mixer_mix_meat_end', 'mixer_tiller_mix_meat', 'mixer_tiller_mix_meat_end',
            'unloaded_to_packer', 'unloaded_to_packer_end', 'to_shocker', 'to_shocker_finish',
            'unload_shocker', 'unload_shocker_finish', 'palletizing', 'palletizing_end',
            'pallet_is_set', 'work_is_finished'
        ]
        
        missing_statuses = []
        for status_codename in required_statuses:
            if not Status.objects.filter(codename=status_codename).exists():
                missing_statuses.append(status_codename)
        
        if missing_statuses:
            self.stdout.write(f'Отсутствующие статусы: {missing_statuses}')
            self.stdout.write('Выполните: python manage.py load_initial_data')
        else:
            self.stdout.write('Все необходимые статусы присутствуют в базе данных')
        
        # 7. Детальная информация если запрошена
        if detailed:
            self.stdout.write(self.style.WARNING('\n=== ДЕТАЛЬНАЯ ИНФОРМАЦИЯ ==='))
            
            if blanks_without_status.exists():
                self.stdout.write('Заготовки без статусов:')
                for blank in blanks_without_status[:10]:  # Показываем первые 10
                    self.stdout.write(f'  - ID: {blank.id}, Создана: {blank.created_at}')
            
            if stuck_after_mixer_end.exists():
                self.stdout.write('Замесы застрявшие после mixer_mix_meat_end:')
                for mix in stuck_after_mixer_end[:10]:  # Показываем первые 10
                    statuses = mix.statuses.all().values_list('status__codename', flat=True)
                    self.stdout.write(f'  - ID: {mix.id}, Партия: {mix.minced_meat_batch_id}, Статусы: {list(statuses)}')
        
        self.stdout.write(self.style.SUCCESS('\nДиагностика завершена'))

