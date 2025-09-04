# Camera Service

A Python service for capturing images from RTSP cameras and uploading them to a cloud storage API.

## Features

- **Web Interface**: Modern, responsive dashboard for monitoring and control
- **RTSP Camera Capture**: Dual camera support with retry logic
- **Offline Mode**: Continues capturing when internet is unavailable
- **Local Storage**: Stores up to 50 images locally with automatic queue management
- **Automatic Upload**: Uploads queued images when internet connection returns
- **Real-time Status**: Live monitoring of system health and upload queue
- **Configuration Management**: Web-based RTSP and S3 URL configuration
- **Image Gallery**: View and manage captured images through web interface
- **TCP Server**: Handles RFID triggers for automated capture
- **Comprehensive Logging**: Detailed logging and error handling
- **Environment-based Configuration**: Secure credential management

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy configuration template:
```bash
cp config_template.env .env
```

3. Edit `.env` file with your actual configuration values.

## Configuration

The service uses environment variables for configuration. See `config_template.env` for all available options:

- `CAMERA_USERNAME` / `CAMERA_PASSWORD`: RTSP camera credentials
- `CAMERA_1_IP` / `CAMERA_2_IP`: Camera IP addresses
- `S3_API_URL`: Upload API endpoint
- `MAX_RETRIES` / `RETRY_DELAY`: Retry configuration
- `BIND_IP` / `BIND_PORT`: TCP server configuration

## Usage

### Web Interface (Recommended)
```bash
python start_web.py
```
Then open your browser to `http://localhost:5000` to access the dashboard.

### Basic Camera Capture
```python
from capture_service import CameraService

cam = CameraService()
location = cam.capture_camera_1()  # Returns S3 location URL or local path
```

### Run Main Demo
```bash
python main.py
```

### Start Trigger Server
```bash
python trigger_server.py
```

The trigger server accepts TCP connections and processes trigger commands:
- `camera_1` or `rfid_1` → triggers camera 1
- `camera_2` or `rfid_2` → triggers camera 2
- Any other text → defaults to camera 1

### GPIO Triggers (Raspberry Pi)
The system supports GPIO triggers for automatic camera capture:

1. **Enable GPIO in configuration:**
   ```bash
   export GPIO_ENABLED=true
   export GPIO_CAMERA_1_PIN=18
   export GPIO_CAMERA_2_PIN=19
   ```

2. **Install GPIO dependencies:**
   ```bash
   pip install RPi.GPIO
   ```

3. **Use the web interface to toggle GPIO monitoring:**
   - Navigate to the Camera Controls section
   - Toggle the GPIO switches for each camera
   - When enabled, pulling the respective GPIO pin LOW will trigger camera capture

**GPIO Pin Configuration:**
- Camera 1: GPIO Pin 18 (configurable via `GPIO_CAMERA_1_PIN`)
- Camera 2: GPIO Pin 19 (configurable via `GPIO_CAMERA_2_PIN`)
- Pins are configured with internal pull-up resistors
- Trigger occurs on falling edge (pin pulled LOW)

## Architecture

- `web_app.py`: Flask web application with dashboard
- `start_web.py`: Web application startup script
- `capture_service.py`: Core camera capture functionality with offline support
- `uploader.py`: Image upload service
- `gpio_service.py`: GPIO monitoring service for Raspberry Pi triggers
- `local_storage.py`: Local image storage and queue management
- `trigger_server.py`: TCP server for external triggers
- `config.py`: Configuration management
- `logging_config.py`: Logging setup
- `main.py`: Demo application
- `templates/index.html`: Web dashboard interface

## Security Notes

- Camera credentials are now stored in environment variables
- File size limits prevent large file uploads
- Input validation prevents path traversal attacks
- Proper error handling prevents information leakage

## Web Interface Features

### Dashboard
- **Real-time Status**: Live monitoring of system health, connection status, and upload queue
- **Image Gallery**: View all captured images with thumbnails and metadata
- **Configuration Panel**: Update RTSP URLs and S3 endpoint through web interface
- **Camera Controls**: Manual trigger buttons for both cameras
- **Upload Management**: Force upload queued images and monitor upload progress

### Offline Mode
- **Automatic Detection**: Detects internet connectivity and switches modes automatically
- **Local Storage**: Stores up to 50 images locally when offline
- **Queue Management**: Automatically uploads queued images when connection returns
- **Status Indicators**: Visual indicators for online/offline status and queue size

## Error Handling

The service includes comprehensive error handling:
- Camera connection failures with retry logic
- Upload failures with automatic retries
- File validation and size limits
- Proper resource cleanup
- Detailed logging for debugging
- Offline mode with graceful degradation

## Logging

Logs are written to console by default. To enable file logging, set the `LOG_FILE` environment variable.

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
