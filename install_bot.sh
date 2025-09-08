#!/bin/bash

# =============================================================================
# Loranet Deployment Bot Installation Script
# =============================================================================
# This script installs the Python dependencies and sets up the deployment bot
# 
# Author: Aqmar
# Date: $(date +%Y-%m-%d)
# =============================================================================

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo
    echo "=========================================="
    echo -e "${YELLOW}$1${NC}"
    echo "=========================================="
}

# Check if Python 3 is installed
check_python() {
    if ! command -v python3 >/dev/null 2>&1; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    print_success "Python $python_version found"
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Install pip if not available
    if ! command -v pip3 >/dev/null 2>&1; then
        print_status "Installing pip3..."
        sudo apt update
        sudo apt install -y python3-pip
    fi
    
    # Install required packages
    pip3 install -r requirements.txt
    
    print_success "Dependencies installed successfully"
}

# Make bot executable
setup_bot() {
    print_status "Setting up deployment bot..."
    
    chmod +x loranet_deployment_bot.py
    
    print_success "Bot setup completed"
}

# Create example usage script
create_example_script() {
    print_status "Creating example usage script..."
    
    cat > run_bot_example.sh << 'EOF'
#!/bin/bash

# Example usage of Loranet Deployment Bot

echo "Loranet Deployment Bot - Example Usage"
echo "======================================"

# Example 1: Discover devices only
echo "1. Discovering devices on network..."
python3 loranet_deployment_bot.py --discover-only

echo
echo "2. Deploy to discovered devices (auto mode)..."
python3 loranet_deployment_bot.py --mode auto

echo
echo "3. Deploy with custom network range..."
python3 loranet_deployment_bot.py --network 192.168.0.0/24 --mode auto

echo
echo "4. Deploy with custom credentials..."
python3 loranet_deployment_bot.py --username admin --password admin123 --mode auto

echo
echo "5. Deploy with custom MAC prefixes..."
python3 loranet_deployment_bot.py --mac-prefix 00:52:24 --mac-prefix 02:52:24 --mode auto
EOF
    
    chmod +x run_bot_example.sh
    print_success "Example script created: run_bot_example.sh"
}

# Main installation
main() {
    print_section "LORANET DEPLOYMENT BOT INSTALLATION"
    
    check_python
    install_dependencies
    setup_bot
    create_example_script
    
    print_section "INSTALLATION COMPLETED"
    print_success "Loranet Deployment Bot is ready to use!"
    echo
    print_status "Usage examples:"
    echo "  python3 loranet_deployment_bot.py --discover-only"
    echo "  python3 loranet_deployment_bot.py --mode auto"
    echo "  python3 loranet_deployment_bot.py --help"
    echo
    print_status "Configuration file: bot_config.json"
    print_status "Example script: run_bot_example.sh"
}

main "$@"
