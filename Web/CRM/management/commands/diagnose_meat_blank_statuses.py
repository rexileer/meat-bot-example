from django.core.management.base import BaseCommand
from Web.CRM.models import MeatBlank, MeatBlankStatus, Status


class Command(BaseCommand):
    help = 'Диагностика проблем со статусами заготовок'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Показать детальную информацию о каждой заготовке',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== ДИАГНОСТИКА СТАТУСОВ ЗАГОТОВОК ===\n'))
        
        # 1. Заготовки без статусов
        blanks_without_status = MeatBlank.objects.filter(statuses__isnull=True)
        self.stdout.write(f'Заготовки без статусов: {blanks_without_status.count()}')
        if options['detailed'] and blanks_without_status.exists():
            for blank in blanks_without_status:
                self.stdout.write(f'  - ID: {blank.id}, Создана: {blank.created_at}')
        
        # 2. Заготовки с пустыми стадиями обработки (только created)
        blanks_only_created = MeatBlank.objects.filter(
            statuses__isnull=False
        ).exclude(
            statuses__status__codename__in=[
                'defrosting', 'to_defroster', 'loaded_to_defroster', 
                'unloaded_from_defroster', 'storekeeper_output', 'storekeeper_outputed'
            ]
        )
        self.stdout.write(f'Заготовки с пустыми стадиями: {blanks_only_created.count()}')
        if options['detailed'] and blanks_only_created.exists():
            for blank in blanks_only_created:
                statuses = blank.statuses.all().values_list('status__codename', flat=True)
                self.stdout.write(f'  - ID: {blank.id}, Статусы: {list(statuses)}')
        
        # 3. Заготовки застрявшие на storekeeper_output
        stuck_on_output = MeatBlank.objects.filter(
            statuses__status__codename='storekeeper_output'
        ).exclude(
            statuses__status__codename='storekeeper_outputed'
        )
        self.stdout.write(f'Заготовки застрявшие на вводе веса: {stuck_on_output.count()}')
        if options['detailed'] and stuck_on_output.exists():
            for blank in stuck_on_output:
                self.stdout.write(f'  - ID: {blank.id}, Создана: {blank.created_at}')
        
        # 4. Заготовки застрявшие на defrosting
        stuck_on_defrosting = MeatBlank.objects.filter(
            statuses__status__codename='defrosting'
        ).exclude(
            statuses__status__codename__in=['to_defroster', 'loaded_to_defroster']
        )
        self.stdout.write(f'Заготовки застрявшие на дефросте: {stuck_on_defrosting.count()}')
        
        # 5. Статистика по всем статусам заготовок
        self.stdout.write('\n=== СТАТИСТИКА ПО СТАТУСАМ ===')
        status_counts = {}
        for status in Status.objects.filter(meatblankstatus__isnull=False).distinct():
            count = MeatBlankStatus.objects.filter(status=status).count()
            status_counts[status.codename] = count
            self.stdout.write(f'{status.codename}: {count}')
        
        # 6. Проблемные заготовки (созданы, но не прошли базовый поток)
        problematic_blanks = MeatBlank.objects.filter(
            statuses__isnull=False
        ).exclude(
            statuses__status__codename__in=[
                'defrosting', 'to_defroster', 'loaded_to_defroster', 
                'unloaded_from_defroster', 'storekeeper_output', 'storekeeper_outputed',
                'rastarshik_unload_meat_blank', 'rastarshik_unload_meat_blank_end'
            ]
        )
        self.stdout.write(f'\nПроблемные заготовки (не в основном потоке): {problematic_blanks.count()}')
        
        if problematic_blanks.exists():
            self.stdout.write('Рекомендуется выполнить: python manage.py fix_meat_blank_statuses')
        
        self.stdout.write(self.style.SUCCESS('\nДиагностика завершена'))

