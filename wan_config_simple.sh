#!/bin/bash

# =============================================================================
# Simple WAN Configuration Manager
# Non-root version for basic WAN operations and monitoring
# Includes LAN configuration fixes and improved error handling
# Version: 2.0
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
    fix-lan         Fix LAN configuration issues (requires sudo)

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

# Function to clean up empty routes
cleanup_empty_routes() {
    print_status "Cleaning up empty routes..."
    
    # Remove all empty default routes
    ip route show | grep "default via $" | while read route; do
        ip route del $route 2>/dev/null || true
    done
    
    # Remove routes with empty gateway
    ip route show | grep "default via  metric" | while read route; do
        ip route del $route 2>/dev/null || true
    done
    
    # Remove routes with empty dev
    ip route show | grep "default via.*dev $" | while read route; do
        ip route del $route 2>/dev/null || true
    done
    
    # Add proper default route if WAN is configured
    local wan_gateway=$(uci -q get network.wan.gateway 2>/dev/null)
    local wan_ifname=$(uci -q get network.wan.ifname 2>/dev/null)
    
    if [ -n "$wan_gateway" ] && [ "$wan_gateway" != "" ] && [ -n "$wan_ifname" ]; then
        print_status "Adding default route via $wan_gateway dev $wan_ifname"
        ip route add default via "$wan_gateway" dev "$wan_ifname" 2>/dev/null || true
    fi
    
    print_success "Route cleanup completed"
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
    uci commit network 2>/dev/null || true
    
    # Clean up empty routes before applying configuration
    cleanup_empty_routes
    
    print_status "Running network configuration..."
    if [ -x "/usr/sbin/network_config" ]; then
        /usr/sbin/network_config 2>/dev/null || true
    else
        /etc/init.d/network restart 2>/dev/null || true
    fi
    
    print_status "Reloading network services..."
    if [ -x "/usr/sbin/luci-reload" ]; then
        # Create a dummy lock command if it doesn't exist
        if ! command -v lock >/dev/null 2>&1; then
            print_status "Creating temporary lock command..."
            echo '#!/bin/sh\necho "lock: dummy command"' > /tmp/lock
            chmod +x /tmp/lock
            export PATH="/tmp:$PATH"
        fi
        /usr/sbin/luci-reload network 2>/dev/null || true
    else
        print_warning "luci-reload not found, using network restart"
        /etc/init.d/network restart 2>/dev/null || true
    fi
    
    # Final cleanup of empty routes after configuration
    print_status "Performing final route cleanup..."
    cleanup_empty_routes
    
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

# Function to fix LAN configuration issues
fix_lan_configuration() {
    print_header "Fixing LAN Configuration Issues"
    
    if [ "$EUID" -ne 0 ]; then
        print_error "This operation requires root privileges"
        print_status "Running with sudo..."
        sudo "$0" fix-lan
        return $?
    fi
    
    # Check current LAN configuration
    local lan_proto=$(uci -q get network.lan.proto 2>/dev/null || echo "unknown")
    local lan_ifname=$(uci -q get network.lan.ifname 2>/dev/null || echo "unknown")
    
    print_status "Current LAN protocol: $lan_proto"
    print_status "Current LAN interfaces: $lan_ifname"
    
    # Fix LAN protocol if it's set to DHCP (should be static)
    if [ "$lan_proto" = "dhcp" ]; then
        print_warning "LAN protocol is set to DHCP, fixing to static..."
        uci set network.lan.proto='static'
        print_success "LAN protocol fixed to static"
    fi
    
    # Fix LAN interfaces if wlan0 is missing
    if [[ "$lan_ifname" != *"wlan0"* ]]; then
        print_warning "LAN interface missing wlan0, adding it..."
        uci set network.lan.ifname='eth0 wlan0'
        print_success "LAN interfaces updated to include wlan0"
    fi
    
    # Commit changes
    uci commit network
    print_success "LAN configuration fixes applied"
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
        fix-lan)
            fix_lan_configuration
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
