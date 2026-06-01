import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import uvicorn

from bot import bot
from config import SUB_PAGE_API_KEY, WEB_API_PORT, JWT_SECRET
from config_bd.models import create_tables
from web_api import app as subpage_app
from payments import pay_stars, pay_cryptobot, pay_platega, pay_freekassa, pay_youkassa
# from payments import pay_wata
from sheduler.check_connect import check_connect
from sheduler.check_cryptobot import check_cryptobot_payments
from sheduler.check_online import check_online_daily
from sheduler.check_platega import check_platega, check_platega_card, check_platega_crypto
from sheduler.check_fk import check_fk
from sheduler.check_youkassa import check_youkassa_payments
from sheduler.check_wata_sbp import check_wata_sbp
from sheduler.check_wata_card import check_wata_card
from handlers import handlers_user, handlers_statistic, handlers_admin, handlers_broadcast, handlers_export, handlers_import
from sheduler.time_mes import send_message_cron
from logging_config import logger
from sheduler.time_mes_not_sub import send_push_cron


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command='/start', description='Запустить бота')
    ]
    await bot.set_my_commands(commands)

# Функция конфигурирования и запуска бота
async def main() -> None:
    await create_tables()

    # Инициализация диспетчера
    dp: Dispatcher = Dispatcher()
    dp.include_router(handlers_broadcast.router)
    dp.include_router(handlers_admin.router)
    dp.include_router(handlers_import.router)
    dp.include_router(handlers_user.router)
    dp.include_router(handlers_export.router)
    dp.include_router(handlers_statistic.router)
    # dp.include_router(pay_platega.router)
    # dp.include_router(pay_wata.router)
    dp.include_router(pay_freekassa.router)
    dp.include_router(pay_youkassa.router)
    dp.include_router(pay_stars.router)
    dp.include_router(pay_cryptobot.router)

    # Запуск шедулера
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(send_message_cron, trigger='interval', minutes=10, args=[bot], misfire_grace_time=120)
    scheduler.add_job(check_connect, trigger='interval', minutes=14, misfire_grace_time=60)
    # scheduler.add_job(check_platega, trigger='interval', minutes=1, misfire_grace_time=10)
    # scheduler.add_job(check_platega_card, trigger='interval', minutes=1, misfire_grace_time=10)
    # scheduler.add_job(check_platega_crypto, trigger='interval', minutes=1, misfire_grace_time=10)
    scheduler.add_job(check_fk, trigger='interval', minutes=1, misfire_grace_time=10)
    scheduler.add_job(check_youkassa_payments, trigger='interval', minutes=1, misfire_grace_time=10)
    scheduler.add_job(check_wata_sbp, trigger='interval', minutes=1, misfire_grace_time=10)
    scheduler.add_job(check_wata_card, trigger='interval', minutes=1, misfire_grace_time=10)
    scheduler.add_job(check_cryptobot_payments, trigger='interval', minutes=1, misfire_grace_time=10)
    scheduler.add_job(send_push_cron, trigger='interval', minutes=30, misfire_grace_time=60)
    scheduler.add_job(check_online_daily, 'cron', hour=2, minute=55, id='daily_online_stats', misfire_grace_time=60)
    scheduler.start()

    await set_commands(bot)

    api_task: asyncio.Task | None = None
    api_server: uvicorn.Server | None = None
    if SUB_PAGE_API_KEY or JWT_SECRET:
        uvicorn_config = uvicorn.Config(
            subpage_app,
            host="0.0.0.0",
            port=WEB_API_PORT,
            log_level="info",
        )
        api_server = uvicorn.Server(uvicorn_config)
        api_task = asyncio.create_task(api_server.serve())
        logger.info(f"Web API: http://0.0.0.0:{WEB_API_PORT}/api/...")
    else:
        logger.info("SUB_PAGE_API_KEY и JWT_SECRET не заданы — HTTP API не запускается.")

    try:
        # Пропуск накопившихся апдейтов и запуск polling
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot start polling.")
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        logger.error("Polling was cancelled. Cleaning up...")
    finally:
        if api_server is not None:
            api_server.should_exit = True
        if api_task is not None:
            api_task.cancel()
            try:
                await api_task
            except asyncio.CancelledError:
                pass
        await bot.session.close()
        logger.info("Bot session closed.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually.")
