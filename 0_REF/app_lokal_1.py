from flask import Flask, send_file, render_template_string, url_for
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Ses dosyalarının yolunu çevre değişkeninden al
AUDIO_PATH = os.getenv('AUDIO_PATH', 'E:\\oku')

app = Flask(__name__)

HTML_TEMPLATE = """
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
    }
    
    .menu_bar img {
      margin-left: calc(50% - 75px);
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
</body>
</html>
"""

@app.route("/<int:page>")
def show_page(page):
    # Sayfa numarasını 3 haneli formata çevir
    page_str = str(page).zfill(3)
    return render_template_string(HTML_TEMPLATE, page_number=page_str)


@app.route("/audio/<page>")
def serve_audio(page):
    # Ses dosyasının tam yolu - sau formatında
    audio_path = os.path.join(AUDIO_PATH, f"{page}_sau.mp3")

    # Dosya varsa gönder, yoksa 404 hatası döndür
    if os.path.exists(audio_path):
        return send_file(audio_path, mimetype="audio/mpeg")
    else:
        return "Ses dosyası bulunamadı", 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
