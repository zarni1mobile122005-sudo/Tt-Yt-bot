import logging
import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# States
PLATFORM, FORMAT_TYPE, GET_LINK = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎵 TikTok", callback_data='tiktok'),
         InlineKeyboardButton("📺 YouTube", callback_data='youtube')]
    ]
    await update.message.reply_text("👋 မင်္ဂလာပါ! မီဒီယာများကို အရည်အသွေးမြင့်စွာ ဒေါင်းလုဒ်လုပ်ပေးမည့် Bot ဖြစ်ပါသည်။\n\nဘယ် platform က ဒေါင်းမှာလဲ ရွေးချယ်ပေးပါ:", 
                                    reply_markup=InlineKeyboardMarkup(keyboard))
    return PLATFORM

async def platform_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['platform'] = query.data
    
    keyboard = [
        [InlineKeyboardButton("🎥 Video", callback_data='video'),
         InlineKeyboardButton("🎧 Audio", callback_data='audio')]
    ]
    await query.edit_message_text(f"✅ {query.data.upper()} ရွေးချယ်ပြီးပါပြီ။ ဘာအမျိုးအစားလိုချင်ပါသလဲ?", 
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return FORMAT_TYPE

async def ask_for_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['format'] = query.data
    await query.edit_message_text("🔗 ကျေးဇူးပြု၍ ဒေါင်းလုဒ်လုပ်လိုသော Video Link ကို ပို့ပေးပါ:")
    return GET_LINK

async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    media_format = context.user_data.get('format')
    
    # Professional Loading Effect
    status_msg = await update.message.reply_text("⏳ *Processing...*\n\n`[||||......] 40%`", parse_mode='MarkdownV2')

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if media_format == 'video' else 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
    }

    try:
        await status_msg.edit_text("⏳ *Downloading...*\n\n`[||||||||..] 80%`", parse_mode='MarkdownV2')
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        await status_msg.edit_text("✅ *Uploading to Telegram...*", parse_mode='MarkdownV2')
        
        if media_format == 'video':
            await update.message.reply_video(video=open(filename, 'rb'))
        else:
            await update.message.reply_audio(audio=open(filename, 'rb'))
            
        os.remove(filename)
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ *Error:* `{str(e)}`", parse_mode='MarkdownV2')
    
    return ConversationHandler.END

def main():
    TOKEN = "YOUR_TOKEN_HERE"
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PLATFORM: [CallbackQueryHandler(platform_choice)],
            FORMAT_TYPE: [CallbackQueryHandler(ask_for_link)],
            GET_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_download)]
        },
        fallbacks=[CommandHandler('start', start)]
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    if not os.path.exists('downloads'): os.makedirs('downloads')
    main()
