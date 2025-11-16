from django.core.management.base import BaseCommand
from Web.CRM.models import MeatBlank, MeatBlankStatus, MincedMeatBatchMix, MincedMeatBatchStatus, Status


class Command(BaseCommand):
    help = 'Анализ причин застревания статусов'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== АНАЛИЗ ПРИЧИН ЗАСТРЕВАНИЯ СТАТУСОВ ===\n'))
        
        # 1. Анализ потока заготовок
        self.stdout.write(self.style.WARNING('=== ПОТОК ЗАГОТОВОК ==='))
        self.stdout.write('Ожидаемый поток:')
        self.stdout.write('1. Создание заготовки (без статуса)')
        self.stdout.write('2. storekeeper_output (ввод веса)')
        self.stdout.write('3. storekeeper_outputed (завершение ввода веса)')
        self.stdout.write('4. rastarshik_unload_meat_blank (растарка)')
        self.stdout.write('5. rastarshik_unload_meat_blank_end (завершение растарки)')
        self.stdout.write('6. defrosting (дефрост)')
        self.stdout.write('7. to_defroster (загрузка в дефростер)')
        self.stdout.write('8. loaded_to_defroster (загружено в дефростер)')
        self.stdout.write('9. unloaded_from_defroster (выгружено из дефростера)')
        
        # Проверяем заготовки без статусов
        blanks_without_status = MeatBlank.objects.filter(statuses__isnull=True)
        self.stdout.write(f'\nПроблема 1: Заготовки без статусов: {blanks_without_status.count()}')
        self.stdout.write('Причина: check_work_storekeeper() не срабатывает для новых заготовок')
        self.stdout.write('Условие: check_prev_status() должно возвращать True')
        
        # Проверяем застрявшие на storekeeper_output
        stuck_on_output = MeatBlank.objects.filter(
            statuses__status__codename='storekeeper_output'
        ).exclude(
            statuses__status__codename='storekeeper_outputed'
        )
        self.stdout.write(f'\nПроблема 2: Застрявшие на вводе веса: {stuck_on_output.count()}')
        self.stdout.write('Причина: Пользователь не завершил ввод веса через бота')
        self.stdout.write('Решение: Автоматически добавлять storekeeper_outputed через 24 часа')
        
        # 2. Анализ потока замесов
        self.stdout.write(self.style.WARNING('\n=== ПОТОК ЗАМЕСОВ ==='))
        self.stdout.write('Ожидаемый поток:')
        self.stdout.write('1. Создание замеса (без статуса)')
        self.stdout.write('2. press_operator_mix_meat (сепарация)')
        self.stdout.write('3. press_operator_mix_meat_end (завершение сепарации)')
        self.stdout.write('4. mixer_mix_meat (перемешивание и анализ)')
        self.stdout.write('5. mixer_mix_meat_end (завершение перемешивания)')
        self.stdout.write('6. mixer_tiller_mix_meat (загрузка в плиточник)')
        self.stdout.write('7. mixer_tiller_mix_meat_end (загрузка в плиточник завершена)')
        self.stdout.write('8. unloaded_to_packer (выгрузка из плиточника)')
        self.stdout.write('9. unloaded_to_packer_end (выгрузка из плиточника завершена)')
        self.stdout.write('10. to_shocker (загрузка в шокер)')
        self.stdout.write('11. to_shocker_finish (загрузка в шокер завершена)')
        self.stdout.write('12. unload_shocker (выгрузка из шокера)')
        self.stdout.write('13. unload_shocker_finish (выгрузка из шокера завершена)')
        self.stdout.write('14. palletizing (паллетирование)')
        self.stdout.write('15. palletizing_end (паллетирование завершено)')
        self.stdout.write('16. work_is_finished (работа завершена)')
        
        # Проверяем замесы без статусов
        mixes_without_status = MincedMeatBatchMix.objects.filter(statuses__isnull=True)
        self.stdout.write(f'\nПроблема 3: Замесы без статусов: {mixes_without_status.count()}')
        self.stdout.write('Причина: check_work_rastarshik() не срабатывает для новых замесов')
        self.stdout.write('Условие: Замесы должны быть в списке mixes в check_work_rastarshik()')
        
        # Проверяем застрявшие после mixer_mix_meat_end
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
        self.stdout.write(f'\nПроблема 4: Застрявшие после mixer_mix_meat_end: {stuck_after_mixer_end.count()}')
        self.stdout.write('Причина: check_work_packer() не срабатывает')
        self.stdout.write('Условие: Должно пройти 10 секунд после mixer_mix_meat_end')
        self.stdout.write('Проблема: check_last_status_packer() может возвращать False')
        
        # 3. Анализ условий в check_prev_status()
        self.stdout.write(self.style.WARNING('\n=== АНАЛИЗ УСЛОВИЙ В check_prev_status() ==='))
        
        meat_blanks = MeatBlankStatus.objects.filter(status__codename="storekeeper_output").count()
        meat_blanks_finished = MeatBlankStatus.objects.filter(status__codename="storekeeper_outputed").count()
        mix_palleting = MincedMeatBatchMix.objects.filter(statuses__status__codename="palletizing").count()
        mix_palleting_finished = MincedMeatBatchMix.objects.filter(statuses__status__codename="palletizing_end").count()
        
        self.stdout.write(f'storekeeper_output: {meat_blanks}')
        self.stdout.write(f'storekeeper_outputed: {meat_blanks_finished}')
        self.stdout.write(f'palletizing: {mix_palleting}')
        self.stdout.write(f'palletizing_end: {mix_palleting_finished}')
        
        check_result = (meat_blanks_finished == meat_blanks and mix_palleting == mix_palleting_finished)
        self.stdout.write(f'check_prev_status() результат: {check_result}')
        
        if not check_result:
            self.stdout.write('ПРОБЛЕМА: check_prev_status() возвращает False')
            if meat_blanks != meat_blanks_finished:
                self.stdout.write(f'  - Неравенство в заготовках: {meat_blanks} != {meat_blanks_finished}')
            if mix_palleting != mix_palleting_finished:
                self.stdout.write(f'  - Неравенство в замесах: {mix_palleting} != {mix_palleting_finished}')
        
        # 4. Анализ периодических задач
        self.stdout.write(self.style.WARNING('\n=== АНАЛИЗ ПЕРИОДИЧЕСКИХ ЗАДАЧ ==='))
        self.stdout.write('Периодические задачи запускаются каждые 4 секунды:')
        self.stdout.write('1. check_work_storekeeper() - для заготовок и замесов')
        self.stdout.write('2. check_work_rastarshik() - для заготовок и новых замесов')
        self.stdout.write('3. check_work_press_operator() - для замесов')
        self.stdout.write('4. check_work_mixer() - для замесов')
        self.stdout.write('5. check_work_packer() - для замесов')
        
        self.stdout.write('\nПроблемы:')
        self.stdout.write('- Если одна задача зависает, остальные могут не сработать')
        self.stdout.write('- Условия в check_prev_status() могут блокировать все задачи')
        self.stdout.write('- Ошибки в коде могут прерывать выполнение задач')
        
        # 5. Рекомендации по исправлению
        self.stdout.write(self.style.WARNING('\n=== РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ ==='))
        
        self.stdout.write('1. НЕМЕДЛЕННЫЕ ИСПРАВЛЕНИЯ:')
        self.stdout.write('   - Запустить команды диагностики и исправления')
        self.stdout.write('   - Проверить работу периодических задач')
        
        self.stdout.write('\n2. СТРУКТУРНЫЕ ИЗМЕНЕНИЯ:')
        self.stdout.write('   - Добавить логирование в периодические задачи')
        self.stdout.write('   - Упростить условия в check_prev_status()')
        self.stdout.write('   - Добавить таймауты для застрявших статусов')
        self.stdout.write('   - Создать мониторинг статусов')
        
        self.stdout.write('\n3. ПРЕВЕНТИВНЫЕ МЕРЫ:')
        self.stdout.write('   - Добавить автоматическое исправление застрявших статусов')
        self.stdout.write('   - Создать алерты при застревании')
        self.stdout.write('   - Добавить ручные команды для принудительного перехода статусов')
        
        self.stdout.write(self.style.SUCCESS('\nАнализ завершен'))

