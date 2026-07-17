import asyncio
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
import db
from sources import coingecko, dexscreener

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Each entry: (fetch_fn, format_fn)
SOURCES = [
    (coingecko.fetch_new_coins, coingecko.format_message),
    (dexscreener.fetch_new_tokens, dexscreener.format_message),
]


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.add_subscriber(update.effective_chat.id)
    await update.message.reply_text(
        "You're subscribed! You'll get DMs whenever new coins/tokens launch.\n"
        "Use /stop to unsubscribe."
    )


async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.remove_subscriber(update.effective_chat.id)
    await update.message.reply_text("You're unsubscribed. Use /start to rejoin anytime.")


async def broadcast(app: Application, text: str):
    # 1. Post to the owned channel
    if config.CHANNEL_ID:
        try:
            await app.bot.send_message(
                chat_id=config.CHANNEL_ID, text=text, parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to post to channel: {e}")

    # 2. DM every subscriber
    for chat_id in db.get_subscribers():
        try:
            await app.bot.send_message(
                chat_id=chat_id, text=text, parse_mode=ParseMode.HTML
            )
        except Exception as e:
            # e.g. user blocked the bot -- drop them silently
            logger.warning(f"Failed to DM {chat_id}: {e}")
            db.remove_subscriber(chat_id)


async def poll_sources(app: Application):
    for fetch_fn, format_fn in SOURCES:
        source_name = fetch_fn.__module__.split(".")[-1]
        try:
            items = await fetch_fn()
        except Exception as e:
            logger.error(f"Error fetching {source_name}: {e}")
            continue

        new_count = 0
        for item in items:
            if db.is_seen(item["source"], item["item_id"]):
                continue
            db.mark_seen(item["source"], item["item_id"])
            new_count += 1
            await broadcast(app, format_fn(item))

        logger.info(f"[{source_name}] checked {len(items)} items, {new_count} new")


def main():
    db.init_db()

    app = Application.builder().token(config.BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        poll_sources,
        "interval",
        minutes=config.POLL_INTERVAL_MINUTES,
        args=[app],
        next_run_time=None,
    )

    async def start_scheduler(_app):
        scheduler.start()
        # kick off one immediate poll on startup
        asyncio.create_task(poll_sources(_app))

    app.post_init = start_scheduler

    logger.info("Bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
