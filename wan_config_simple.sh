#!/bin/bash

# =============================================================================
# Simple WAN Configuration Manager
# Non-root version for basic WAN operations and monitoring
# =============================================================================

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}==========================================${NC}"
}

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

# Function to show help
show_help() {
    cat << EOF
Simple WAN Configuration Manager

USAGE:
    $0 [COMMAND]

COMMANDS:
    status          Show current WAN status (no root required)
    test            Test WAN connectivity (no root required)
    info            Show network information (no root required)
    apply           Apply WAN changes (requires sudo)
    backup          Backup configuration (requires sudo)
    configure       Interactive configuration (requires sudo)

EXAMPLES:
    $0 status       # Show WAN status
    $0 test         # Test connectivity
    $0 apply        # Apply changes (with sudo)
EOF
}

# Function to get WAN status (no root required)
get_wan_status() {
    print_header "WAN Status Check"
    
    # Get WAN protocol from UCI (if accessible)
    if command -v uci >/dev/null 2>&1; then
        local proto=$(uci -q get network.wan.proto 2>/dev/null || echo "unknown")
        local ifname=$(uci -q get network.wan.ifname 2>/dev/null || echo "unknown")
        print_status "WAN Protocol: $proto"
        print_status "WAN Interface: $ifname"
    else
        print_warning "UCI command not available"
    fi
    
    # Check network interfaces
    print_status "Network Interfaces:"
    ip addr show | grep -E "(inet |UP|DOWN)" | head -10
    
    # Check default route
    print_status "Default Route:"
    ip route | grep default || print_warning "No default route found"
    
    # Check WAN connectivity
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        print_success "Internet connectivity: OK"
    else
        print_warning "Internet connectivity: FAILED"
    fi
}

# Function to test connectivity (no root required)
test_connectivity() {
    print_header "Connectivity Test"
    
    # Test DNS
    print_status "Testing DNS resolution..."
    if nslookup google.com >/dev/null 2>&1; then
        print_success "DNS: OK"
    else
        print_warning "DNS: FAILED"
    fi
    
    # Test ping to Google DNS
    print_status "Testing ping to 8.8.8.8..."
    if ping -c 3 8.8.8.8 >/dev/null 2>&1; then
        print_success "Ping: OK"
    else
        print_warning "Ping: FAILED"
    fi
    
    # Test HTTP
    print_status "Testing HTTP connectivity..."
    if curl -s --connect-timeout 5 http://www.google.com >/dev/null 2>&1; then
        print_success "HTTP: OK"
    else
        print_warning "HTTP: FAILED"
    fi
    
    # Show current IP
    print_status "Current WAN IP:"
    curl -s --connect-timeout 5 ifconfig.me 2>/dev/null || echo "Unable to determine external IP"
}

# Function to show network info (no root required)
show_network_info() {
    print_header "Network Information"
    
    print_status "Network Interfaces:"
    ip addr show
    
    print_status "Routing Table:"
    ip route show
    
    print_status "ARP Table:"
    ip neigh show | head -10
    
    print_status "Network Statistics:"
    cat /proc/net/dev | head -5
}

# Function to apply WAN config (requires sudo)
apply_wan_config() {
    print_header "Applying WAN Configuration"
    
    if [ "$EUID" -ne 0 ]; then
        print_error "This operation requires root privileges"
        print_status "Running with sudo..."
        sudo "$0" apply
        return $?
    fi
    
    print_status "Committing UCI changes..."
    uci commit network
    
    print_status "Running network configuration..."
    if [ -x "/usr/sbin/network_config" ]; then
        /usr/sbin/network_config
    else
        /etc/init.d/network restart
    fi
    
    print_status "Reloading network services..."
    /usr/sbin/luci-reload network
    
    print_success "WAN configuration applied"
}

# Function to backup config (requires sudo)
backup_config() {
    print_header "Backing Up Configuration"
    
    if [ "$EUID" -ne 0 ]; then
        print_error "This operation requires root privileges"
        print_status "Running with sudo..."
        sudo "$0" backup
        return $?
    fi
    
    local backup_dir="/home/admin/wan-backups"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$backup_dir/wan_backup_$timestamp.tar.gz"
    
    mkdir -p "$backup_dir"
    
    print_status "Creating backup: $backup_file"
    tar -czf "$backup_file" /etc/config/network /etc/config/wireless /etc/config/firewall 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "Backup created: $backup_file"
    else
        print_error "Backup failed"
    fi
}

# Function for interactive configuration (requires sudo)
configure_interactive() {
    print_header "Interactive WAN Configuration"
    
    if [ "$EUID" -ne 0 ]; then
        print_error "This operation requires root privileges"
        print_status "Running with sudo..."
        sudo "$0" configure
        return $?
    fi
    
    print_status "Current WAN configuration:"
    uci show network.wan
    
    echo
    print_status "Available protocols:"
    echo "1) dhcp (automatic)"
    echo "2) static (manual IP)"
    echo "3) pppoe"
    echo "4) lte (3G/4G)"
    
    read -p "Select protocol (1-4): " choice
    
    case $choice in
        1)
            uci set network.wan.proto=dhcp
            uci delete network.wan.ipaddr 2>/dev/null
            uci delete network.wan.netmask 2>/dev/null
            uci delete network.wan.gateway 2>/dev/null
            ;;
        2)
            uci set network.wan.proto=static
            read -p "Enter IP address: " ip
            read -p "Enter netmask: " mask
            read -p "Enter gateway: " gw
            uci set network.wan.ipaddr="$ip"
            uci set network.wan.netmask="$mask"
            uci set network.wan.gateway="$gw"
            ;;
        3)
            uci set network.wan.proto=pppoe
            read -p "Enter username: " user
            read -p "Enter password: " pass
            uci set network.wan.username="$user"
            uci set network.wan.password="$pass"
            ;;
        4)
            uci set network.wan.proto=lte
            ;;
        *)
            print_error "Invalid choice"
            return 1
            ;;
    esac
    
    print_success "Configuration updated"
    print_status "Run 'apply' to apply changes"
}

# Main function
main() {
    case "${1:-help}" in
        status)
            get_wan_status
            ;;
        test)
            test_connectivity
            ;;
        info)
            show_network_info
            ;;
        apply)
            apply_wan_config
            ;;
        backup)
            backup_config
            ;;
        configure)
            configure_interactive
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
