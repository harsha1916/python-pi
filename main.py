import logging
from capture_service import CameraService
from logging_config import setup_logging

def main():
    """Main function to demonstrate camera service."""
    # Setup logging
    setup_logging(log_level="INFO")
    logger = logging.getLogger(__name__)
    
    logger.info("Starting camera service...")
    
    try:
        cam = CameraService()
        
        # Simulate individual camera triggers
        logger.info("Triggering camera 1...")
        location = cam.capture_camera_1()  # Trigger from RFID 1
        
        if location:
            logger.info(f"Camera 1 capture successful. Location: {location}")
        else:
            logger.error("Camera 1 capture failed")
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main()

