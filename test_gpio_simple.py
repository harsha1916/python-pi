#!/usr/bin/env python3
"""
Simple GPIO Test Script
Run this on your Raspberry Pi to test GPIO functionality.
"""
import os
import sys

print("🔍 Simple GPIO Test")
print("=" * 30)

# Test 1: Check if we're on Raspberry Pi
try:
    with open('/proc/cpuinfo', 'r') as f:
        cpuinfo = f.read()
        if 'BCM' in cpuinfo or 'Raspberry Pi' in cpuinfo:
            print("✅ Running on Raspberry Pi")
        else:
            print("❌ Not running on Raspberry Pi")
            sys.exit(1)
except:
    print("❌ Cannot read /proc/cpuinfo")
    sys.exit(1)

# Test 2: Check RPi.GPIO import
print("\n📦 Testing RPi.GPIO import...")
try:
    import RPi.GPIO as GPIO
    print("✅ RPi.GPIO imported successfully")
    print(f"   Version: {GPIO.VERSION}")
except ImportError as e:
    print(f"❌ RPi.GPIO import failed: {e}")
    print("   Install with: pip install RPi.GPIO")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)

# Test 3: Check GPIO permissions
print("\n🔐 Testing GPIO permissions...")
try:
    GPIO.setmode(GPIO.BCM)
    print("✅ GPIO.setmode() successful")
    
    # Test pin setup
    test_pin = 18
    GPIO.setup(test_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    print(f"✅ GPIO.setup(pin {test_pin}) successful")
    
    # Test pin read
    value = GPIO.input(test_pin)
    print(f"✅ GPIO.input(pin {test_pin}) = {value}")
    
    # Cleanup
    GPIO.cleanup()
    print("✅ GPIO.cleanup() successful")
    
except PermissionError as e:
    print(f"❌ Permission denied: {e}")
    print("   Fix: sudo usermod -a -G gpio $USER")
    print("   Then logout and login again")
    sys.exit(1)
except Exception as e:
    print(f"❌ GPIO test failed: {e}")
    sys.exit(1)

# Test 4: Check environment variables
print("\n🌍 Checking environment variables...")
gpio_enabled = os.getenv('GPIO_ENABLED', 'NOT_SET')
print(f"   GPIO_ENABLED: {gpio_enabled}")

if gpio_enabled == 'true':
    print("✅ GPIO_ENABLED is set correctly")
else:
    print("❌ GPIO_ENABLED is not set to 'true'")
    print("   Fix: export GPIO_ENABLED=true")

# Test 5: Test config import
print("\n⚙️ Testing config import...")
try:
    import config
    print("✅ Config imported successfully")
    print(f"   config.GPIO_ENABLED: {config.GPIO_ENABLED}")
    print(f"   config.GPIO_CAMERA_1_PIN: {config.GPIO_CAMERA_1_PIN}")
    print(f"   config.GPIO_CAMERA_2_PIN: {config.GPIO_CAMERA_2_PIN}")
except Exception as e:
    print(f"❌ Config import failed: {e}")

print("\n🎉 GPIO test completed!")
print("If all tests passed, GPIO should work in your application.")
