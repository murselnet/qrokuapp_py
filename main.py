from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import re
import os
from typing import Optional

# Create FastAPI app
app = FastAPI(title="Qroku Audio Player", description="Audio player for MP3 files from Google Drive")

# Add CORS middleware to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Google Drive folder ID
DRIVE_FOLDER_ID = "199FGGEFrOOIKg6edCF7GKNZvKRKHRgGg"
MAX_FILE_NUMBER = 605

# HTML template for the welcome page
WELCOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Qroku Audio Player - Hoşgeldiniz</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            text-align: center;
        }
        .welcome-container {
            background-color: #fff;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            padding: 40px 20px;
            margin-top: 50px;
        }
        h1 {
            color: #333;
            font-size: 36px;
            margin-bottom: 30px;
        }
        .btn {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 15px 25px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 18px;
            margin: 20px 0;
            cursor: pointer;
            border-radius: 5px;
            transition: background-color 0.3s;
        }
        .btn:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <div class="welcome-container">
        <h1>Hoşgeldiniz</h1>
        <a href="/001.mp3" class="btn">Dinlemeye Başla</a>
    </div>
</body>
</html>
"""

# HTML template for the audio player
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Qroku Audio Player</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .player-container {
            background-color: #fff;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-top: 20px;
        }
        h1 {
            color: #333;
        }
        .audio-player {
            width: 100%;
            margin: 20px 0;
        }
        .navigation {
            display: flex;
            justify-content: space-between;
            margin-top: 20px;
        }
        .btn {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px 15px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 5px;
        }
        .btn:hover {
            background-color: #45a049;
        }
        .btn:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        .file-info {
            margin-top: 10px;
            color: #666;
        }
        .home-link {
            display: block;
            margin-top: 20px;
            color: #4CAF50;
            text-decoration: none;
        }
        .home-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="player-container">
        <h1>Qroku Audio Player</h1>
        <div class="file-info">
            Playing: {file_number}.mp3
        </div>
        <audio class="audio-player" controls autoplay>
            <source src="/stream/{file_number}.mp3" type="audio/mpeg">
            Your browser does not support the audio element.
        </audio>
        <div class="navigation">
            <a href="/{prev_file}.mp3" class="btn" {prev_disabled}>Previous</a>
            <a href="/{next_file}.mp3" class="btn" {next_disabled}>Next</a>
        </div>
        <a href="/" class="home-link">Ana Sayfaya Dön</a>
    </div>
</body>
</html>
"""


async def get_file_download_url(file_name: str) -> str:
    """
    Get the direct download URL for a file from Google Drive
    
    Args:
        file_name: The name of the file in Google Drive
        
    Returns:
        Direct download URL for the file
        
    Raises:
        HTTPException: If the file is not found or there's an error
    """
    try:
        # Google Drive API doesn't provide a simple way to download by filename
        # We need to use the Google Drive UI search feature
        search_url = f"https://drive.google.com/drive/folders/{DRIVE_FOLDER_ID}"
        
        async with httpx.AsyncClient() as client:
            # First get the folder to find the file ID
            response = await client.get(search_url)
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to access Google Drive folder")
            
            # Look for the file pattern in the response
            # The pattern might need adjustment based on how Google Drive renders the page
            pattern = f'"{file_name}".*?"id":"([^"]+)"'
            match = re.search(pattern, response.text)
            
            if not match:
                raise HTTPException(status_code=404, detail=f"File {file_name} not found in Google Drive folder")
            
            file_id = match.group(1)
            
            # Construct the direct download URL
            return f"https://drive.google.com/uc?export=download&id={file_id}"
            
    except httpx.RequestError:
        raise HTTPException(status_code=500, detail="Failed to connect to Google Drive")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the welcome page"""
    return HTMLResponse(content=WELCOME_TEMPLATE)


@app.get("/{file_number}.mp3", response_class=HTMLResponse)
async def get_player(file_number: str):
    """
    Serve HTML page with audio player for the requested file
    
    Args:
        file_number: The number of the file to play (e.g., 001, 002, etc.)
        
    Returns:
        HTML page with audio player
    """
    # Validate file number format
    if not re.match(r'^\d{3}$', file_number):
        raise HTTPException(status_code=400, detail="Invalid file number format. Use 3 digits (e.g., 001)")
    
    # Convert to integer for validation and navigation
    file_num = int(file_number)
    
    # Check if file number is within valid range
    if file_num < 1 or file_num > MAX_FILE_NUMBER:
        raise HTTPException(status_code=404, detail=f"File number must be between 001 and {MAX_FILE_NUMBER}")
    
    # Calculate prev and next file numbers
    prev_file = f"{file_num - 1:03d}" if file_num > 1 else "001"
    next_file = f"{file_num + 1:03d}" if file_num < MAX_FILE_NUMBER else f"{MAX_FILE_NUMBER:03d}"
    
    # Disable buttons if at the limits
    prev_disabled = "disabled" if file_num == 1 else ""
    next_disabled = "disabled" if file_num == MAX_FILE_NUMBER else ""
    
    # Generate HTML
    html_content = HTML_TEMPLATE.format(
        file_number=file_number,
        prev_file=prev_file,
        next_file=next_file,
        prev_disabled=prev_disabled,
        next_disabled=next_disabled
    )
    
    return HTMLResponse(content=html_content)


@app.get("/stream/{file_number}.mp3")
async def stream_audio(file_number: str):
    """
    Stream the audio file from Google Drive
    
    Args:
        file_number: The number of the file to stream (e.g., 001, 002, etc.)
        
    Returns:
        Streaming response with the audio content
    """
    # Validate file number format
    if not re.match(r'^\d{3}$', file_number):
        raise HTTPException(status_code=400, detail="Invalid file number format. Use 3 digits (e.g., 001)")
    
    # Convert to integer for validation
    file_num = int(file_number)
    
    # Check if file number is within valid range
    if file_num < 1 or file_num > MAX_FILE_NUMBER:
        raise HTTPException(status_code=404, detail=f"File number must be between 001 and {MAX_FILE_NUMBER}")
    
    # Format Google Drive filename based on pattern (001_sau.mp3)
    drive_filename = f"{file_number}_sau.mp3"
    
    try:
        # Get direct download URL
        download_url = await get_file_download_url(drive_filename)
        
        async def stream_file():
            async with httpx.AsyncClient() as client:
                async with client.stream("GET", download_url) as response:
                    if response.status_code != 200:
                        raise HTTPException(status_code=response.status_code, detail="Failed to stream file from Google Drive")
                    
                    async for chunk in response.aiter_bytes():
                        yield chunk
        
        return StreamingResponse(
            stream_file(),
            media_type="audio/mpeg",
            headers={"Content-Disposition": f"inline; filename={file_number}.mp3"}
        )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stream audio: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8000))
    # Run the application
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
