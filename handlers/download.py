import os
import tempfile
import yt_dlp
import json
import re
from telebot import types # 🚨 إضافة استيراد types لإنشاء زر المشاركة

# ===============================================
#              0. دوال التخزين والثوابت
# ===============================================

TEMP_STORAGE_FILE = 'temp_links.json' 
CHANNEL_USERNAME = "@iiollr" 
# 🚨 الميزة 12: اسم المستخدم الجديد للبوت
BOT_USERNAME = "@gdudhdbeebot" 

def load_links():
    if os.path.exists(TEMP_STORAGE_FILE):
        try:
            with open(TEMP_STORAGE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def save_links(data):
    try:
        with open(TEMP_STORAGE_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"❌ فشل حفظ البيانات في ملف JSON: {e}")

# ===============================================
#              1. دالة التحميل الرئيسية (المُبتكرة)
# ===============================================

def download_media_yt_dlp(bot, chat_id, url, platform_name, loading_msg_id, download_as_mp3=False, clip_times=None):
    
    video_title = 'Video' # عنوان افتراضي
    
    # 🚨 الميزة 12: استخراج معلومات العنوان (للتسمية والمشاركة)
    try:
        ydl_opts_title = {'quiet': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts_title) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'Video')
    except Exception:
        video_title = 'Video'

    # معالجة العنوان (إزالة الأحرف الخاصة واستبدال المسافات بـ '_')
    safe_title = re.sub(r'[^\w\s-]', '', video_title).strip().replace(' ', '_')
    final_file_name_prefix = f'{BOT_USERNAME}_{safe_title}' # 💡 تطبيق التسمية المخصصة

    # 🚨 2. إنشاء زر المشاركة (الميزة 35)
    share_markup = types.InlineKeyboardMarkup()
    share_btn = types.InlineKeyboardButton(
        text="🚀 شارك هذا الملف بسرعة", 
        url=f"https://t.me/share/url?url={url}&text={video_title}" 
    )
    share_markup.row(share_btn)
    
    # ==========================================================
    #             محاولة التحميل السريع (CDN Upload)
    # ==========================================================
    if not download_as_mp3 and not clip_times:
        try:
            print(f"🌐 محاولة التحميل السريع (CDN) للرابط: {url}")
            ydl_opts_info = {'quiet': True, 'skip_download': True, 'force_generic_extractor': True}
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'url' in info: 
                    direct_link = info['url']
                    
                    # 💡 حذف رسالة التحميل مع حماية من الخطأ 400
                    try:
                        bot.delete_message(chat_id, loading_msg_id)
                    except Exception as e:
                        print(f"⚠️ فشل حذف رسالة التحميل (CDN). تم تجاهل الخطأ: {e}") 
                        
                    caption_text = f"✅ تم التحميل بسرعة فائقة من {platform_name} بواسطة: {CHANNEL_USERNAME}"
                    
                    bot.send_video(
                        chat_id,
                        direct_link, 
                        caption=f'<b>{caption_text}</b>', 
                        parse_mode='HTML',
                        supports_streaming=True,
                        file_name=f'{final_file_name_prefix}.mp4', # 💡 تطبيق الميزة 12
                        reply_markup=share_markup # 💡 تطبيق الميزة 35
                    )
                    print("✅ نجاح الإرسال عبر CDN.")
                    return True
                    
        except Exception as e:
            print(f"❌ فشل التحميل المباشر (CDN): {e}. العودة للتحميل عبر الخادم...")
            pass # الاستمرار إلى الخيار الاحتياطي
    
    # ==========================================================
    #         التحميل التقليدي عبر الخادم (Fallback)
    # ==========================================================
    with tempfile.TemporaryDirectory() as tmpdir:
        file_extension = 'mp4' if not download_as_mp3 else 'mp3'
        # 🚨 استخدام الاسم المخصص
        file_path = os.path.join(tmpdir, f'{final_file_name_prefix}.{file_extension}') 
        
        ydl_opts = {
            'outtmpl': file_path, # 🚨 تحديث مسار الحفظ
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        }
        
        if download_as_mp3:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                 'key': 'FFmpegExtractAudio',
                 'preferredcodec': 'mp3',
                 'preferredquality': '192',
            }]
            file_path = os.path.join(tmpdir, f'{final_file_name_prefix}.mp3') # 🚨 تحديث مسار MP3

        # 1. بدء التنزيل
        try:
            print(f"🔄 بدء التحميل عبر الخادم (Fallback) للرابط: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)
        except Exception as e:
             raise Exception(f"فشل التحميل عبر yt-dlp. قد يكون الرابط غير متاح: {e}")
            
        # 2. حذف رسالة "جاري التحميل"
        try:
            bot.delete_message(chat_id, loading_msg_id)
        except Exception as e:
            print(f"⚠️ فشل حذف رسالة التحميل (Fallback). تم تجاهل الخطأ: {e}")
        
        # 3. الإرسال إلى تيليجرام
        caption_text = f"✅ تم التحميل من {platform_name} بواسطة: {CHANNEL_USERNAME}" 
        
        if os.path.exists(file_path):
             print(f"📤 إرسال الملف: {file_path}")
             
             with open(file_path, 'rb') as f:
                if 'mp3' in file_path.lower():
                     bot.send_audio(
                         chat_id, 
                         f, 
                         caption=f'<b>{caption_text}</b>', 
                         parse_mode='HTML',
                         file_name=f'{final_file_name_prefix}.mp3', # 💡 الميزة 12
                         reply_markup=share_markup # 💡 الميزة 35
                     )
                else:
                    bot.send_video(
                        chat_id,
                        f,
                        caption=f'<b>{caption_text}</b>', 
                        parse_mode='HTML',
                        supports_streaming=True,
                        disable_notification=False,
                        file_name=f'{final_file_name_prefix}.mp4', # 💡 الميزة 12
                        reply_markup=share_markup # 💡 الميزة 35
                    )
             print("✅ نجاح إرسال الملف عبر الخادم.")
             return True
        else:
             raise Exception("فشل yt-dlp في حفظ أو إيجاد الملف بعد التنزيل.")

