#!/usr/bin/env python3
"""
Flask Web Interface for Camera Service
Provides web-based configuration, monitoring, and image management.
"""
import os
import json
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_cors import CORS
import logging

from capture_service import CameraService
from uploader import ImageUploader
from local_storage import LocalStorageManager
from gpio_service import gpio_service
import config
from config import RTSP_CAMERAS, S3_API_URL, MAX_RETRIES, RETRY_DELAY
from logging_config import setup_logging

app = Flask(__name__)
CORS(app)

# Global variables
camera_service = None
uploader = None
storage_manager = None
gpio_status = {
    'camera_1': False,
    'camera_2': False
}
system_status = {
    'online': True,
    'last_check': datetime.now(),
    'pending_uploads': 0,
    'total_captures': 0,
    'successful_uploads': 0,
    'failed_uploads': 0
}

def gpio_camera_1_callback():
    """GPIO callback for camera 1 trigger."""
    if camera_service:
        try:
            location = camera_service.capture_camera_1()
            if location and location.startswith('local:'):
                filepath = location[6:]  # Remove 'local:' prefix
                storage_manager.add_image(filepath)
                
                # Try to upload in background
                try:
                    upload_location = uploader.upload(filepath)
                    if upload_location:
                        storage_manager.mark_as_uploaded(os.path.basename(filepath))
                        logging.info(f"GPIO triggered capture and upload: {os.path.basename(filepath)}")
                    else:
                        logging.info(f"GPIO triggered capture (upload failed): {os.path.basename(filepath)}")
                except Exception as e:
                    logging.error(f"GPIO capture upload error: {e}")
        except Exception as e:
            logging.error(f"GPIO camera 1 capture error: {e}")

def gpio_camera_2_callback():
    """GPIO callback for camera 2 trigger."""
    if camera_service:
        try:
            location = camera_service.capture_camera_2()
            if location and location.startswith('local:'):
                filepath = location[6:]  # Remove 'local:' prefix
                storage_manager.add_image(filepath)
                
                # Try to upload in background
                try:
                    upload_location = uploader.upload(filepath)
                    if upload_location:
                        storage_manager.mark_as_uploaded(os.path.basename(filepath))
                        logging.info(f"GPIO triggered capture and upload: {os.path.basename(filepath)}")
                    else:
                        logging.info(f"GPIO triggered capture (upload failed): {os.path.basename(filepath)}")
                except Exception as e:
                    logging.error(f"GPIO capture upload error: {e}")
        except Exception as e:
            logging.error(f"GPIO camera 2 capture error: {e}")

def init_services():
    """Initialize camera and upload services."""
    global camera_service, uploader, storage_manager
    camera_service = CameraService()
    uploader = ImageUploader()
    storage_manager = LocalStorageManager(max_images=50)
    
    # Initialize GPIO service
    if gpio_service.is_gpio_available():
        gpio_service.register_callback('camera_1', gpio_camera_1_callback)
        gpio_service.register_callback('camera_2', gpio_camera_2_callback)
        gpio_service.start_monitoring()
        logging.info("GPIO service initialized and monitoring started")
    else:
        logging.info("GPIO service not available or disabled")
    
    # Start background upload thread
    start_upload_thread()

# Removed load_local_images function - now handled by LocalStorageManager

def check_internet_connection():
    """Check if internet connection is available."""
    try:
        import requests
        response = requests.get('https://www.google.com', timeout=5)
        return response.status_code == 200
    except:
        return False

def start_upload_thread():
    """Start background thread for uploading queued images."""
    def upload_worker():
        global system_status, storage_manager
        
        while True:
            try:
                if check_internet_connection():
                    system_status['online'] = True
                    system_status['last_check'] = datetime.now()
                    
                    # Get images that need uploading
                    images_to_upload = storage_manager.get_upload_queue()
                    
                    if images_to_upload:
                        # Try to upload oldest images first
                        for img_info in images_to_upload[:5]:  # Upload up to 5 at a time
                            try:
                                location = uploader.upload(img_info['filepath'])
                                if location:
                                    system_status['successful_uploads'] += 1
                                    # Mark as uploaded but keep in local storage for gallery
                                    storage_manager.mark_as_uploaded(img_info['filename'])
                                    logging.info(f"Successfully uploaded: {img_info['filename']}")
                                else:
                                    system_status['failed_uploads'] += 1
                                    break  # Stop if upload fails
                            except Exception as e:
                                logging.error(f"Upload error: {e}")
                                system_status['failed_uploads'] += 1
                                break
                    
                    system_status['pending_uploads'] = len(storage_manager.get_upload_queue())
                else:
                    system_status['online'] = False
                    system_status['last_check'] = datetime.now()
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logging.error(f"Upload thread error: {e}")
                time.sleep(30)
    
    thread = threading.Thread(target=upload_worker, daemon=True)
    thread.start()

# Initialize services when the app is created
def initialize_services_on_startup():
    """Initialize services on startup."""
    try:
        init_services()
        logging.info("Services initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize services: {e}")

# Initialize services immediately
initialize_services_on_startup()

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get system status."""
    global system_status, storage_manager
    
    if storage_manager is None:
        return jsonify({'error': 'Storage manager not initialized'}), 500
    
    upload_queue = storage_manager.get_upload_queue()
    system_status['pending_uploads'] = len(upload_queue)
    system_status['total_captures'] = storage_manager.get_image_count()
    
    return jsonify({
        'status': system_status,
        'local_images': storage_manager.get_image_count(),
        'queued_uploads': len(upload_queue),
        'successful_uploads': storage_manager.get_uploaded_count(),
        'max_local_images': storage_manager.max_images,
        'storage_info': storage_manager.get_storage_info()
    })

@app.route('/api/config')
def get_config():
    """Get current configuration."""
    return jsonify({
        'rtsp_cameras': RTSP_CAMERAS,
        's3_url': S3_API_URL,
        'max_retries': MAX_RETRIES,
        'retry_delay': RETRY_DELAY
    })

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration."""
    try:
        data = request.json
        
        # Update RTSP cameras
        if 'rtsp_cameras' in data:
            for camera_id, url in data['rtsp_cameras'].items():
                if camera_id in RTSP_CAMERAS:
                    RTSP_CAMERAS[camera_id] = url
        
        # Update S3 URL
        if 's3_url' in data:
            global S3_API_URL
            S3_API_URL = data['s3_url']
        
        # Save to environment file (optional)
        save_config_to_file(data)
        
        return jsonify({'success': True, 'message': 'Configuration updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

def save_config_to_file(config_data):
    """Save configuration to file."""
    try:
        config_file = 'web_config.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    except Exception as e:
        logging.error(f"Failed to save config: {e}")

@app.route('/api/capture/<camera_id>')
def capture_image(camera_id):
    """Capture image from specified camera."""
    try:
        if camera_service is None:
            return jsonify({'success': False, 'message': 'Camera service not initialized'}), 500
            
        if storage_manager is None:
            return jsonify({'success': False, 'message': 'Storage manager not initialized'}), 500
            
        if camera_id not in RTSP_CAMERAS:
            return jsonify({'success': False, 'message': 'Invalid camera ID'}), 400
        
        # Capture image
        if camera_id == 'camera_1':
            location = camera_service.capture_camera_1()
        elif camera_id == 'camera_2':
            location = camera_service.capture_camera_2()
        else:
            return jsonify({'success': False, 'message': 'Invalid camera ID'}), 400
        
        if location:
            # Add to local storage
            if location.startswith('local:'):
                filepath = location[6:]  # Remove 'local:' prefix
                storage_manager.add_image(filepath)
                
                # Try to upload in background
                try:
                    upload_location = uploader.upload(filepath)
                    if upload_location:
                        storage_manager.mark_as_uploaded(os.path.basename(filepath))
                        location = f"Captured and uploaded: {os.path.basename(filepath)}"
                    else:
                        location = f"Captured locally (upload failed): {os.path.basename(filepath)}"
                except Exception as e:
                    logging.error(f"Upload error: {e}")
                    location = f"Captured locally (upload error): {os.path.basename(filepath)}"
            else:
                location = f"Captured: {location}"
            
            return jsonify({
                'success': True, 
                'message': 'Image captured successfully',
                'location': location
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to capture image'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/images')
def get_images():
    """Get list of local images."""
    global storage_manager
    
    if storage_manager is None:
        return jsonify({'error': 'Storage manager not initialized'}), 500
    
    images = storage_manager.get_images()
    
    return jsonify({
        'images': [
            {
                'filename': img['filename'],
                'size': img['size'],
                'created': img['created'].isoformat(),
                'modified': img['modified'].isoformat(),
                'upload_status': 'uploaded' if storage_manager.is_uploaded(img['filename']) else 'pending'
            }
            for img in images
        ]
    })

@app.route('/api/images/<filename>')
def get_image(filename):
    """Serve image file."""
    try:
        filepath = os.path.join('images', filename)
        if os.path.exists(filepath):
            return send_file(filepath)
        else:
            return jsonify({'error': 'Image not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-queue')
def get_upload_queue():
    """Get upload queue status."""
    global storage_manager
    
    if storage_manager is None:
        return jsonify({'error': 'Storage manager not initialized'}), 500
    
    upload_queue = storage_manager.get_upload_queue()
    
    return jsonify({
        'queue': [
            {
                'filename': img['filename'],
                'size': img['size'],
                'created': img['created'].isoformat()
            }
            for img in upload_queue
        ]
    })

@app.route('/api/force-upload', methods=['POST'])
def force_upload():
    """Force upload of all queued images."""
    global storage_manager, system_status, uploader
    
    if storage_manager is None:
        return jsonify({'success': False, 'message': 'Storage manager not initialized'}), 500
        
    if uploader is None:
        return jsonify({'success': False, 'message': 'Uploader not initialized'}), 500
    
    if not check_internet_connection():
        return jsonify({'success': False, 'message': 'No internet connection'}), 400
    
    uploaded_count = 0
    failed_count = 0
    upload_queue = storage_manager.get_upload_queue()
    
    for img_info in upload_queue:
        try:
            location = uploader.upload(img_info['filepath'])
            if location:
                uploaded_count += 1
                system_status['successful_uploads'] += 1
                # Mark as uploaded but keep in local storage for gallery
                storage_manager.mark_as_uploaded(img_info['filename'])
            else:
                failed_count += 1
                system_status['failed_uploads'] += 1
        except Exception as e:
            failed_count += 1
            system_status['failed_uploads'] += 1
            logging.error(f"Force upload error: {e}")
    
    remaining = storage_manager.get_image_count()
    
    return jsonify({
        'success': True,
        'uploaded': uploaded_count,
        'failed': failed_count,
        'remaining': remaining
    })

@app.route('/api/scan-images', methods=['POST'])
def scan_existing_images():
    """Scan for existing images in the images directory and add them to storage."""
    global storage_manager
    
    if storage_manager is None:
        return jsonify({'success': False, 'message': 'Storage manager not initialized'}), 500
    
    try:
        # Reload images from directory
        storage_manager.images = storage_manager._load_images()
        
        return jsonify({
            'success': True,
            'message': f'Found {len(storage_manager.images)} images',
            'count': len(storage_manager.images)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/gpio-status')
def get_gpio_status():
    """Get GPIO status for all cameras."""
    global gpio_status
    
    # Add detailed debug information
    debug_info = {
        'gpio_available': gpio_service.is_gpio_available(),
        'gpio_service_available': gpio_service.gpio_available,
        'config_gpio_enabled': config.GPIO_ENABLED,
        'gpio_pins': {
            'camera_1': config.GPIO_CAMERA_1_PIN,
            'camera_2': config.GPIO_CAMERA_2_PIN
        }
    }
    
    return jsonify({
        'success': True,
        'gpio_available': gpio_service.is_gpio_available(),
        'gpio_status': gpio_status,
        'debug_info': debug_info
    })

@app.route('/api/gpio-toggle', methods=['POST'])
def toggle_gpio():
    """Toggle GPIO monitoring for a camera."""
    global gpio_status
    
    try:
        data = request.get_json()
        camera_id = data.get('camera_id')
        enabled = data.get('enabled', False)
        
        if camera_id not in ['camera_1', 'camera_2']:
            return jsonify({'success': False, 'message': 'Invalid camera ID'}), 400
        
        if not gpio_service.is_gpio_available():
            # Log detailed GPIO status for debugging
            logging.error(f"GPIO not available. GPIO_AVAILABLE: {gpio_service.gpio_available}")
            logging.error(f"GPIO_ENABLED: {config.GPIO_ENABLED}")
            return jsonify({
                'success': False, 
                'message': 'GPIO not available. Check logs for details.',
                'debug_info': {
                    'gpio_available': gpio_service.gpio_available,
                    'gpio_enabled': config.GPIO_ENABLED
                }
            }), 400
        
        # Update GPIO status
        gpio_status[camera_id] = enabled
        
        logging.info(f"GPIO monitoring {'enabled' if enabled else 'disabled'} for {camera_id}")
        
        return jsonify({
            'success': True,
            'message': f"GPIO monitoring {'enabled' if enabled else 'disabled'} for {camera_id}",
            'gpio_status': gpio_status
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    # Setup logging
    setup_logging(log_level="INFO")
    
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
