import logging
import asyncio
import configparser
import time
from pyrogram import Client, filters, idle, emoji
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger(__name__)

configuration_file = "config.ini"
config = configparser.ConfigParser()
config.read(configuration_file)


token = config.get("bot", "token")
admin_group = int(config.get("bot", "admin_group"))
dest_chan = int(config.get("bot", "dest_chan"))
api_id = config.get("pyrogram", "api_id")
api_hash = config.get("pyrogram", "api_hash")

review_rep_resp = "As a reply to this message send me the final confession to be posted."

bot = Client(
    "UnijaBesutConfession_chatbot",
    workers=200,
    workdir="working_dir",
    bot_token=token,
    api_id=api_id,
    api_hash=api_hash
)

confession_submission_allowed = {}
admin_requests = {}

@bot.on_message(filters.command("start"))
async def start_command_handler(_, m: Message):
    user_id = m.from_user.id
    confession_submission_allowed[user_id] = True
    await m.reply_text(
        "😊😊Hello there, 😊😊 Anda boleh share apa²  confession or anything di bot ini. Apa yang anda kongsi akan di'share' on UniSZA Besut KONfession Channel\n"
        "\n"
        "👉 Sent text tu, HANYA 1 MESSAGE SAHAJA DIBENARKAN atau SERTAKAN CAPTION SEKALI DENGAN GAMBAR . Tak kisah la panjang berjela sekalipun  (kalau lebih dari 1, message ke-2 dan seterusnya akan diabaikan)\n"
        "\n"
        "👉 Privasi anda adalah satu keutamaan!! To protext your privacy and identity, PLEASE disable link forwarding messages to your account.\n"
        "\n"
        "You can send your confession now‼️"
    )

@bot.on_message(filters.command("channel"))
async def channel_command_handler(_, m: Message):
    user_id = m.from_user.id
    channel_invite_link = "https://t.me/+lMqkbLyl78phNDdl"  # Replace with your actual channel invite link

    await m.reply_text(
        f"Here is the invite link to UniSZA Besut Confession Channel: {channel_invite_link}"
    )

@bot.on_message(filters.command("admin"))
async def admin_command_handler(_, m: Message):
    user_id = m.from_user.id
    admin_requests[user_id] = True

    await m.reply_text(
        "You are now in admin message forwarding mode.\n"
        "Send the message you want to forward to the admin.\n"
        "\n"
        "The admin will read your message but won't respond directly to you.\n"
        "\n"
        "Feel free to leave your message for the admin's review, and if necessary, the admin will contact you privately.\n"
        "\n"
        "To stop, send /stop_admin"
    )


@bot.on_message(filters.command("stop_admin"))
async def stop_admin_command_handler(_, m: Message):
    user_id = m.from_user.id
    admin_requests[user_id] = False

    await m.reply_text(
        "You have stopped the admin message forwarding mode. "
        "If you want to chat with admin again, send /admin."
    )

@bot.on_message(filters.private)
async def new_confessions_handler(_, m: Message):
    user_id = m.from_user.id

    if user_id in confession_submission_allowed and confession_submission_allowed[user_id]:
        # User is allowed to submit a confession
        if m.text:  # If it's a text message, we copy
            copied_msg = await m.copy(admin_group)  # Copy text message
            fd_msg = copied_msg  # Assign copied_msg to fd_msg to maintain consistency
        else:  # For media or other types of messages, we forward
            forwarded_msg = await m.forward(admin_group)  # Forward media or other types of messages
            fd_msg = forwarded_msg  # Assign forwarded_msg to fd_msg to maintain consistency
        await fd_msg.reply_text(
            f"<i>Confession by user</i>",
            reply_to_message_id=fd_msg.id,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text=f"{emoji.MEMO} Review", callback_data="review"),
                        InlineKeyboardButton(text=f"{emoji.CHECK_MARK} Approve", callback_data="approve")
                    ]
                ]
            )
        )
        # Set the user's submission flag to False, preventing further submissions
        confession_submission_allowed[user_id] = False
        await m.reply_text("Alright👍, your message sudah diterima for review. dan tunggu your turn untuk dipost ke dalam channel https://t.me/+lMqkbLyl78phNDdl nanti ☺️☺️☺️\n"
                          "\n"
                          "‼️AMARAN‼️ ▶️ KALAU DAH SENT, MOHON JANGAN SPAM BANYAK KALI .. - jangan sampai admin BAN you ye \n"
                          "\n"
                          "▶️ Dan juga kalau you sent message TIDAK MENGIKUT PERATURAN DITETAPKAN, jangan marah juga ye kalau tak foward ke channel. (jangan persoalkan admin)\n"
                          "\n"
                          "If you want to submit another confession, please send /start.\n")
    elif user_id in admin_requests and admin_requests[user_id]:
        # User is in admin message forwarding mode
        await m.forward(admin_group)
        await m.reply_text("Your message has been forwarded to the admin. To stop, send /stop_admin.")
    else:
        await m.reply_text("To submit another confession, please send /start.\n"
                           "To view confession channel link, please send /channel\n"
                           "To chat with admin, please send /admin\n")



@bot.on_callback_query(filters.regex("review"))
async def review_callback_handler(_, cb: CallbackQuery):
    await cb.answer()
    await cb.message.edit_reply_markup()
    await cb.message.reply_text(
        review_rep_resp
    )


@bot.on_callback_query(filters.regex("approve"))
async def approve_callback_handler(_, cb: CallbackQuery):
    await cb.message.reply_to_message.copy(dest_chan)
    await cb.edit_message_reply_markup()
    await cb.answer("Confession has been posted!", show_alert=True)


@bot.on_message(filters.reply & filters.chat(admin_group))
async def review_reply_handler(_, m: Message):
    if m.reply_to_message.text == review_rep_resp:
        await m.copy(dest_chan)
        await m.reply_to_message.edit_text(
            "<i>This confession has been reviewed and Posted!</i>"
        )

async def sync_time():
    try:
        await bot.invoke(Ping(ping_id=0))  # Sends a ping to sync time with the server
        logging.info("Time synchronized with Telegram server.")
    except Exception as e:
        logging.error(f"Time synchronization failed: {e}")

async def main():
    try:
        await bot.start()
        await sync_time()  # Immediately sync time after starting
        await idle()
    except Exception as e:
        logging.error(f"Error while starting bot: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
