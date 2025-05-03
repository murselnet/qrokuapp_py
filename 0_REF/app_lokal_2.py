from flask import Flask, send_file, render_template_string, url_for
import os

# Ses dosyalarının yolunu çevre değişkeninden al
AUDIO_PATH="E:\\0MURSELDEPO\\qrokuapp_ses"
app = Flask(__name__)

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
    # Ses dosyasının tam yolu - sau formatında
    audio_path = os.path.join(AUDIO_PATH, f"{page}_sau.mp3")

    # Dosya varsa gönder, yoksa 404 hatası döndür
    if os.path.exists(audio_path):
        return send_file(audio_path, mimetype="audio/mpeg")
    else:
        return "Ses dosyası bulunamadı", 404

@app.route('/favicon.ico')
def favicon():
    return send_file('static/favicon.ico', mimetype='image/x-icon')

if __name__ == "__main__":
    app.run(debug=True, port=5000)
