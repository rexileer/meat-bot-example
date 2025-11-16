import asyncio
import logging
import os

import django

from bot import middlewares
from bot.loader import dp, scheduler
from bot.utils.notify_admins import on_startup_notify
from bot.utils.set_bot_commands import set_default_commands


async def on_startup(dp):

    middlewares.setup(dp)
    await on_startup_notify(dp)
    await set_default_commands(dp)


def setup_django():
    os.environ["DJANGO_SETTINGS_MODULE"] = "Web.web.settings"
    os.environ.update({"DJANGO_ALLOW_ASYNC_UNSAFE": "true"})
    django.setup()


async def django_start():
    from bot.handlers.storekeeper.utils.storekeeper_check_status import check_work_storekeeper

    scheduler.add_job(check_work_storekeeper, "interval", seconds=4, max_instances=20)
    from bot.handlers.rastarshik.utils.rastarshik_check_status import check_work_rastarshik

    scheduler.add_job(check_work_rastarshik, "interval", seconds=4, max_instances=20)
    from bot.handlers.press_operator.utils.press_operatos_check_status import check_work_press_operator

    scheduler.add_job(check_work_press_operator, "interval", seconds=4, max_instances=20)
    from bot.handlers.mixer.utils.mixer_check_status import check_work_mixer

    scheduler.add_job(check_work_mixer, "interval", seconds=4, max_instances=20)
    from bot.handlers.packer.utils.packer_check_status import check_work_packer

    scheduler.add_job(check_work_packer, "interval", seconds=4, max_instances=20)
    logging.getLogger("apscheduler.executors.default").propagate = False
    logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)

    scheduler.start()

    import bot.handlers

    # await executor.start_polling(dp, on_startup=on_startup, loop=loop)
    middlewares.setup(dp)
    await on_startup_notify(dp)
    await set_default_commands(dp)
    await dp.start_polling(bot)
    print("EXITTED")


if __name__ == "__main__":
    setup_django()
    asyncio.run(django_start())
