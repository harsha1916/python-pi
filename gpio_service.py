"""
GPIO Service for Raspberry Pi Camera Triggers
Handles GPIO pin monitoring for camera capture triggers.
"""
import logging
import threading
import time
from typing import Dict, Callable, Optional
import config

# Try to import RPi.GPIO, handle gracefully if not available
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    # Create a mock GPIO class for non-Raspberry Pi systems
    class MockGPIO:
        BCM = "BCM"
        IN = "IN"
        PUD_UP = "PUD_UP"
        FALLING = "FALLING"
        
        @staticmethod
        def setmode(mode):
            pass
        
        @staticmethod
        def setup(pin, mode, pull_up_down=None):
            pass
        
        @staticmethod
        def add_event_detect(pin, edge, callback=None, bouncetime=None):
            pass
        
        @staticmethod
        def remove_event_detect(pin):
            pass
        
        @staticmethod
        def input(pin):
            return 1  # Return high by default
        
        @staticmethod
        def cleanup():
            pass
    
    GPIO = MockGPIO()

class GPIOService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gpio_available = GPIO_AVAILABLE and config.GPIO_ENABLED
        self.monitoring = False
        self.monitor_thread = None
        self.callbacks: Dict[str, Callable] = {}
        self.pin_states: Dict[int, bool] = {}
        
        # GPIO pin configuration
        self.pins = {
            'camera_1': config.GPIO_CAMERA_1_PIN,
            'camera_2': config.GPIO_CAMERA_2_PIN
        }
        
        if self.gpio_available:
            self._setup_gpio()
        else:
            self.logger.warning("GPIO not available or disabled. Running in mock mode.")
    
    def _setup_gpio(self):
        """Initialize GPIO pins."""
        try:
            GPIO.setmode(GPIO.BCM)
            
            # Setup pins as input with pull-up resistors
            for camera_id, pin in self.pins.items():
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                self.pin_states[pin] = GPIO.input(pin)
                self.logger.info(f"GPIO pin {pin} configured for {camera_id}")
            
            self.logger.info("GPIO setup completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to setup GPIO: {e}")
            self.gpio_available = False
    
    def register_callback(self, camera_id: str, callback: Callable):
        """Register a callback function for camera trigger."""
        if camera_id in self.pins:
            self.callbacks[camera_id] = callback
            self.logger.info(f"Registered callback for {camera_id}")
        else:
            self.logger.error(f"Invalid camera ID: {camera_id}")
    
    def start_monitoring(self):
        """Start monitoring GPIO pins for triggers."""
        if not self.gpio_available:
            self.logger.warning("GPIO not available, cannot start monitoring")
            return
        
        if self.monitoring:
            self.logger.warning("GPIO monitoring already started")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_pins, daemon=True)
        self.monitor_thread.start()
        self.logger.info("GPIO monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring GPIO pins."""
        if not self.monitoring:
            return
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        
        # Remove event detection
        if self.gpio_available:
            for pin in self.pins.values():
                try:
                    GPIO.remove_event_detect(pin)
                except:
                    pass
        
        self.logger.info("GPIO monitoring stopped")
    
    def _monitor_pins(self):
        """Monitor GPIO pins for state changes."""
        while self.monitoring:
            try:
                for camera_id, pin in self.pins.items():
                    if camera_id not in self.callbacks:
                        continue
                    
                    current_state = GPIO.input(pin)
                    previous_state = self.pin_states.get(pin, 1)
                    
                    # Detect falling edge (pin pulled low)
                    if previous_state == 1 and current_state == 0:
                        self.logger.info(f"GPIO trigger detected on pin {pin} for {camera_id}")
                        try:
                            self.callbacks[camera_id]()
                        except Exception as e:
                            self.logger.error(f"Error in GPIO callback for {camera_id}: {e}")
                    
                    self.pin_states[pin] = current_state
                
                time.sleep(0.01)  # Small delay to prevent excessive CPU usage
                
            except Exception as e:
                self.logger.error(f"Error in GPIO monitoring: {e}")
                time.sleep(0.1)
    
    def get_pin_state(self, camera_id: str) -> Optional[bool]:
        """Get current state of GPIO pin for a camera."""
        if not self.gpio_available or camera_id not in self.pins:
            return None
        
        pin = self.pins[camera_id]
        return GPIO.input(pin) == 0  # Return True if pin is low (triggered)
    
    def is_gpio_available(self) -> bool:
        """Check if GPIO is available and enabled."""
        return self.gpio_available
    
    def cleanup(self):
        """Cleanup GPIO resources."""
        self.stop_monitoring()
        if self.gpio_available:
            try:
                GPIO.cleanup()
                self.logger.info("GPIO cleanup completed")
            except Exception as e:
                self.logger.error(f"Error during GPIO cleanup: {e}")

# Global GPIO service instance
gpio_service = GPIOService()
