import logging
import os
import sys

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")
TARGET_CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID")


def load_config():
    if not BOT_TOKEN or not OWNER_ID or not TARGET_CHANNEL_ID:
        logger.error(
            "Env vars BOT_TOKEN, OWNER_ID, TARGET_CHANNEL_ID are required"
        )
        sys.exit(1)

    try:
        owner_id_int = int(OWNER_ID)
    except ValueError:
        logger.error("OWNER_ID must be integer (Telegram user id)")
        sys.exit(1)

    return BOT_TOKEN, owner_id_int, TARGET_CHANNEL_ID


BOT_TOKEN, OWNER_ID_INT, TARGET_CHANNEL_ID = load_config()


def is_allowed(update: Update) -> bool:
    """Проверка, что пишет именно владелец и в личку."""
    user = update.effective_user
    chat = update.effective_chat

    if user is None or chat is None:
        return False

    if user.id != OWNER_ID_INT:
        logger.warning(
            "Got message from unauthorized user %s (%s)",
            user.id,
            user.username,
        )
        return False

    if chat.type != "private":
        logger.info("Ignoring non-private chat message: %s", chat.id)
        return False

    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return

    await update.message.reply_text(
        "Привет! 👋\n\n"
        "Просто перешли мне пост из любого канала с фото или видео, "
        "а я выложу медиа в твой канал."
    )


async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return

    msg = update.effective_message

    extra_kwargs = {}

    if msg.photo:
        # photo — список размеров, последний обычно самый крупный
        photo = msg.photo[-1]
        await context.bot.send_photo(
            chat_id=TARGET_CHANNEL_ID,
            photo=photo.file_id,
            **extra_kwargs,
        )
        await msg.reply_text("✅ Фото отправлено в канал.")
        logger.info(
            "Photo from user %s forwarded to %s", msg.from_user.id, TARGET_CHANNEL_ID
        )
    elif msg.video:
        video = msg.video
        await context.bot.send_video(
            chat_id=TARGET_CHANNEL_ID,
            video=video.file_id,
            **extra_kwargs,
        )
        await msg.reply_text("✅ Видео отправлено в канал.")
        logger.info(
            "Video from user %s forwarded to %s", msg.from_user.id, TARGET_CHANNEL_ID
        )
    else:
        # По идее сюда не попадём, т.к. хэндлер висит только на PHOTO|VIDEO,
        # но оставим на всякий случай.
        await msg.reply_text("В этом сообщении нет ни фото, ни видео 🤷‍♂️")


async def handle_other(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return

    await update.message.reply_text(
        "Я вижу сообщение, но в нём нет фото или видео.\n"
        "Перешли мне пост из канала с медиа (фото/видео)."
    )


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    # /start
    application.add_handler(CommandHandler("start", start))

    # Медиа от владельца в личке
    media_filter = (filters.PHOTO | filters.VIDEO) & filters.ChatType.PRIVATE
    application.add_handler(MessageHandler(media_filter, handle_media))

    # Остальные сообщения от владельца в личке
    application.add_handler(
        MessageHandler(filters.ChatType.PRIVATE, handle_other)
    )

    # Можно сузить типы апдейтов для экономии
    application.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
