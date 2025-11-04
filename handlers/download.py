import os
import tempfile
import yt_dlp
import json
import re

# ===============================================
#              0. دوال التخزين الدائم
# ===============================================

TEMP_STORAGE_FILE = 'temp_links.json' 
CHANNEL_USERNAME = "@SuPeRx1" 

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
#              1. دالة التحميل الرئيسية (مع التحميل السريع)
# ===============================================

def download_media_yt_dlp(bot, chat_id, url, platform_name, loading_msg_id, download_as_mp3=False, clip_times=None):
    """
    دالة متخصصة للتحميل باستخدام yt-dlp وإرسال الملف.
    """
    
    # 🚨 1. محاولة التحميل السريع عبر الرابط المباشر (Direct CDN Upload)
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
                        direct_link, # إرسال الرابط المباشر (Direct CDN)
                        caption=f'<b>{caption_text}</b>', 
                        parse_mode='HTML',
                        supports_streaming=True,
                        disable_notification=False # لا تستخدم Silent Mode هنا
                    )
                    print("✅ نجاح الإرسال عبر CDN.")
                    return True
                    
        except Exception as e:
            print(f"❌ فشل التحميل المباشر (CDN): {e}. العودة للتحميل عبر الخادم...")
            pass # الاستمرار إلى الخيار الاحتياطي
    
    # 🧹 2. التحميل التقليدي عبر الخادم (Fallback)
    with tempfile.TemporaryDirectory() as tmpdir:
        file_name_prefix = 'downloaded_media'
        file_extension = 'mp4' if not download_as_mp3 else 'mp3'
        file_path = os.path.join(tmpdir, f'{file_name_prefix}.{file_extension}')
        
        ydl_opts = {
            'outtmpl': file_path,
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
            file_path = os.path.join(tmpdir, f'{file_name_prefix}.mp3')

        # 1. بدء التنزيل
        try:
            print(f"🔄 بدء التحميل عبر الخادم (Fallback) للرابط: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)
        except Exception as e:
             # إذا فشل هنا، يتم رفع الخطأ إلى main.py وسيظهر للمستخدم
             raise Exception(f"فشل التحميل عبر yt-dlp. قد يكون الرابط غير متاح: {e}")
            
        # 2. حذف رسالة "جاري التحميل"
        # 💡 حماية من الخطأ 400
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
                     bot.send_audio(chat_id, f, caption=f'<b>{caption_text}</b>', parse_mode='HTML')
                else:
                    bot.send_video(
                        chat_id,
                        f,
                        caption=f'<b>{caption_text}</b>', 
                        parse_mode='HTML',
                        supports_streaming=True,
                        disable_notification=False
                    )
             print("✅ نجاح إرسال الملف عبر الخادم.")
             return True
        else:
             # إذا وصلنا إلى هنا ولم يتم العثور على الملف، يتم رفع خطأ
             raise Exception("فشل yt-dlp في حفظ أو إيجاد الملف بعد التنزيل.")
