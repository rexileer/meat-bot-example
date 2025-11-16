from django.core.management.base import BaseCommand
from Web.CRM.models import MeatBlank, MeatBlankStatus, Status


class Command(BaseCommand):
    help = 'Исправление застрявших статусов заготовок'

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
        
        self.stdout.write(self.style.SUCCESS('=== ИСПРАВЛЕНИЕ СТАТУСОВ ЗАГОТОВОК ===\n'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('РЕЖИМ ПРОСМОТРА - изменения не будут внесены\n'))
        
        # 1. Заготовки без статусов - добавить defrosting
        blanks_without_status = MeatBlank.objects.filter(statuses__isnull=True)
        if blanks_without_status.exists():
            self.stdout.write(f'Найдено заготовок без статусов: {blanks_without_status.count()}')
            if not dry_run:
                defrosting_status = Status.objects.get(codename='defrosting')
                for blank in blanks_without_status:
                    MeatBlankStatus.objects.create(
                        meat_blank=blank,
                        status=defrosting_status,
                        notify=True
                    )
                self.stdout.write(self.style.SUCCESS(f'Добавлен статус "defrosting" для {blanks_without_status.count()} заготовок'))
            else:
                for blank in blanks_without_status:
                    self.stdout.write(f'  - ID: {blank.id} -> добавить статус "defrosting"')
        
        # 2. Заготовки застрявшие на storekeeper_output - добавить storekeeper_outputed
        stuck_on_output = MeatBlank.objects.filter(
            statuses__status__codename='storekeeper_output'
        ).exclude(
            statuses__status__codename='storekeeper_outputed'
        )
        if stuck_on_output.exists():
            self.stdout.write(f'Найдено заготовок застрявших на вводе веса: {stuck_on_output.count()}')
            if not dry_run:
                outputed_status = Status.objects.get(codename='storekeeper_outputed')
                for blank in stuck_on_output:
                    MeatBlankStatus.objects.create(
                        meat_blank=blank,
                        status=outputed_status,
                        notify=False
                    )
                self.stdout.write(self.style.SUCCESS(f'Добавлен статус "storekeeper_outputed" для {stuck_on_output.count()} заготовок'))
            else:
                for blank in stuck_on_output:
                    self.stdout.write(f'  - ID: {blank.id} -> добавить статус "storekeeper_outputed"')
        
        # 3. Заготовки застрявшие на defrosting - добавить to_defroster
        stuck_on_defrosting = MeatBlank.objects.filter(
            statuses__status__codename='defrosting'
        ).exclude(
            statuses__status__codename__in=['to_defroster', 'loaded_to_defroster']
        )
        if stuck_on_defrosting.exists():
            self.stdout.write(f'Найдено заготовок застрявших на дефросте: {stuck_on_defrosting.count()}')
            if not dry_run:
                to_defroster_status = Status.objects.get(codename='to_defroster')
                for blank in stuck_on_defrosting:
                    MeatBlankStatus.objects.create(
                        meat_blank=blank,
                        status=to_defroster_status,
                        notify=True
                    )
                self.stdout.write(self.style.SUCCESS(f'Добавлен статус "to_defroster" для {stuck_on_defrosting.count()} заготовок'))
            else:
                for blank in stuck_on_defrosting:
                    self.stdout.write(f'  - ID: {blank.id} -> добавить статус "to_defroster"')
        
        # 4. Заготовки с пустыми стадиями - сбросить к defrosting
        if force:
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
                self.stdout.write(f'Найдено проблемных заготовок (сброс к defrosting): {problematic_blanks.count()}')
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
                    self.stdout.write(self.style.SUCCESS(f'Сброшены статусы для {problematic_blanks.count()} заготовок'))
                else:
                    for blank in problematic_blanks:
                        self.stdout.write(f'  - ID: {blank.id} -> сбросить к статусу "defrosting"')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nДля применения изменений запустите команду без --dry-run'))
        else:
            self.stdout.write(self.style.SUCCESS('\nИсправление завершено'))

