@echo off
echo ===========================================
echo YouTube Shorts Generator - Setup Script
echo ===========================================
echo.

echo Checking for Python installation...
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python not found! Please install Python 3.8 or newer.
    echo Visit https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Checking for pip...
pip --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo pip not found! Please ensure pip is installed with Python.
    pause
    exit /b 1
)

echo.
echo Installing Python dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install dependencies.
    echo Please make sure you have internet connection and proper permissions.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Creating required directories...
mkdir output 2>nul
mkdir resources 2>nul
mkdir resources\temp 2>nul
mkdir resources\music 2>nul

echo.
echo Checking for FFmpeg...
where ffmpeg > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo FFmpeg not found! The application requires FFmpeg for video processing.
    echo.
    echo Would you like to download FFmpeg automatically? (y/n)
    set /p ffmpeg_choice=
    
    if /i "%ffmpeg_choice%"=="y" (
        echo This feature is not implemented yet. Please download FFmpeg manually.
        echo Visit: https://ffmpeg.org/download.html
    ) else (
        echo Please download and install FFmpeg manually from https://ffmpeg.org/download.html
    )
    echo.
)

echo.
echo Setting up environment...
if not exist .env (
    echo Creating sample .env file
    echo OPENAI_API_KEY=your_api_key_here > .env
    echo Please edit the .env file to add your OpenAI API key
)

echo.
echo Would you like to download sample background videos and music? (y/n)
set /p download_choice=

if /i "%download_choice%"=="y" (
    echo.
    echo Downloading sample resources...
    python download_resources.py
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to download resources.
        echo You can try again later by running 'python download_resources.py'
    )
)

echo.
echo ===========================================
echo Setup complete! 
echo ===========================================
echo.
echo You can now run the application with:
echo.
echo     streamlit run app.py
echo.
echo Or use the run_app.bat script.
echo.
echo Don't forget to set your OpenAI API key in the .env file or in the application!
echo.

pause 