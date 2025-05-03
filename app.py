from flask import Flask, send_file, render_template_string, url_for, Response
import os
import io
import tempfile
import json
import threading
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import requests

# Google Drive klasör ID'si
DRIVE_FOLDER_ID = "199FGGEFrOOIKg6edCF7GKNZvKRKHRgGg"
app = Flask(__name__)

# Kendi dosya önbellek sistemi
CACHE_FILE = "drive_file_cache.json"
file_cache = {}
cache_lock = threading.Lock()
last_cache_update = 0
CACHE_TTL = 24 * 60 * 60  # 24 saat cache geçerlilik süresi

# Google Drive API için kimlik doğrulama
def get_drive_service():
    try:
        # Eğer service account credentials dosyanız varsa:
        # CREDENTIALS_FILE = 'credentials.json'  # Google Cloud Console'dan indirilen kimlik dosyası
        # creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE)
        # service = build('drive', 'v3', credentials=creds)
        
        # API key kullanarak basit erişim (yalnızca herkese açık dosyalar için)
        API_KEY = os.environ.get('GOOGLE_API_KEY', '')  # API anahtarınızı çevre değişkenlerinden alın
        service = build('drive', 'v3', developerKey=API_KEY)
        return service
    except Exception as e:
        print(f"Drive servisine bağlanırken hata: {e}")
        return None

def load_cache_from_file():
    """Disk üzerindeki önbellek dosyasından verileri yükler"""
    global file_cache, last_cache_update
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
                file_cache = cache_data.get('files', {})
                last_cache_update = cache_data.get('timestamp', 0)
                print(f"Diskten {len(file_cache)} adet dosya bilgisi yüklendi. Son güncelleme: {time.ctime(last_cache_update)}")
    except Exception as e:
        print(f"Önbellek dosyası yüklenirken hata: {e}")

def save_cache_to_file():
    """Önbellek verilerini diske kaydeder"""
    try:
        with open(CACHE_FILE, 'w') as f:
            cache_data = {
                'files': file_cache,
                'timestamp': time.time()
            }
            json.dump(cache_data, f)
            print(f"Önbellek dosyası güncellendi. Toplam {len(file_cache)} dosya bilgisi.")
    except Exception as e:
        print(f"Önbellek dosyası kaydedilirken hata: {e}")

def list_files_in_drive_folder():
    """Google Drive klasöründeki tüm dosyaları listeler ve önbelleğe alır"""
    global last_cache_update
    service = get_drive_service()
    if not service:
        return False

    with cache_lock:
        try:
            # Büyük listelerde sayfalama yapmak için
            page_token = None
            new_cache = {}
            
            while True:
                # Her sorguda en fazla 100 dosya alır
                results = service.files().list(
                    q=f"'{DRIVE_FOLDER_ID}' in parents",
                    fields="nextPageToken, files(id, name)",
                    pageSize=100,
                    pageToken=page_token
                ).execute()
                
                files = results.get('files', [])
                for file in files:
                    file_name = file.get('name')
                    file_id = file.get('id')
                    if file_name.endswith('_sau.mp3'):
                        page_number = file_name.split('_')[0]
                        if len(page_number) == 3:  # Sadece üç haneli sayfa numaraları
                            new_cache[page_number] = file_id
                
                # Daha fazla sayfa var mı kontrol et
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            # Güncellenmiş önbelleği kullan
            file_cache.update(new_cache)
            last_cache_update = time.time()
            
            # Diske kaydet
            save_cache_to_file()
            
            print(f"{len(file_cache)} adet ses dosyası önbelleğe alındı.")
            return True
            
        except Exception as e:
            print(f"Drive dosyalarını listelerken hata: {e}")
            return False

def should_update_cache():
    """Önbelleğin güncellenmesi gerekip gerekmediğini kontrol eder"""
    return time.time() - last_cache_update > CACHE_TTL

def update_cache_background():
    """Arka planda önbelleği günceller"""
    def update_job():
        if should_update_cache():
            print("Arka planda önbellek güncelleniyor...")
            list_files_in_drive_folder()
    
    # Yeni bir thread başlat
    thread = threading.Thread(target=update_job)
    thread.daemon = True
    thread.start()

# Flask 2.0+ için before_first_request yerine alternatif çözüm
# with app.app_context() bloğunu kullanıyoruz

def initialize_app():
    load_cache_from_file()
    
    # Önbellek boşsa veya güncel değilse güncelle
    if not file_cache or should_update_cache():
        # Düşük gecikme için arka planda güncelle
        update_cache_background()

# Bu işlev uygulama başlatıldığında çağrılacak

# Ana sayfa şablonu
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kuran Dinle - Ana Sayfa</title>
    
    <style rel="stylesheet" type="text/css">
        body {
            margin: 0;
            padding: 0;
            background: url("{{ url_for('static', filename='background.png') }}") no-repeat fixed;
            background-size: cover;
        }
        
        .menu_bar {
            position: relative;
            width: 100%;
            text-align: center;
            margin-bottom: 20px;
        }
        
        .menu_bar img {
            margin: 0 auto;
        }

        .page-list {
            max-width: 800px;
            margin: 20px auto;
            padding: 20px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 10px;
            columns: 4;
            column-gap: 20px;
        }

        .page-list a {
            display: block;
            color: #000;
            text-decoration: none;
            padding: 5px;
            margin: 2px 0;
            text-align: center;
        }

        .page-list a:hover {
            background: #f0f0f0;
            border-radius: 5px;
        }

        @media (max-width: 576px) {
            .page-list {
                columns: 2;
            }
        }
    </style>
</head>
<body>
    <div class="menu_bar">
        <img src="{{ url_for('static', filename='logo2.png') }}" alt="Bismillah">
    </div>

    <div class="page-list">
        {% for i in range(1, 606) %}
            <a href="/{{ '%03d' % i }}">{{ '%03d' % i }}</a>
        {% endfor %}
    </div>
</body>
</html>
"""

# Sayfa şablonu
PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kuran Dinle - Sayfa {{ page_number }}</title>
    
    <style rel="stylesheet" type="text/css">
        @media (max-width: 576px) {
            table tr td div audio {
                width: 250px;
            }
            table tr td img {
                width: 100px;
            }
        }
        
        body {
            margin: 0;
            padding: 0;
            background: url("{{ url_for('static', filename='background.png') }}") no-repeat fixed;
            background-size: cover;
        }
        
        .menu_bar {
            position: relative;
            width: 100%;
            text-align: center;
            margin-bottom: 20px;
        }
        
        .menu_bar img {
            margin: 0 auto;
        }
        
        table {
            margin: auto;
            margin-top: 20px;
        }
        
        table tr td {
            position: relative;
            padding: 0;
            margin: 0;
        }

        .back-button {
            display: block;
            width: 200px;
            margin: 50px auto;  /* margin-top değerini 20px'den 50px'e çıkardım */
            padding: 10px;
            text-align: center;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 5px;
            text-decoration: none;
            color: #000;
        }

        .back-button:hover {
            background: rgba(255, 255, 255, 1);
        }
    </style>
</head>
<body>
    <div class="menu_bar">
        <img src="{{ url_for('static', filename='logo2.png') }}" alt="Bismillah">
    </div>
    
    <div class="orta_alan">
        <table>
            <tr>
                <td>
                    <img src="{{ url_for('static', filename='sau.png') }}" width="120px" />
                </td>
                <td>
                    <div class="">
                        <audio controls>
                            <source src="{{ url_for('serve_audio', page=page_number) }}" type="audio/mpeg">
                            Tarayıcınız ses dosyasını desteklemiyor.
                        </audio>
                    </div>
                </td>
            </tr>
        </table>
    </div>

    <a href="/" class="back-button">Ana Sayfaya Dön</a>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HOME_TEMPLATE)

@app.route("/<string:page>")
def show_page(page):
    # Sayfa numarasının geçerli bir 3 haneli format olup olmadığını kontrol et
    if not page.isdigit() or len(page) != 3:
        return "Geçersiz sayfa formatı. Lütfen 3 haneli bir sayfa numarası girin (Örnek: 001, 015, 604)", 400
        
    # Sayfa numarasını doğrudan kullan çünkü zaten 3 haneli formatta
    return render_template_string(PAGE_TEMPLATE, page_number=page)

@app.route("/audio/<page>")
def serve_audio(page):
    # Önbellekte dosya ID'si var mı kontrol et
    file_id = file_cache.get(page)
    
    if not file_id:
        # Önbellek güncel değilse ve dosya önbellekte yoksa
        if should_update_cache():
            # Senkron olarak güncelle (kullanıcı bekleyebilir)
            list_files_in_drive_folder()
            file_id = file_cache.get(page)
        else:
            # Önbellek güncel ama aranan dosya yoksa
            # Düzenli önbellek güncellemesini tetikle (arka planda)
            update_cache_background()
    
    if not file_id:
        return "Ses dosyası bulunamadı", 404
    
    try:
        # Önce Google Drive alternatif API ile deneyin (daha hızlı ve daha az kısıtlama)
        download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
        
        # API anahtarı varsa ekleyin
        api_key = os.environ.get('GOOGLE_API_KEY', '')
        if api_key:
            download_url += f"&key={api_key}"
        
        # Alternatif olarak web indirme linkini kullanabilirsiniz
        fallback_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        # Önce API yöntemini deneyin
        try:
            response = requests.get(download_url, stream=True, timeout=5)
            if response.status_code != 200:
                # API yöntemi başarısız olursa, web linkini deneyin
                response = requests.get(fallback_url, stream=True, timeout=5)
        except:
            # API yöntemi başarısız olursa, web linkini deneyin
            response = requests.get(fallback_url, stream=True, timeout=5)
        
        if response.status_code != 200:
            return "Ses dosyası indirilemedi", 404
            
        # Önbellek kontrolünü için header'lar
        headers = {
            "Content-Type": "audio/mpeg",
            "Cache-Control": "public, max-age=86400"  # 24 saat önbellekleme
        }
            
        # Stream yanıtı oluştur
        def generate():
            for chunk in response.iter_content(chunk_size=8192):  # Chunk boyutunu artırdık
                yield chunk
                
        return Response(generate(), mimetype="audio/mpeg", headers=headers)
    except Exception as e:
        print(f"Ses dosyası servis edilirken hata: {e}")
        
        # Arka planda önbelleği güncelle (dosya silindi olabilir)
        update_cache_background()
        
        return "Ses dosyası servis edilirken bir hata oluştu", 500

@app.route('/favicon.ico')
def favicon():
    return send_file('static/favicon.ico', mimetype='image/x-icon')

# Doğrudan Drive dosya linki oluşturma fonksiyonu (isteğe bağlı kullanım)
def predict_file_id(page_number):
    """Ses dosyası için Drive ID bulunamadığında, isim kalıbına göre tahmin eder"""
    # Bu fonksiyon belirli bir düzene göre dosya adı formatı tahmin edebilir
    # Örneğin: Tüm dosyalar ardışık bir pattern ile yüklendiyse
    page_number = page_number.zfill(3)  # Sayfa numarasını 3 basamağa tamamla
    return f"{page_number}_sau.mp3"

# Hata sayfasını güzelleştirme
@app.errorhandler(404)
def page_not_found(e):
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sayfa Bulunamadı</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 40px;
                background: url("{{ url_for('static', filename='background.png') }}") no-repeat fixed;
                background-size: cover;
            }
            .error-container {
                max-width: 500px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.9);
                padding: 20px;
                border-radius: 10px;
            }
            .back-btn {
                display: inline-block;
                margin-top: 20px;
                padding: 10px 20px;
                background: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <div class="error-container">
            <h1>Sayfa Bulunamadı</h1>
            <p>Aradığınız sayfa veya ses dosyası bulunamadı.</p>
            <a href="/" class="back-btn">Ana Sayfaya Dön</a>
        </div>
    </body>
    </html>
    """), 404

# Uygulamayı performance mode ile başlat
if __name__ == "__main__":
    # Önce önbelleği yükle
    load_cache_from_file()
    
    # Eğer önbellek boşsa hemen güncelle
    if not file_cache:
        print("Önbellek boş. Google Drive'dan dosya listesi çekiliyor...")
        list_files_in_drive_folder()
    
    # Initialize fonksiyonunu çağır
    with app.app_context():
        initialize_app()
    
    # Daha iyi performans için debug modunu kapatabilirsiniz
    app.run(debug=False, port=5000)