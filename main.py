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

FORMAT_TYPE, GET_LINK = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎥 Video", callback_data='video'),
         InlineKeyboardButton("🎧 Audio", callback_data='audio')]
    ]
    await update.message.reply_text("👋 TikTok Downloader Bot\n\nဘာအမျိုးအစားဒေါင်းမလဲ ရွေးချယ်ပေးပါ:", 
                                    reply_markup=InlineKeyboardMarkup(keyboard))
    return FORMAT_TYPE

async def ask_for_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['format'] = query.data
    await query.edit_message_text("🔗 ကျေးဇူးပြု၍ TikTok Link ကို ပို့ပေးပါ:")
    return GET_LINK

async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    media_format = context.user_data.get('format')
    status_msg = await update.message.reply_text("⏳ Processing...")

    ydl_opts = {
        'format': 'best' if media_format == 'video' else 'bestaudio/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s', # filename ပြဿနာမတက်အောင် id ကိုသုံးခြင်း
    }

    filename = None
    try:
        await status_msg.edit_text("⏳ Downloading...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        await status_msg.edit_text("✅ Uploading...")
        
        if media_format == 'video':
            await update.message.reply_video(video=open(filename, 'rb'))
        else:
            await update.message.reply_audio(audio=open(filename, 'rb'))
            
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ Error ဖြစ်သွားပါသည်: {str(e)}")
    finally:
        if filename and os.path.exists(filename):
            os.remove(filename) # ဖိုင်ကို အမြဲသေချာဖျက်ပေးခြင်း
    
    return ConversationHandler.END

def main():
    TOKEN = "YOUR_TOKEN_HERE"
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
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
