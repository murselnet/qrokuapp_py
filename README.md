# Qroku Audio Player

A FastAPI application that serves MP3 files from Google Drive with a web-based audio player.

## Features

- Streams MP3 files directly from Google Drive
- Clean and modern audio player interface
- Navigation between audio files
- Responsive design

## Requirements

- Python 3.7+
- FastAPI
- Uvicorn
- httpx

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd qrokuapp_py
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python main.py
   ```

2. Access the application in your web browser:
   ```
   http://localhost:8000
   ```

3. For production deployment on a server with the domain https://oku.mursel.net, 
   set up a reverse proxy (like Nginx) to forward requests to the application.

## Configuration

- The application is configured to serve MP3 files from Google Drive folder: `199FGGEFrOOIKg6edCF7GKNZvKRKHRgGg`
- Files in the folder should be named in the format `001_sau.mp3`, `002_sau.mp3`, etc., up to `605_sau.mp3`
- The port can be configured by setting the `PORT` environment variable

## API Endpoints

- `GET /`: Redirects to the first audio file
- `GET /{file_number}.mp3`: Serves the HTML page with the audio player for the specified file
- `GET /stream/{file_number}.mp3`: Streams the audio file directly from Google Drive

## Notes

- The application uses CORS middleware to allow requests from any origin
- The streaming is done asynchronously to optimize performance 