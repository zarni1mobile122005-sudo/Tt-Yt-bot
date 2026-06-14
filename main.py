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
PLATFORM, FORMAT_TYPE = range(2)

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎵 TikTok", callback_data='tiktok'),
         InlineKeyboardButton("📺 YouTube", callback_data='youtube')]
    ]
    await update.message.reply_text("👋 မင်္ဂလာပါ! ဘယ် platform က ဒေါင်းမှာလဲ ရွေးချယ်ပေးပါ:", 
                                    reply_markup=InlineKeyboardMarkup(keyboard))
    return PLATFORM

# Platform ရွေးပြီးရင် Format ရွေးခိုင်းခြင်း
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

# Link ပို့ပြီး ဒေါင်းလုဒ်လုပ်ခြင်း
async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    media_format = query.data
    context.user_data['format'] = media_format
    
    await query.edit_message_text("🔗 ကျေးဇူးပြု၍ Video Link ကို ပို့ပေးပါ (ဥပမာ - https://...):")
    return ConversationHandler.END

# Link ကို လက်ခံပြီး Processing လုပ်ခြင်း
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    platform = context.user_data.get('platform')
    media_format = context.user_data.get('format')
    
    status_msg = await update.message.reply_text("⏳ ဒေါင်းလုဒ်လုပ်နေပါတယ်... ခဏစောင့်ပါ...")

    # yt-dlp options
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if media_format == 'video' else 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # Audio ဖြစ်လျှင် .m4a/.webm ကို .mp3 သို့ ပြောင်းရန် လိုအပ်ပါက FFmpeg သုံးရပါမည်
        
        if media_format == 'video':
            await update.message.reply_video(video=open(filename, 'rb'))
        else:
            await update.message.reply_audio(audio=open(filename, 'rb'))
            
        os.remove(filename) # ပို့ပြီးရင် ဖိုင်ကို ဖျက်ပေးပါ
        await status_msg.edit_text("✅ အောင်မြင်စွာ ဒေါင်းလုဒ်လုပ်ပြီးပါပြီ!")
    except Exception as e:
        await status_msg.edit_text(f"❌ Error ဖြစ်သွားပါတယ်: {str(e)}")

# Main Function
def main():
    # TOKEN အသစ်ကို ဒီနေရာမှာ ထည့်ပါ
    TOKEN = "8735328068:AAHfMpZOhC_7ZOgjh8tTvwgDPoT82f84t48"
    
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

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    if not os.path.exists('downloads'): os.makedirs('downloads')
    main()
