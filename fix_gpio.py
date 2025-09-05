#!/usr/bin/env python3
"""
Quick GPIO Fix Script
Run this on your Raspberry Pi to enable GPIO.
"""
import os

print("🔧 Quick GPIO Fix")
print("=" * 20)

# Set environment variables
os.environ['GPIO_ENABLED'] = 'true'
os.environ['GPIO_CAMERA_1_PIN'] = '18'
os.environ['GPIO_CAMERA_2_PIN'] = '19'

print("✅ Environment variables set:")
print(f"   GPIO_ENABLED: {os.environ.get('GPIO_ENABLED')}")
print(f"   GPIO_CAMERA_1_PIN: {os.environ.get('GPIO_CAMERA_1_PIN')}")
print(f"   GPIO_CAMERA_2_PIN: {os.environ.get('GPIO_CAMERA_2_PIN')}")

# Test config import
try:
    import config
    print(f"✅ Config imported successfully")
    print(f"   config.GPIO_ENABLED: {config.GPIO_ENABLED}")
except Exception as e:
    print(f"❌ Config import failed: {e}")

# Test GPIO service
try:
    from gpio_service import gpio_service
    print(f"✅ GPIO service imported")
    print(f"   gpio_service.is_gpio_available(): {gpio_service.is_gpio_available()}")
except Exception as e:
    print(f"❌ GPIO service import failed: {e}")

print("\n🎉 GPIO fix completed!")
print("Now restart your web application: python start_web.py")
