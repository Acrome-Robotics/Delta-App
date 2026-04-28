#!/bin/bash

# ==========================================
#  Acrome Delta API — Raspberry Pi Setup
# ==========================================
#
#  Run this script on your Raspberry Pi:
#    cd Delta-App/deploy
#    bash setup.sh
#
#  After installation, from any terminal:
#    delta start    -> Start the API server
#    delta stop     -> Stop the API server
#    delta status   -> Check if API is running
#    delta log      -> Follow API logs in real-time
# ==========================================

set -e  # Exit on error

# Detect the directory this script lives in (deploy/)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# Find the project root (one level above deploy/)
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
# API directory
API_DIR="$PROJECT_DIR/api"

echo ""
echo "=========================================="
echo " Acrome Delta API — Setup Starting"
echo "=========================================="
echo " Project dir : $PROJECT_DIR"
echo " API dir     : $API_DIR"
echo "=========================================="
echo ""

# Make sure the API directory exists
if [ ! -f "$API_DIR/app.py" ]; then
    echo "ERROR: $API_DIR/app.py not found!"
    echo "Make sure you are running this script from the Delta-App/deploy/ directory."
    exit 1
fi

# 1. Check internet connectivity
echo "[1/4] Checking internet connection..."
if ! ping -c 1 -W 3 pypi.org &> /dev/null; then
    echo ""
    echo "=========================================="
    echo " ❌ ERROR: No internet connection!"
    echo "=========================================="
    echo " Setup requires internet to download Python packages."
    echo " Please connect to the internet and try again:"
    echo "   bash setup.sh"
    echo "=========================================="
    exit 1
fi
echo "  ✅ Internet connection OK."

# 2. Create virtual environment
echo "[2/4] Creating Python virtual environment..."
python3 -m venv "$API_DIR/venv"

# 3. Install dependencies
echo "[3/4] Installing Python dependencies..."
"$API_DIR/venv/bin/pip" install --upgrade pip
"$API_DIR/venv/bin/pip" install -r "$API_DIR/requirements.txt"

# 4. Create global 'delta' command
echo "[4/4] Installing 'delta' command globally..."

sudo tee /usr/local/bin/delta > /dev/null << 'CMDEOF'
#!/bin/bash

# ---- Configuration (auto-generated) ----
API_DIR="PLACEHOLDER_API_DIR"
PYTHON="$API_DIR/venv/bin/python3"
PID_FILE="$API_DIR/.delta_api.pid"
# -----------------------------------------

case "$1" in
    start)
        # Check if already running
        if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            echo "Delta API is already running (PID: $(cat "$PID_FILE"))"
            echo "To stop it: delta stop"
            exit 0
        fi

        echo "Starting Acrome Delta API..."
        cd "$API_DIR"
        nohup "$PYTHON" app.py > "$API_DIR/api.log" 2>&1 &
        echo $! > "$PID_FILE"
        sleep 1

        if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            echo ""
            echo "=========================================="
            echo " ✅ Delta API started successfully!"
            echo "=========================================="
            echo " PID     : $(cat "$PID_FILE")"
            echo " Log     : $API_DIR/api.log"
            echo " Address : http://0.0.0.0:5000"
            echo ""
            echo " To stop     : delta stop"
            echo " To view log : delta log"
            echo "=========================================="
        else
            echo "ERROR: Failed to start the API. Check the log:"
            echo "  cat $API_DIR/api.log"
            rm -f "$PID_FILE"
            exit 1
        fi
        ;;

    stop)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                kill "$PID"
                rm -f "$PID_FILE"
                echo "✅ Delta API stopped (PID: $PID)"
            else
                echo "API was not running (stale PID file removed)."
                rm -f "$PID_FILE"
            fi
        else
            echo "API is not running."
        fi
        ;;

    status)
        if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            echo "✅ Delta API is running (PID: $(cat "$PID_FILE"))"
        else
            echo "❌ Delta API is not running."
            rm -f "$PID_FILE" 2>/dev/null
        fi
        ;;

    log)
        if [ -f "$API_DIR/api.log" ]; then
            tail -f "$API_DIR/api.log"
        else
            echo "No log file yet. Start the API first: delta start"
        fi
        ;;

    *)
        echo ""
        echo "=========================================="
        echo "  Acrome Delta Robot — Control Center"
        echo "=========================================="
        echo ""
        echo "  Usage:"
        echo "    delta start    Start the API server"
        echo "    delta stop     Stop the API server"
        echo "    delta status   Check if API is running"
        echo "    delta log      Follow API logs in real-time"
        echo ""
        ;;
esac
CMDEOF

# Replace placeholder with the actual API directory path
sudo sed -i "s|PLACEHOLDER_API_DIR|$API_DIR|g" /usr/local/bin/delta
sudo chmod +x /usr/local/bin/delta

echo ""
echo "=========================================="
echo " ✅ SETUP COMPLETED SUCCESSFULLY!"
echo "=========================================="
echo ""
echo " You can now use these commands from any terminal:"
echo ""
echo "   delta start    ->  Start the API"
echo "   delta stop     ->  Stop the API"
echo "   delta status   ->  Check status"
echo "   delta log      ->  View logs"
echo ""
