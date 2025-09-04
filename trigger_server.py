#!/usr/bin/env python3
"""
TCP Server for handling RFID triggers.
Handles external trigger commands via TCP connections.
"""
import socketserver
import sys
import signal
import logging
import threading
from datetime import datetime
from config import BIND_IP, BIND_PORT
from capture_service import CameraService

class TriggerHandler(socketserver.BaseRequestHandler):
    """Handle incoming trigger connections."""
    
    def __init__(self, request, client_address, server):
        self.camera_service = CameraService()
        super().__init__(request, client_address, server)
    
    def handle(self):
        """Handle incoming trigger data."""
        peer_ip, peer_port = self.client_address
        logger = logging.getLogger(__name__)
        
        logger.info(f"Connected from {peer_ip}:{peer_port}")
        self.request.settimeout(60)
        
        try:
            while True:
                chunk = self.request.recv(4096)
                if not chunk:
                    break
                
                # Process trigger data
                trigger_data = chunk.decode('utf-8', errors='ignore').strip()
                logger.info(f"Received trigger: {trigger_data}")
                
                # Parse trigger and capture appropriate camera
                if self._process_trigger(trigger_data):
                    logger.info("Trigger processed successfully")
                else:
                    logger.warning("Failed to process trigger")
                    
        except Exception as e:
            logger.error(f"Error handling trigger: {e}")
        finally:
            logger.info(f"Disconnected from {peer_ip}:{peer_port}")
    
    def _process_trigger(self, trigger_data: str) -> bool:
        """Process trigger data and capture appropriate camera."""
        try:
            # Simple trigger parsing - can be enhanced based on actual protocol
            if "camera_1" in trigger_data.lower() or "rfid_1" in trigger_data.lower():
                location = self.camera_service.capture_camera_1()
                return location is not None
            elif "camera_2" in trigger_data.lower() or "rfid_2" in trigger_data.lower():
                location = self.camera_service.capture_camera_2()
                return location is not None
            else:
                # Default to camera 1
                location = self.camera_service.capture_camera_1()
                return location is not None
        except Exception as e:
            logging.getLogger(__name__).error(f"Error processing trigger: {e}")
            return False

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Threaded TCP server for handling multiple connections."""
    allow_reuse_address = True
    daemon_threads = True

def main():
    """Main server function."""
    from logging_config import setup_logging
    
    # Setup logging
    setup_logging(log_level="INFO")
    logger = logging.getLogger(__name__)
    
    server = ThreadedTCPServer((BIND_IP, BIND_PORT), TriggerHandler)

    def shutdown(*_):
        logger.info("Shutting down server...")
        try:
            server.shutdown()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        server.server_close()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    logger.info(f"Trigger server listening on {BIND_IP}:{BIND_PORT}")
    logger.info(
        "Trigger format examples:\n"
        "  camera_1 or rfid_1 -> triggers camera 1\n"
        "  camera_2 or rfid_2 -> triggers camera 2\n"
        "  any other text -> defaults to camera 1"
    )
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        shutdown()

if __name__ == "__main__":
    main()
