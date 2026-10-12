"""
Main Entry Point for Be'minnat Telegram Bot (aiogram 3)
Supports both Polling (local dev) and Webhook (production)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from app.config import settings
from app.handlers import (
    start,
    publish,
    search,
    requests as req_handlers,
    my_items,
    favorites,
    profile,
    help as help_handlers
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("beminnat_bot")

def setup_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    # Register routers in priority order
    dp.include_router(start.router)
    dp.include_router(publish.router)
    dp.include_router(search.router)
    dp.include_router(req_handlers.router)
    dp.include_router(my_items.router)
    dp.include_router(favorites.router)
    dp.include_router(profile.router)
    dp.include_router(help_handlers.router)
    return dp

async def on_startup(bot: Bot):
    logger.info("Bot starting up...")
    if settings.USE_WEBHOOK:
        webhook_url = f"{settings.WEBHOOK_HOST}{settings.WEBHOOK_PATH}"
        logger.info(f"Setting webhook to: {webhook_url}")
        await bot.set_webhook(
            url=webhook_url,
            secret_token=settings.WEBHOOK_SECRET,
            drop_pending_updates=True
        )

async def on_shutdown(bot: Bot):
    logger.info("Bot shutting down...")
    if settings.USE_WEBHOOK:
        await bot.delete_webhook()

def main():
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = setup_dispatcher()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    if settings.USE_WEBHOOK:
        logger.info(f"Running in WEBHOOK mode on port {settings.PORT}")
        app = web.Application()

        # Health check endpoint for Railway/Render
        async def health_check(request):
            return web.Response(text="OK", content_type="text/plain")

        app.router.add_get("/health", health_check)
        app.router.add_get("/", health_check)

        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
            secret_token=settings.WEBHOOK_SECRET
        )
        webhook_requests_handler.register(app, path=settings.WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
        web.run_app(app, host="0.0.0.0", port=settings.PORT)
    else:
        logger.info("Running in POLLING mode (development)")
        import asyncio
        asyncio.run(dp.start_polling(bot))

if __name__ == "__main__":
    main()
