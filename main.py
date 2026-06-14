import logging
import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "8735328068:AAHfMpZOhC_7ZOgjh8tTvwgDPoT82f84t48"
PORT = int(os.environ.get("PORT", 8080))

PLATFORM, FORMAT_TYPE = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎵 TikTok", callback_data='tiktok'),
                 InlineKeyboardButton("📺 YouTube", callback_data='youtube')]]
    await update.message.reply_text("👋 မင်္ဂလာပါ! ဘယ် platform က ဒေါင်းမှာလဲ?", reply_markup=InlineKeyboardMarkup(keyboard))
    return PLATFORM

async def platform_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['platform'] = query.data
    keyboard = [[InlineKeyboardButton("🎥 Video", callback_data='video'),
                 InlineKeyboardButton("🎧 Audio", callback_data='audio')]]
    await query.edit_message_text("✅ ရွေးပြီးပြီ။ ဘာအမျိုးအစားလိုချင်လဲ?", reply_markup=InlineKeyboardMarkup(keyboard))
    return FORMAT_TYPE

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['format'] = query.data
    await query.edit_message_text("🔗 Link ကို အခု ပို့ပေးပါ:")
    return ConversationHandler.END

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    platform = context.user_data.get('platform')
    media_format = context.user_data.get('format')
    status_msg = await update.message.reply_text("⏳ ဒေါင်းလုဒ်လုပ်နေပါတယ်...")

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if media_format == 'video' else 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        if media_format == 'video':
            await update.message.reply_video(video=open(filename, 'rb'))
        else:
            await update.message.reply_audio(audio=open(filename, 'rb'))
        os.remove(filename)
        await status_msg.edit_text("✅ အောင်မြင်ပါပြီ!")
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")

def main():
    if not os.path.exists('downloads'): os.makedirs('downloads')
    
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PLATFORM: [CallbackQueryHandler(platform_choice)],
            FORMAT_TYPE: [CallbackQueryHandler(download_media)]
        },
        fallbacks=[CommandHandler('start', start)]
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    # Render ပေါ်မှာ run ရန်
    app.run_polling() 

if __name__ == '__main__':
    main()
