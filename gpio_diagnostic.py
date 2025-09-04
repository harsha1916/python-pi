#!/usr/bin/env python3
"""
GPIO Diagnostic Script for Raspberry Pi
Run this script to diagnose GPIO availability issues.
"""
import os
import sys

def check_gpio_availability():
    """Check GPIO availability and configuration."""
    print("🔍 GPIO Diagnostic Tool")
    print("=" * 50)
    
    # Check 1: Python version
    print(f"✅ Python version: {sys.version}")
    
    # Check 2: RPi.GPIO import
    print("\n📦 Checking RPi.GPIO import...")
    try:
        import RPi.GPIO as GPIO
        print("✅ RPi.GPIO imported successfully")
        print(f"   RPi.GPIO version: {GPIO.VERSION}")
    except ImportError as e:
        print(f"❌ RPi.GPIO import failed: {e}")
        print("   Solution: pip install RPi.GPIO")
        return False
    except Exception as e:
        print(f"❌ Unexpected error importing RPi.GPIO: {e}")
        return False
    
    # Check 3: GPIO permissions
    print("\n🔐 Checking GPIO permissions...")
    gpio_devices = ['/dev/gpiomem', '/dev/mem']
    for device in gpio_devices:
        if os.path.exists(device):
            stat = os.stat(device)
            print(f"✅ {device} exists")
            print(f"   Permissions: {oct(stat.st_mode)}")
            print(f"   Owner: {stat.st_uid}")
        else:
            print(f"❌ {device} not found")
    
    # Check 4: User groups
    print("\n👥 Checking user groups...")
    try:
        import grp
        import pwd
        
        current_user = pwd.getpwuid(os.getuid()).pw_name
        user_groups = [grp.getgrgid(g).gr_name for g in os.getgroups()]
        
        print(f"✅ Current user: {current_user}")
        print(f"✅ User groups: {', '.join(user_groups)}")
        
        if 'gpio' in user_groups:
            print("✅ User is in 'gpio' group")
        else:
            print("❌ User is NOT in 'gpio' group")
            print("   Solution: sudo usermod -a -G gpio $USER")
            print("   Then logout and login again")
    except Exception as e:
        print(f"❌ Error checking groups: {e}")
    
    # Check 5: Environment variables
    print("\n🌍 Checking environment variables...")
    gpio_enabled = os.getenv('GPIO_ENABLED', 'false').lower()
    camera_1_pin = os.getenv('GPIO_CAMERA_1_PIN', '18')
    camera_2_pin = os.getenv('GPIO_CAMERA_2_PIN', '19')
    
    print(f"   GPIO_ENABLED: {gpio_enabled}")
    print(f"   GPIO_CAMERA_1_PIN: {camera_1_pin}")
    print(f"   GPIO_CAMERA_2_PIN: {camera_2_pin}")
    
    if gpio_enabled == 'true':
        print("✅ GPIO_ENABLED is set to true")
    else:
        print("❌ GPIO_ENABLED is not set to true")
        print("   Solution: export GPIO_ENABLED=true")
    
    # Check 6: Config import
    print("\n⚙️ Checking config import...")
    try:
        import config
        print("✅ Config module imported successfully")
        print(f"   config.GPIO_ENABLED: {config.GPIO_ENABLED}")
        print(f"   config.GPIO_CAMERA_1_PIN: {config.GPIO_CAMERA_1_PIN}")
        print(f"   config.GPIO_CAMERA_2_PIN: {config.GPIO_CAMERA_2_PIN}")
    except Exception as e:
        print(f"❌ Error importing config: {e}")
    
    # Check 7: GPIO service import
    print("\n🔧 Checking GPIO service...")
    try:
        from gpio_service import gpio_service
        print("✅ GPIO service imported successfully")
        print(f"   gpio_service.is_gpio_available(): {gpio_service.is_gpio_available()}")
        print(f"   gpio_service.gpio_available: {gpio_service.gpio_available}")
    except Exception as e:
        print(f"❌ Error importing GPIO service: {e}")
    
    # Check 8: Test GPIO setup
    print("\n🧪 Testing GPIO setup...")
    try:
        GPIO.setmode(GPIO.BCM)
        print("✅ GPIO.setmode(GPIO.BCM) successful")
        
        # Test pin setup
        test_pin = 18
        GPIO.setup(test_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        print(f"✅ GPIO.setup(pin {test_pin}) successful")
        
        # Test pin read
        pin_value = GPIO.input(test_pin)
        print(f"✅ GPIO.input(pin {test_pin}) = {pin_value}")
        
        # Cleanup
        GPIO.cleanup()
        print("✅ GPIO.cleanup() successful")
        
    except Exception as e:
        print(f"❌ GPIO setup test failed: {e}")
        return False
    
    print("\n🎉 GPIO diagnostic completed!")
    return True

if __name__ == "__main__":
    success = check_gpio_availability()
    if success:
        print("\n✅ GPIO appears to be working correctly!")
        print("   If you're still having issues, check the web application logs.")
    else:
        print("\n❌ GPIO has issues that need to be resolved.")
        print("   Please fix the issues above and run this script again.")
