#!/bin/bash
# GPIO Setup Script for Raspberry Pi
# Run this script on your Raspberry Pi to fix GPIO issues

echo "🔧 GPIO Setup Script for Raspberry Pi"
echo "====================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Don't run this script as root (sudo)"
    echo "   Run as regular user: ./setup_gpio.sh"
    exit 1
fi

echo "✅ Running as user: $(whoami)"

# Step 1: Install RPi.GPIO
echo ""
echo "📦 Installing RPi.GPIO..."
pip3 install RPi.GPIO

# Step 2: Add user to gpio group
echo ""
echo "👥 Adding user to gpio group..."
sudo usermod -a -G gpio $USER

# Step 3: Set environment variables
echo ""
echo "🌍 Setting environment variables..."
echo "export GPIO_ENABLED=true" >> ~/.bashrc
echo "export GPIO_CAMERA_1_PIN=18" >> ~/.bashrc
echo "export GPIO_CAMERA_2_PIN=19" >> ~/.bashrc

# Step 4: Create .env file
echo ""
echo "📝 Creating .env file..."
cat > .env << EOF
# GPIO Configuration
GPIO_ENABLED=true
GPIO_CAMERA_1_PIN=18
GPIO_CAMERA_2_PIN=19

# Camera Configuration
CAMERA_USERNAME=admin
CAMERA_PASSWORD=admin
CAMERA_1_IP=192.168.1.201
CAMERA_2_IP=192.168.1.202

# API Configuration
S3_API_URL=https://api.easyparkai.com/api/Common/Upload?modulename=anpr

# Server Configuration
BIND_IP=0.0.0.0
BIND_PORT=5000
EOF

# Step 5: Check GPIO device files
echo ""
echo "🔍 Checking GPIO device files..."
if [ -e /dev/gpiomem ]; then
    echo "✅ /dev/gpiomem exists"
    ls -la /dev/gpiomem
else
    echo "❌ /dev/gpiomem not found"
    echo "   You may need to enable GPIO in raspi-config"
fi

# Step 6: Test GPIO
echo ""
echo "🧪 Testing GPIO..."
python3 test_gpio_simple.py

echo ""
echo "🎉 Setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Logout and login again (or restart Pi) for group changes to take effect"
echo "2. Run: source ~/.bashrc (to load environment variables)"
echo "3. Test your application: python start_web.py"
echo ""
echo "🔧 If GPIO still doesn't work:"
echo "1. Run: sudo raspi-config"
echo "2. Go to: Advanced Options > GPIO > Enable"
echo "3. Reboot your Pi"
