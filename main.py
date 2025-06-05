from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import httpx
import re
import os
from typing import Optional
import aiohttp
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(title="Qroku Audio Player", description="Audio player for MP3 files from repo.mursel.net")

# Add CORS middleware to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Base URL for MP3 files
BASE_URL = "https://repo.mursel.net/oku"

# Available MP3 files list
MP3_FILES = [f"{i:03d}_sau.mp3" for i in range(1, 606)]

# HTML template for the welcome page with file list
WELCOME_TEMPLATE = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Qroku Audio Player - Hoşgeldiniz</title>
    <link rel="icon" href="/static/favicon.ico" type="image/x-icon">
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: url("/static/background.png") no-repeat center center fixed;
            background-size: cover;
            background-color: #000;
            min-height: 100vh;
            overflow-x: hidden;
        }}
        
        .menu_bar {{
            position: relative;
            width: 100%;
            text-align: center;
            margin-bottom: 20px;
        }}
        
        .menu_bar img {{
            margin: 0 auto;
        }}
        
        table {{
            margin: auto;
            margin-top: 20px;
        }}
        
        table tr td {{
            position: relative;
            padding: 0;
            margin: 0;
        }}

        .page-list {{
            max-width: 800px;
            margin: 20px auto 10px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 10px;
            columns: 4;
            column-gap: 20px;
        }}

        .page-list a {{
            display: block;
            color: #000;
            text-decoration: none;
            padding: 5px;
            margin: 2px 0;
            text-align: center;
            position: relative;
        }}

        .page-list a:hover {{
            background: #f0f0f0;
            border-radius: 5px;
        }}

        .status-dot {{
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-left: 5px;
        }}

        .status-dot.available {{
            background-color: #4CAF50;
        }}

        .status-dot.unavailable {{
            background-color: #f44336;
        }}
        
        .back-button {{
            display: block;
            width: 200px;
            margin: 20px auto;
            padding: 10px;
            text-align: center;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 5px;
            text-decoration: none;
            color: #000;
        }}

        .back-button:hover {{
            background: rgba(255, 255, 255, 1);
        }}

        @media (max-width: 576px) {{
            .page-list {{
                columns: 2;
            }}
            table tr td img {{
                width: 100px;
            }}
        }}
    </style>
</head>
<body>
    <div class="menu_bar">
        <img src="/static/logo2.png" alt="Bismillah">
    </div>
    
    <div class="orta_alan">
        <table>
            <tr>
                <td>
                    <img src="/static/sau.png" width="120px" />
                </td>
                <td>
                    <h2 style="color: white; background: rgba(0,0,0,0.5); padding: 10px; border-radius: 5px;">Qroku Audio Player</h2>
                </td>
            </tr>
        </table>
    </div>

    <div class="page-list">
        {file_links}
    </div>
</body>
</html>
'''

# HTML template for the audio player
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Qroku Audio Player</title>
    <link rel="icon" href="/static/favicon.ico" type="image/x-icon">
    <style>
        @media (max-width: 576px) {{
            table tr td div audio {{
                width: 250px;
            }}
            table tr td img {{
                width: 100px;
            }}
        }}
        
        body {{
            margin: 0;
            padding: 0;
            background: url("/static/background.png") no-repeat center center fixed;
            background-size: cover;
            background-color: #000;
            min-height: 100vh;
            overflow-x: hidden;
        }}
        
        .menu_bar {{
            position: relative;
            width: 100%;
            text-align: center;
            margin-bottom: 20px;
        }}
        
        .menu_bar img {{
            margin: 0 auto;
        }}
        
        table {{
            margin: auto;
            margin-top: 20px;
        }}
        
        table tr td {{
            position: relative;
            padding: 0;
            margin: 0;
        }}

        .back-button {{
            display: block;
            width: 200px;
            margin: 50px auto;
            padding: 10px;
            text-align: center;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 5px;
            text-decoration: none;
            color: #000;
        }}

        .back-button:hover {{
            background: rgba(255, 255, 255, 1);
        }}
    </style>
</head>
<body>
    <div class="menu_bar">
        <img src="/static/logo2.png" alt="Bismillah">
    </div>
    
    <div class="orta_alan">
        <table>
            <tr>
                <td>
                    <img src="/static/sau.png" width="120px" />
                </td>
                <td>
                    <div class="">
                        <audio controls>
                            <source src="{file_url}" type="audio/mpeg">
                            Tarayıcınız ses dosyasını desteklemiyor.
                        </audio>
                    </div>
                </td>
            </tr>
        </table>
    </div>

    <div style="text-align: center; margin-top: 20px;">
        <a href="/{prev_file}" class="back-button" {prev_disabled}>Previous</a>
        <a href="/{next_file}" class="back-button" {next_disabled}>Next</a>
    </div>

    <a href="/" class="back-button">Ana Sayfaya Dön</a>
</body>
</html>
'''

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the welcome page with file list"""
    file_links = ""
    for file_name in MP3_FILES:
        # Add a green dot for available files (all files are available in this case)
        file_links += f'<a href="/{file_name}">{file_name}<span class="status-dot available"></span></a>\n'
    
    return HTMLResponse(content=WELCOME_TEMPLATE.format(file_links=file_links))

@app.get("/{file_name}", response_class=HTMLResponse)
async def get_player(file_name: str):
    """Serve HTML page with audio player for the requested file"""
    if file_name not in MP3_FILES:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Find current index and calculate prev/next files
    current_index = MP3_FILES.index(file_name)
    prev_file = MP3_FILES[current_index - 1] if current_index > 0 else file_name
    next_file = MP3_FILES[current_index + 1] if current_index < len(MP3_FILES) - 1 else file_name
    
    # Disable buttons if at the limits
    prev_disabled = "disabled" if current_index == 0 else ""
    next_disabled = "disabled" if current_index == len(MP3_FILES) - 1 else ""
    
    # Generate direct URL to the file
    file_url = f"{BASE_URL}/{file_name}"
    
    # Generate HTML
    html_content = HTML_TEMPLATE.format(
        file_name=file_name,
        file_url=file_url,
        prev_file=prev_file,
        next_file=next_file,
        prev_disabled=prev_disabled,
        next_disabled=next_disabled
    )
    
    return HTMLResponse(content=html_content)

# Error handling middleware
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        print(f"Error handling request: {request.url.path} - {str(e)}")
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html lang="tr">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Sayfa Bulunamadı</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        text-align: center;
                        padding: 40px;
                        background: url("/static/background.png") no-repeat center center fixed;
                        background-size: cover;
                        background-color: #000;
                        min-height: 100vh;
                        overflow-x: hidden;
                    }}
                    .error-container {{
                        max-width: 500px;
                        margin: 0 auto;
                        background: rgba(255, 255, 255, 0.9);
                        padding: 20px;
                        border-radius: 10px;
                    }}
                    .back-btn {{
                        display: inline-block;
                        margin-top: 20px;
                        padding: 10px 20px;
                        background: #4CAF50;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                    }}
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
            """,
            status_code=500
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
