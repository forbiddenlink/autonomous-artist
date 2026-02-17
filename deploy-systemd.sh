#!/bin/bash
# Deploy with systemd for production Linux servers

set -e

echo "════════════════════════════════════════════════════════════"
echo "  Systemd Deployment Script"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root or with sudo"
    exit 1
fi

APP_DIR="/opt/autonomous-artist"
SERVICE_FILE="/etc/systemd/system/autonomous-artist.service"
LOG_DIR="/var/log/autonomous-artist"

# Create application directory
echo "Creating application directory..."
mkdir -p $APP_DIR
mkdir -p $LOG_DIR

# Copy files (assuming we're in the source directory)
echo "Copying application files..."
cp -r . $APP_DIR/
cd $APP_DIR

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create application user
if ! id -u artist > /dev/null 2>&1; then
    echo "Creating 'artist' user..."
    useradd -r -s /bin/false -d $APP_DIR artist
fi

# Set permissions
echo "Setting permissions..."
chown -R artist:artist $APP_DIR
chown -R artist:artist $LOG_DIR
chmod 750 $APP_DIR
chmod 770 $LOG_DIR

# Install systemd service
echo "Installing systemd service..."
cp autonomous-artist.service $SERVICE_FILE
systemctl daemon-reload

# Enable and start service
echo "Starting service..."
systemctl enable autonomous-artist
systemctl restart autonomous-artist

# Wait for service to start
sleep 5

# Check status
if systemctl is-active --quiet autonomous-artist; then
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "  ✅ DEPLOYMENT SUCCESSFUL!"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "Service Status:"
    systemctl status autonomous-artist --no-pager
    echo ""
    echo "Useful commands:"
    echo "  - View logs: journalctl -u autonomous-artist -f"
    echo "  - Restart: systemctl restart autonomous-artist"
    echo "  - Stop: systemctl stop autonomous-artist"
    echo "  - Check status: systemctl status autonomous-artist"
    echo ""
else
    echo ""
    echo "❌ Service failed to start. Checking logs..."
    journalctl -u autonomous-artist --no-pager -n 50
    exit 1
fi
