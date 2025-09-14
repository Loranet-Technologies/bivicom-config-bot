#!/bin/bash

# =============================================================================
# Network Configuration Script
# =============================================================================
# Essential functions for network configuration and SSH deployment
# 
# Author: Aqmar
# Date: $(date +%Y-%m-%d)
# Version: 2.0
# =============================================================================

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Remote deployment variables
REMOTE_HOST=""
REMOTE_USER="admin"
REMOTE_PASSWORD="admin"
REMOTE_SSH_KEY=""
USE_SSH=false
PINGED_REMOTE=false

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Function to print colored output
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

# Function to ping remote host before SSH operations (only once per session)
ping_remote_host() {
    if [ "$USE_SSH" = true ] && [ -n "$REMOTE_HOST" ] && [ "$PINGED_REMOTE" = false ]; then
        print_status "Pinging remote host $REMOTE_HOST..."
        if ping -c 3 -W 5 "$REMOTE_HOST" >/dev/null 2>&1; then
            print_success "Remote host $REMOTE_HOST is reachable"
            PINGED_REMOTE=true
            return 0
        else
            print_error "Remote host $REMOTE_HOST is not reachable"
            print_error "Please check network connectivity and IP address"
            return 1
        fi
    elif [ "$PINGED_REMOTE" = true ]; then
        # Already pinged successfully, skip
        return 0
    else
        return 0  # No remote host to ping
    fi
}

# Function to check if UCI is available
check_uci_available() {
    if [ "$USE_SSH" = true ] && [ -n "$REMOTE_HOST" ]; then
        if [ -n "$REMOTE_SSH_KEY" ]; then
            ssh -i "$REMOTE_SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "which uci >/dev/null 2>&1"
        else
            sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "which uci >/dev/null 2>&1"
        fi
    else
        which uci >/dev/null 2>&1
    fi
}

# Function to execute commands locally or via SSH
execute_command() {
    local cmd="$1"
    local description="$2"
    local max_retries=3
    local retry_count=0
    
    if [ "$USE_SSH" = true ] && [ -n "$REMOTE_HOST" ]; then
        print_status "Executing on $REMOTE_HOST: $description"
        
        while [ $retry_count -lt $max_retries ]; do
            if [ -n "$REMOTE_SSH_KEY" ]; then
                ssh -i "$REMOTE_SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$REMOTE_USER@$REMOTE_HOST" "$cmd"
            else
                sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$REMOTE_USER@$REMOTE_HOST" "$cmd"
            fi
            
            local exit_code=$?
            if [ $exit_code -eq 0 ]; then
                return 0
            elif [ $exit_code -eq 255 ]; then
                # SSH connection error, retry
                retry_count=$((retry_count + 1))
                if [ $retry_count -lt $max_retries ]; then
                    print_warning "SSH connection failed, retrying in 2 seconds... (attempt $retry_count/$max_retries)"
                    sleep 2
                else
                    print_error "SSH connection failed after $max_retries attempts"
                    return $exit_code
                fi
            else
                # Command execution error, don't retry
                return $exit_code
            fi
        done
    else
        print_status "Executing locally: $description"
        eval "$cmd"
    fi
}

# Function to copy files locally or via SSH
copy_to_remote() {
    local local_file="$1"
    local remote_path="$2"
    
    if [ "$USE_SSH" = true ] && [ -n "$REMOTE_HOST" ]; then
        print_status "Copying $local_file to $REMOTE_HOST:$remote_path"
        if [ -n "$REMOTE_SSH_KEY" ]; then
            scp -i "$REMOTE_SSH_KEY" -o StrictHostKeyChecking=no "$local_file" "$REMOTE_USER@$REMOTE_HOST:$remote_path"
        else
            sshpass -p "$REMOTE_PASSWORD" scp -o StrictHostKeyChecking=no "$local_file" "$REMOTE_USER@$REMOTE_HOST:$remote_path"
        fi
    else
        print_status "Copying $local_file to $remote_path (local)"
        cp "$local_file" "$remote_path"
    fi
}

# Function to check if we should use SSH
check_ssh_mode() {
    if [ "$1" = "--remote" ] && [ -n "$2" ]; then
        USE_SSH=true
        REMOTE_HOST="$2"
        if [ -n "$3" ]; then
            REMOTE_USER="$3"
        fi
        if [ -n "$4" ]; then
            # Check if parameter 4 is an SSH key file or password
            if [ -f "$4" ]; then
                REMOTE_SSH_KEY="$4"
                print_success "Remote deployment mode enabled for $REMOTE_HOST with SSH key authentication"
            else
                REMOTE_PASSWORD="$4"
                print_success "Remote deployment mode enabled for $REMOTE_HOST with password authentication"
            fi
        fi
        if [ -n "$5" ] && [ -z "$REMOTE_SSH_KEY" ]; then
            # Only set password if SSH key wasn't already set
            REMOTE_PASSWORD="$5"
        fi
    fi
}

# =============================================================================
# NETWORK CONFIGURATION FUNCTIONS
# =============================================================================

# Function to configure network settings FORWARD: WAN=eth1 (DHCP), LAN=eth0 (Static)
configure_network_settings_forward() {
    print_status "Configuring network settings FORWARD (NO REBOOT)"
    
    # Ping remote host once (if using SSH)
    if [ "$USE_SSH" = true ] && [ -n "$REMOTE_HOST" ]; then
        if ! ping_remote_host; then
            print_error "Cannot configure network: Remote host is not reachable"
            return 1
        fi
    fi
    
    # Check if UCI is available
    if ! check_uci_available; then
        print_error "UCI command not found! This device may not be running OpenWrt."
        print_error "Please ensure the target device is running OpenWrt with UCI installed."
        return 1
    fi
    
    print_success "UCI is available, proceeding with network configuration..."
    
    # Check if network is already configured correctly
    print_status "Checking current network configuration..."
    local current_wan_proto
    local current_wan_ifname
    local current_lan_proto
    local current_lan_ifname
    local current_lan_ip
    
    if [ "$USE_SSH" = true ] && [ -n "$REMOTE_HOST" ]; then
        # Use direct SSH commands to avoid log message contamination
        if [ -n "$REMOTE_SSH_KEY" ]; then
            current_wan_proto=$(ssh -i "$REMOTE_SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "sudo uci get network.wan.proto 2>/dev/null || echo 'not_set'" 2>/dev/null)
            current_wan_ifname=$(ssh -i "$REMOTE_SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "sudo uci get network.wan.ifname 2>/dev/null || echo 'not_set'" 2>/dev/null)
            current_lan_proto=$(ssh -i "$REMOTE_SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "sudo uci get network.lan.proto 2>/dev/null || echo 'not_set'" 2>/dev/null)
            current_lan_ifname=$(ssh -i "$REMOTE_SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "sudo uci get network.lan.ifname 2>/dev/null || echo 'not_set'" 2>/dev/null)
            current_lan_ip=$(ssh -i "$REMOTE_SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "sudo uci get network.lan.ipaddr 2>/dev/null || echo 'not_set'" 2>/dev/null)
        else
            current_wan_proto=$(sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "sudo uci get network.wan.proto 2>/dev/null || echo 'not_set'" 2>/dev/null)
            current_wan_ifname=$(sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "sudo uci get network.wan.ifname 2>/dev/null || echo 'not_set'" 2>/dev/null)
            current_lan_proto=$(sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "sudo uci get network.lan.proto 2>/dev/null || echo 'not_set'" 2>/dev/null)
            current_lan_ifname=$(sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "sudo uci get network.lan.ifname 2>/dev/null || echo 'not_set'" 2>/dev/null)
            current_lan_ip=$(sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "sudo uci get network.lan.ipaddr 2>/dev/null || echo 'not_set'" 2>/dev/null)
        fi
    else
        # Use direct commands for local execution
        current_wan_proto=$(sudo uci get network.wan.proto 2>/dev/null || echo 'not_set')
        current_wan_ifname=$(sudo uci get network.wan.ifname 2>/dev/null || echo 'not_set')
        current_lan_proto=$(sudo uci get network.lan.proto 2>/dev/null || echo 'not_set')
        current_lan_ifname=$(sudo uci get network.lan.ifname 2>/dev/null || echo 'not_set')
        current_lan_ip=$(sudo uci get network.lan.ipaddr 2>/dev/null || echo 'not_set')
    fi
    
    # Check if already configured correctly
    if [ "$current_wan_proto" = "dhcp" ] && [ "$current_wan_ifname" = "eth1" ] && 
       [ "$current_lan_proto" = "static" ] && [ "$current_lan_ifname" = "eth0" ] && 
       [ "$current_lan_ip" = "192.168.1.1" ]; then
        print_success "Network is already configured correctly for FORWARD mode"
        print_status "WAN: eth1 (DHCP), LAN: eth0 (192.168.1.1 static)"
        return 0
    fi
    
    print_status "Network needs configuration - current state:"
    print_status "  WAN: $current_wan_ifname ($current_wan_proto)"
    print_status "  LAN: $current_lan_ifname ($current_lan_proto, $current_lan_ip)"
    
    # WAN Configuration (DHCP on eth1)
    print_status "Configuring WAN interface (eth1) for DHCP..."
    wan_commands=(
        "sudo uci set network.wan.proto='dhcp'"
        "sudo uci set network.wan.ifname='eth1'"
        "sudo uci set network.wan.mtu=1500"
        "sudo uci set network.wan.disabled='0'"
    )
    
    # LAN Configuration (Static on eth0)
    print_status "Configuring LAN interface (eth0) for static..."
    lan_commands=(
        "sudo uci set network.lan.proto='static'"
        "sudo uci set network.lan.ifname='eth0'"
        "sudo uci set network.lan.ipaddr='192.168.1.1'"
        "sudo uci set network.lan.netmask='255.255.255.0'"
        "sudo uci set network.lan.type='bridge'"
    )
    
    # Execute WAN configuration
    for cmd in "${wan_commands[@]}"; do
        print_status "Executing: $cmd"
        if execute_command "$cmd" "WAN configuration"; then
            print_success "Command successful: $cmd"
        else
            print_warning "Command failed: $cmd"
        fi
    done
    
    # Execute LAN configuration
    for cmd in "${lan_commands[@]}"; do
        print_status "Executing: $cmd"
        if execute_command "$cmd" "LAN configuration"; then
            print_success "Command successful: $cmd"
        else
            print_warning "Command failed: $cmd"
        fi
    done
    
    # Apply WAN configuration
    print_status "Applying WAN configuration with enhanced process..."
    apply_wan_config
    
    # Wait for configuration to settle
    print_status "Waiting 5 seconds for configuration to settle..."
    sleep 5
    
    print_success "Network configuration FORWARD completed (NO REBOOT)"
}

# Function to configure network settings REVERSE: WAN=enx0250f4000000 (LTE), LAN=eth0 (Static)
configure_network_settings_reverse() {
    print_status "Configuring network settings REVERSE (NO REBOOT)"
    
    # Ping remote host once (if using SSH)
    if [ "$USE_SSH" = true ] && [ -n "$REMOTE_HOST" ]; then
        if ! ping_remote_host; then
            print_error "Cannot configure network: Remote host is not reachable"
            return 1
        fi
    fi
    
    # Check if UCI is available
    if ! check_uci_available; then
        print_error "UCI command not found! This device may not be running OpenWrt."
        print_error "Please ensure the target device is running OpenWrt with UCI installed."
        return 1
    fi
    
    print_success "UCI is available, proceeding with network configuration..."
    
    # Check if network is already configured correctly
    print_status "Checking current network configuration..."
    local current_wan_proto=$(execute_command "sudo uci get network.wan.proto 2>/dev/null || echo 'not_set'" "Get current WAN protocol" | tail -1)
    local current_wan_ifname=$(execute_command "sudo uci get network.wan.ifname 2>/dev/null || echo 'not_set'" "Get current WAN interface" | tail -1)
    local current_lan_proto=$(execute_command "sudo uci get network.lan.proto 2>/dev/null || echo 'not_set'" "Get current LAN protocol" | tail -1)
    local current_lan_ifname=$(execute_command "sudo uci get network.lan.ifname 2>/dev/null || echo 'not_set'" "Get current LAN interface" | tail -1)
    local current_lan_ip=$(execute_command "sudo uci get network.lan.ipaddr 2>/dev/null || echo 'not_set'" "Get current LAN IP" | tail -1)
    
    # Get expected LAN IP
    local expected_lan_ip="${CUSTOM_LAN_IP:-192.168.1.1}"
    
    # Check if already configured correctly for REVERSE mode
    if [ "$current_wan_proto" = "lte" ] && ([ "$current_wan_ifname" = "enx0250f4000000" ] || [ "$current_wan_ifname" = "usb0" ]) && 
       [ "$current_lan_proto" = "static" ] && [ "$current_lan_ifname" = "eth0" ] && 
       [ "$current_lan_ip" = "$expected_lan_ip" ]; then
        print_success "Network is already configured correctly for REVERSE mode"
        print_status "WAN: enx0250f4000000 (LTE), LAN: eth0 ($expected_lan_ip static)"
        return 0
    fi
    
    print_status "Network needs configuration - current state:"
    print_status "  WAN: $current_wan_ifname ($current_wan_proto)"
    print_status "  LAN: $current_lan_ifname ($current_lan_proto, $current_lan_ip)"
    print_status "  Expected: WAN=enx0250f4000000 (LTE), LAN=eth0 ($expected_lan_ip static)"
    
    # WAN Configuration (LTE on USB device) - REVERSE
    print_status "Configuring WAN interface (enx0250f4000000) for LTE..."
    wan_commands=(
        "sudo uci set network.wan.proto='lte'"
        "sudo uci set network.wan.ifname='enx0250f4000000'"
        "sudo uci set network.wan.mtu=1500"
    )
    
    # LAN Configuration (Static on eth0) - Use custom IP if provided
    local lan_ip="${CUSTOM_LAN_IP:-192.168.1.1}"
    print_status "Configuring LAN interface (eth0) for static with IP: $lan_ip..."
    lan_commands=(
        "sudo uci set network.lan.proto='static'"
        "sudo uci set network.lan.ifname='eth0'"
        "sudo uci set network.lan.ipaddr='$lan_ip'"
        "sudo uci set network.lan.netmask='255.255.255.0'"
    )
    
    # Execute WAN configuration
    for cmd in "${wan_commands[@]}"; do
        print_status "Executing: $cmd"
        if execute_command "$cmd" "WAN LTE configuration"; then
            print_success "Command successful: $cmd"
        else
            print_warning "Command failed: $cmd"
        fi
    done
    
    # Execute LAN configuration
    for cmd in "${lan_commands[@]}"; do
        print_status "Executing: $cmd"
        if execute_command "$cmd" "LAN configuration"; then
            print_success "Command successful: $cmd"
        else
            print_warning "Command failed: $cmd"
        fi
    done
    
    # Skip password setting here - will be done in reset_device()
    print_status "Password will be reset to admin/admin in the final reset step"
    
    # Apply WAN configuration with immediate network reload
    print_status "Applying WAN configuration with enhanced process..."
    apply_wan_config
    
    # Wait for configuration to settle
    print_status "Waiting 5 seconds for configuration to settle..."
    sleep 5
    
    print_success "Network configuration REVERSE completed (NO REBOOT)"
}

# Function to verify network configuration
verify_network_config() {
    local mode="$1"
    print_status "Verifying network configuration for $mode mode..."
    
    # Get current configuration
    local current_wan_proto=$(execute_command "sudo uci get network.wan.proto 2>/dev/null || echo 'not_set'" "Get current WAN protocol" | tail -1)
    local current_wan_ifname=$(execute_command "sudo uci get network.wan.ifname 2>/dev/null || echo 'not_set'" "Get current WAN interface" | tail -1)
    local current_lan_proto=$(execute_command "sudo uci get network.lan.proto 2>/dev/null || echo 'not_set'" "Get current LAN protocol" | tail -1)
    local current_lan_ifname=$(execute_command "sudo uci get network.lan.ifname 2>/dev/null || echo 'not_set'" "Get current LAN interface" | tail -1)
    local current_lan_ip=$(execute_command "sudo uci get network.lan.ipaddr 2>/dev/null || echo 'not_set'" "Get current LAN IP" | tail -1)
    
    print_status "Current UCI Configuration:"
    print_status "  WAN: $current_wan_ifname ($current_wan_proto)"
    print_status "  LAN: $current_lan_ifname ($current_lan_proto, $current_lan_ip)"
    
    # Check interface status
    print_status "Interface Status:"
    execute_command "ip addr show | grep -E '(eth0|eth1|enx0250f4000000|usb0|br-lan):' -A 2" "Show interface status"
    
    # Check routing table
    print_status "Routing Table:"
    execute_command "ip route" "Show routing table"
    
    # Verify based on mode
    if [ "$mode" = "FORWARD" ]; then
        if [ "$current_wan_proto" = "dhcp" ] && [ "$current_wan_ifname" = "eth1" ] && 
           [ "$current_lan_proto" = "static" ] && [ "$current_lan_ifname" = "eth0" ] && 
           [ "$current_lan_ip" = "192.168.1.1" ]; then
            print_success "✅ FORWARD mode configuration is CORRECT"
            return 0
        else
            print_error "❌ FORWARD mode configuration is INCORRECT"
            return 1
        fi
    elif [ "$mode" = "REVERSE" ]; then
        if [ "$current_wan_proto" = "lte" ] && ([ "$current_wan_ifname" = "enx0250f4000000" ] || [ "$current_wan_ifname" = "usb0" ]) && 
           [ "$current_lan_proto" = "static" ] && [ "$current_lan_ifname" = "eth0" ] && 
           [ "$current_lan_ip" = "192.168.1.1" ]; then
            print_success "✅ REVERSE mode configuration is CORRECT"
            
            # Additional LTE interface check
            if execute_command "ip addr show usb0 | grep -q 'inet '" "Check LTE interface IP"; then
                print_success "✅ LTE interface has IP address"
            else
                print_warning "⚠️ LTE interface is UP but no IP address assigned"
                print_status "This may be normal if LTE modem is not connected or not configured"
            fi
            return 0
        else
            print_error "❌ REVERSE mode configuration is INCORRECT"
            return 1
        fi
    fi
    
    print_error "Unknown mode: $mode"
    return 1
}

# Function to apply WAN configuration with enhanced process
apply_wan_config() {
    print_status "Applying WAN configuration"
    
    # Fix hostname resolution
    print_status "Fixing hostname resolution..."
    if execute_command "grep -q 'localhost.localdomain' /etc/hosts || echo '127.0.0.1 localhost.localdomain' | sudo tee -a /etc/hosts" "Hostname resolution fix"; then
        print_success "localhost.localdomain already in /etc/hosts"
    fi
    
    # Commit UCI changes
    print_status "Committing UCI changes..."
    if execute_command "sudo uci commit" "UCI commit"; then
        print_success "UCI commit successful"
    else
        print_error "UCI commit failed"
        return 1
    fi
    
    # Clean up empty routes
    print_status "Cleaning up empty routes..."
    cleanup_empty_routes
    
    # Run network configuration using the same method as web interface
    print_status "Running network configuration (web interface method)..."
    
    # Apply network configuration immediately
    if execute_command "sudo luci-reload network" "LuCI network reload (web interface method)"; then
        print_success "LuCI network reload successful (web interface method)"
    # Try OpenWrt native network_config tool
    elif execute_command "sudo /usr/sbin/network_config" "OpenWrt native network config"; then
        print_success "OpenWrt native network config successful"
    # Fallback to network restart
    elif execute_command "sudo /etc/init.d/network restart" "Network restart fallback"; then
        print_success "Network restart successful (fallback method)"
    else
        print_error "All network configuration methods failed"
        return 1
    fi
    
    # Clean up routes again
    cleanup_empty_routes
    
    print_success "WAN configuration applied successfully"
}

# Function to apply WAN configuration without immediate network reload (for reset_device)
apply_wan_config_deferred() {
    print_status "Applying WAN configuration (deferred network reload)"
    
    # Fix hostname resolution
    print_status "Fixing hostname resolution..."
    if execute_command "grep -q 'localhost.localdomain' /etc/hosts || echo '127.0.0.1 localhost.localdomain' | sudo tee -a /etc/hosts" "Hostname resolution fix"; then
        print_success "localhost.localdomain already in /etc/hosts"
    fi
    
    # Commit UCI changes
    print_status "Committing UCI changes..."
    if execute_command "sudo uci commit" "UCI commit"; then
        print_success "UCI commit successful"
    else
        print_error "UCI commit failed"
        return 1
    fi
    
    # Clean up empty routes
    print_status "Cleaning up empty routes..."
    cleanup_empty_routes
    
    # Skip luci-reload here - will be done at the end of reset_device()
    print_status "Network configuration prepared (luci-reload will be executed at the end)"
    
    # Clean up routes again
    cleanup_empty_routes
    
    print_success "WAN configuration prepared (deferred network reload)"
}

# Function to clean up empty routes
cleanup_empty_routes() {
    print_status "Cleaning up empty routes..."
    
    # Check for WAN gateway configuration
    print_status "Checking for WAN gateway configuration..."
    if execute_command "ip route | grep default" "Check default route"; then
        print_status "WAN gateway configured, routes are present"
    else
        print_status "No WAN gateway configured, skipping default route addition"
    fi
    
    print_success "Route cleanup completed"
}

# =============================================================================
# PASSWORD CONFIGURATION FUNCTIONS
# =============================================================================

# Function to configure password back to admin
configure_password_admin() {
    print_status "Checking current password configuration..."
    
    # Check if password is already set to admin in UCI
    local current_password=$(execute_command "sudo uci get system.@system[0].password 2>/dev/null || echo 'not_set'" "Get current UCI password")
    
    if [ "$current_password" = "admin" ]; then
        print_success "Password is already set to admin in UCI configuration"
        # Still verify with passwd command to ensure consistency
        print_status "Verifying password consistency with passwd command..."
        if execute_command "echo 'admin' | sudo -S true 2>/dev/null" "Test current password"; then
            print_success "Password is already correctly set to admin - no changes needed"
            return 0
        else
            print_warning "UCI shows admin but passwd test failed - will update for consistency"
        fi
    fi
    
    print_status "Configuring password back to admin..."
    
    # Set password using multiple methods (UCI for web interface, passwd for SSH)
    uci_success=false
    system_success=false
    
    # Method 1: Set password using UCI (for OpenWrt web interface)
    print_status "Method 1: Setting password using UCI (for web interface)..."
    
    # First, ensure the system section exists
    if execute_command "sudo uci show system.@system[0] >/dev/null 2>&1" "Check if system section exists"; then
        print_success "System UCI section exists"
    else
        print_warning "System UCI section doesn't exist, creating it..."
        if execute_command "sudo uci add system system" "Create system UCI section"; then
            print_success "System UCI section created"
        else
            print_error "Failed to create system UCI section"
        fi
    fi
    
    # Set the password in UCI
    if execute_command "sudo uci set system.@system[0].password='admin'" "Set password in UCI"; then
        if execute_command "sudo uci commit system" "Commit UCI changes"; then
            print_success "Password set to admin via UCI method (web interface)"
            uci_success=true
        else
            print_error "Failed to commit UCI changes"
        fi
    else
        print_error "Failed to set password in UCI"
    fi
    
    # Method 2: Set system password using passwd command (for SSH login)
    print_status "Method 2: Setting system password using passwd command (for SSH login)..."
    if execute_command "echo -e 'admin\nadmin' | sudo passwd admin" "Set system password via passwd"; then
        print_success "System password set to admin via passwd command (SSH login)"
        system_success=true
    else
        print_warning "Password setting via passwd failed, trying chpasswd..."
        
        # Method 3: Fallback to chpasswd
        print_status "Method 3: Setting system password using chpasswd (fallback)..."
        if execute_command "echo 'admin:admin' | sudo chpasswd" "Set system password via chpasswd"; then
            print_success "System password set to admin via chpasswd command (SSH login)"
            system_success=true
        else
            print_error "Password setting via chpasswd also failed"
        fi
    fi
    
    # Check results
    if [ "$uci_success" = true ] && [ "$system_success" = true ]; then
        print_success "Password configuration completed successfully (both web interface and SSH)"
        return 0
    elif [ "$uci_success" = true ]; then
        print_warning "UCI password set successfully, but system password failed - web interface only"
        return 0
    elif [ "$system_success" = true ]; then
        print_warning "System password set successfully, but UCI password failed - SSH login only"
        return 0
    else
        print_error "All password setting methods failed"
        return 1
    fi
}

# Function to configure custom password
configure_password_custom() {
    local new_password="$1"
    
    if [ -z "$new_password" ]; then
        print_error "No password provided for custom password configuration"
        return 1
    fi
    
    print_status "Configuring password to: $new_password"
    
    # Set password using multiple methods (UCI for web interface, passwd for SSH)
    uci_success=false
    system_success=false
    
    # Method 1: Set password using UCI (for OpenWrt web interface)
    print_status "Method 1: Setting password using UCI (for web interface)..."
    
    # First, ensure the system section exists
    if execute_command "sudo uci show system.@system[0] >/dev/null 2>&1" "Check if system section exists"; then
        print_success "System UCI section exists"
    else
        print_warning "System UCI section doesn't exist, creating it..."
        if execute_command "sudo uci add system system" "Create system UCI section"; then
            print_success "System UCI section created"
        else
            print_error "Failed to create system UCI section"
        fi
    fi
    
    # Set the password in UCI
    if execute_command "sudo uci set system.@system[0].password='$new_password'" "Set password in UCI"; then
        if execute_command "sudo uci commit system" "Commit UCI changes"; then
            print_success "Password set to $new_password via UCI method (web interface)"
            uci_success=true
        else
            print_error "Failed to commit UCI changes"
        fi
    else
        print_error "Failed to set password in UCI"
    fi
    
    # Method 2: Set system password using passwd command (for SSH login)
    print_status "Method 2: Setting system password using passwd command (for SSH login)..."
    if execute_command "echo -e '$new_password\n$new_password' | sudo passwd admin" "Set system password via passwd"; then
        print_success "System password set to $new_password via passwd command (SSH login)"
        system_success=true
    else
        print_warning "Password setting via passwd failed, trying chpasswd..."
        
        # Method 3: Fallback to chpasswd
        print_status "Method 3: Setting system password using chpasswd (fallback)..."
        if execute_command "echo 'admin:$new_password' | sudo chpasswd" "Set system password via chpasswd"; then
            print_success "System password set to $new_password via chpasswd command (SSH login)"
            system_success=true
        else
            print_error "Password setting via chpasswd also failed"
        fi
    fi
    
    # Check results
    if [ "$uci_success" = true ] && [ "$system_success" = true ]; then
        print_success "Password configuration completed successfully (both web interface and SSH)"
        return 0
    elif [ "$uci_success" = true ]; then
        print_warning "UCI password set successfully, but system password failed - web interface only"
        return 0
    elif [ "$system_success" = true ]; then
        print_warning "System password set successfully, but UCI password failed - SSH login only"
        return 0
    else
        print_error "All password setting methods failed"
        return 1
    fi
}

# =============================================================================
# USER MANAGEMENT FUNCTIONS
# =============================================================================

# Function to add user to docker group
add_user_to_docker_group() {
    print_status "Checking if user is already in docker group..."
    
    # Check if user is already in docker group
    local user_in_docker_group=false
    if [ "$USE_SSH" = true ] && [ -n "$REMOTE_USER" ]; then
        if execute_command "groups $REMOTE_USER | grep -q docker" "Check if remote user is in docker group"; then
            print_success "Remote user '$REMOTE_USER' is already in docker group"
            user_in_docker_group=true
        fi
    elif [ "$USE_SSH" = false ]; then
        if execute_command "groups $USER | grep -q docker" "Check if local user is in docker group"; then
            print_success "Local user '$USER' is already in docker group"
            user_in_docker_group=true
        fi
    fi
    
    if [ "$user_in_docker_group" = true ]; then
        print_success "User is already in docker group"
        
        # Test if user can actually run Docker without sudo
        print_status "Testing if user can run Docker without sudo..."
        local docker_working=false
        
        # First check if Docker is installed
        if ! execute_command "which docker" "Check if Docker is installed"; then
            print_warning "Docker is not installed yet - cannot test Docker access"
            print_status "Please install Docker first using: ./network_config.sh install-docker"
            return 0
        fi
        
        if [ "$USE_SSH" = true ] && [ -n "$REMOTE_USER" ]; then
            if execute_command "sudo -u $REMOTE_USER docker --version" "Test Docker access for remote user"; then
                print_success "Remote user '$REMOTE_USER' can already run Docker without sudo"
                docker_working=true
            fi
        elif [ "$USE_SSH" = false ]; then
            if execute_command "docker --version" "Test Docker access for local user"; then
                print_success "Local user '$USER' can already run Docker without sudo"
                docker_working=true
            fi
        fi
        
        if [ "$docker_working" = true ]; then
            print_success "Docker group configuration is already working correctly - no changes needed"
            return 0
        else
            print_warning "User is in docker group but cannot run Docker without sudo yet"
            print_status "Group changes may require logout/login to take effect"
            print_status "Proceeding with verification and testing..."
        fi
    fi
    
    print_status "Adding user to docker group..."
    
    # Add user to docker group (if not root)
    if [ "$USE_SSH" = true ] && [ -n "$REMOTE_USER" ] && [ "$REMOTE_USER" != "root" ]; then
        print_status "Adding remote user '$REMOTE_USER' to docker group..."
        if execute_command "sudo usermod -aG docker $REMOTE_USER" "Add remote user to docker group"; then
            print_success "Remote user '$REMOTE_USER' added to docker group"
            print_warning "Please log out and log back in for group changes to take effect"
        else
            print_warning "Failed to add remote user '$REMOTE_USER' to docker group"
        fi
    elif [ "$USE_SSH" = false ] && [ "$USER" != "root" ]; then
        print_status "Adding local user '$USER' to docker group..."
        if execute_command "sudo usermod -aG docker $USER" "Add local user to docker group"; then
            print_success "Local user '$USER' added to docker group"
            print_warning "Please log out and log back in for group changes to take effect"
        else
            print_warning "Failed to add local user '$USER' to docker group"
        fi
    else
        print_warning "Cannot add root user to docker group"
    fi
    
    # Verify the user is in the docker group
    print_status "Verifying user is in docker group..."
    if [ "$USE_SSH" = true ] && [ -n "$REMOTE_USER" ]; then
        if execute_command "groups $REMOTE_USER | grep -q docker" "Check if user is in docker group"; then
            print_success "User '$REMOTE_USER' is now in docker group"
        else
            print_warning "User '$REMOTE_USER' may not be in docker group yet (group changes require logout/login)"
        fi
    elif [ "$USE_SSH" = false ]; then
        if execute_command "groups $USER | grep -q docker" "Check if user is in docker group"; then
            print_success "User '$USER' is now in docker group"
        else
            print_warning "User '$USER' may not be in docker group yet (group changes require logout/login)"
        fi
    fi
    
    # Test if user can run Docker commands without sudo
    print_status "Testing Docker access without sudo..."
    local docker_test_passed=false
    
    # First check if Docker is installed
    print_status "Checking if Docker is installed..."
    if ! execute_command "which docker" "Check if Docker is installed"; then
        print_warning "Docker is not installed yet - cannot test Docker access"
        print_status "Please install Docker first using: ./network_config.sh install-docker"
        return 0
    fi
    
    if [ "$USE_SSH" = true ] && [ -n "$REMOTE_USER" ]; then
        # For remote users, we need to test differently since we can't easily switch user context
        print_status "Testing Docker access for remote user '$REMOTE_USER'..."
        if execute_command "sudo -u $REMOTE_USER docker --version" "Test Docker access for remote user"; then
            print_success "Remote user '$REMOTE_USER' can access Docker without sudo"
            docker_test_passed=true
        else
            print_warning "Remote user '$REMOTE_USER' cannot access Docker without sudo yet"
            print_status "This is normal - group changes require logout/login to take effect"
        fi
    elif [ "$USE_SSH" = false ]; then
        # For local users, test directly
        print_status "Testing Docker access for local user '$USER'..."
        if execute_command "docker --version" "Test Docker access for local user"; then
            print_success "Local user '$USER' can access Docker without sudo"
            docker_test_passed=true
        else
            print_warning "Local user '$USER' cannot access Docker without sudo yet"
            print_status "This is normal - group changes require logout/login to take effect"
        fi
    fi
    
    # Provide guidance based on test results
    if [ "$docker_test_passed" = true ]; then
        print_success "Docker group configuration is working correctly!"
        print_status "User can now run Docker commands without sudo"
    else
        print_warning "Docker group changes have been applied but may not be active yet"
        print_status "To activate group changes:"
        print_status "  - Log out and log back in, OR"
        print_status "  - Run: newgrp docker, OR"
        print_status "  - Restart the terminal session"
        print_status "After that, test with: docker --version"
    fi
}

# =============================================================================
# SYSTEM UTILITY FUNCTIONS
# =============================================================================

# Function to ensure internet connectivity before installation
ensure_internet_connectivity() {
    print_status "Checking internet connectivity before installation..."
    
    # Test basic internet connectivity
    if execute_command "ping -c 1 -W 5 8.8.8.8" "Test internet connectivity"; then
        print_success "Internet connectivity is working"
        
        # Test DNS resolution
        if execute_command "ping -c 1 -W 5 google.com" "Test DNS resolution"; then
            print_success "DNS resolution is working"
            return 0
        else
            print_warning "DNS resolution failed - attempting to fix..."
            fix_dns_configuration
            return $?
        fi
    else
        print_warning "Internet connectivity failed - attempting to fix DNS..."
        fix_dns_configuration
        return $?
    fi
}

# Function to fix Docker networking issues
fix_docker_networking() {
    print_status "Fixing Docker networking configuration..."
    
    # Stop Docker service first
    print_status "Stopping Docker service..."
    execute_command "sudo systemctl stop docker" "Stop Docker service" || true
    
    # Check if iptables is available
    if ! execute_command "which iptables" "Check if iptables is available"; then
        print_warning "iptables not found - installing..."
        execute_command "sudo apt-get update && sudo apt-get install -y iptables" "Install iptables"
    fi
    
    # Clear existing Docker iptables rules
    print_status "Clearing existing Docker iptables rules..."
    execute_command "sudo iptables -t filter -F DOCKER" "Clear DOCKER filter chain" || true
    execute_command "sudo iptables -t nat -F DOCKER" "Clear DOCKER nat chain" || true
    execute_command "sudo iptables -t filter -D FORWARD -j DOCKER" "Remove FORWARD rule" || true
    execute_command "sudo iptables -t nat -D PREROUTING -m addrtype --dst-type LOCAL -j DOCKER" "Remove PREROUTING rule" || true
    execute_command "sudo iptables -t nat -D OUTPUT -m addrtype --dst-type LOCAL ! --dst 127.0.0.0/8 -j DOCKER" "Remove OUTPUT rule" || true
    
    # Delete existing Docker chains
    execute_command "sudo iptables -t filter -X DOCKER" "Delete DOCKER filter chain" || true
    execute_command "sudo iptables -t nat -X DOCKER" "Delete DOCKER nat chain" || true
    
    # Create Docker iptables chains
    print_status "Creating Docker iptables chains..."
    execute_command "sudo iptables -t filter -N DOCKER" "Create DOCKER filter chain"
    execute_command "sudo iptables -t nat -N DOCKER" "Create DOCKER nat chain"
    
    # Add rules to forward traffic to DOCKER chain
    print_status "Adding iptables rules for Docker..."
    execute_command "sudo iptables -t filter -A FORWARD -j DOCKER" "Add FORWARD rule to DOCKER chain"
    execute_command "sudo iptables -t nat -A PREROUTING -m addrtype --dst-type LOCAL -j DOCKER" "Add PREROUTING rule to DOCKER chain"
    execute_command "sudo iptables -t nat -A OUTPUT -m addrtype --dst-type LOCAL ! --dst 127.0.0.0/8 -j DOCKER" "Add OUTPUT rule to DOCKER chain"
    
    # Configure Docker daemon to use iptables
    print_status "Configuring Docker daemon..."
    if ! execute_command "sudo mkdir -p /etc/docker" "Create Docker config directory"; then
        print_warning "Failed to create Docker config directory"
    fi
    
    # Create Docker daemon configuration
    local docker_daemon_config='{
    "iptables": true,
    "ip-forward": true,
    "bridge": "docker0"
}'
    
    if execute_command "echo '$docker_daemon_config' | sudo tee /etc/docker/daemon.json" "Create Docker daemon config"; then
        print_success "Docker daemon configuration created"
    else
        print_warning "Failed to create Docker daemon configuration"
    fi
    
    # Start Docker service
    print_status "Starting Docker service..."
    if execute_command "sudo systemctl start docker" "Start Docker service"; then
        print_success "Docker service started"
        # Wait for Docker to be ready
        sleep 5
    else
        print_error "Failed to start Docker service"
        return 1
    fi
    
    # Verify Docker is running
    if execute_command "sudo docker ps" "Verify Docker is running"; then
        print_success "Docker networking configuration fixed"
        return 0
    else
        print_error "Docker networking configuration failed"
        return 1
    fi
}

# Function to check disk space and return available space in MB
check_disk_space() {
    local path="${1:-/}"
    local available_space
    
    if [ "$USE_SSH" = true ] && [ -n "$REMOTE_HOST" ]; then
        available_space=$(sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "df -m '$path' | tail -1 | awk '{print \$4}'" 2>/dev/null || echo "0")
    else
        available_space=$(df -m "$path" | tail -1 | awk '{print $4}' 2>/dev/null || echo "0")
    fi
    
    echo "$available_space"
}

# Function to check if we have enough disk space (minimum 2GB)
check_sufficient_disk_space() {
    local min_space_mb=2048  # 2GB minimum
    local available_space
    
    print_status "Checking available disk space..."
    available_space=$(check_disk_space)
    
    if [ "$available_space" -lt "$min_space_mb" ]; then
        print_warning "Insufficient disk space: ${available_space}MB available, ${min_space_mb}MB required"
        return 1
    else
        print_success "Sufficient disk space: ${available_space}MB available"
        return 0
    fi
}

# Function to perform aggressive disk cleanup
aggressive_disk_cleanup() {
    print_status "Performing aggressive disk cleanup..."
    
    # Show current disk usage
    print_status "Current disk usage:"
    execute_command "df -h /" "Show disk usage"
    
    # Clean up package cache
    print_status "Cleaning package cache..."
    if execute_command "sudo apt clean" "Clean apt cache"; then
        print_success "Package cache cleaned"
    fi
    
    if execute_command "sudo apt autoremove -y" "Remove unused packages"; then
        print_success "Unused packages removed"
    fi
    
    # Clean up APT cache more aggressively
    if execute_command "sudo rm -rf /var/cache/apt/archives/*" "Remove APT archives"; then
        print_success "APT archives cleaned"
    fi
    
    # Clean up log files
    print_status "Cleaning log files..."
    if execute_command "sudo find /var/log -name '*.log' -type f -mtime +7 -delete" "Clean old log files"; then
        print_success "Old log files cleaned"
    fi
    
    if execute_command "sudo find /var/log -name '*.gz' -type f -mtime +3 -delete" "Clean old compressed logs"; then
        print_success "Old compressed logs cleaned"
    fi
    
    # Clean up temporary files
    print_status "Cleaning temporary files..."
    if execute_command "sudo rm -rf /tmp/*" "Clean /tmp directory"; then
        print_success "Temporary files cleaned"
    fi
    
    if execute_command "sudo rm -rf /var/tmp/*" "Clean /var/tmp directory"; then
        print_success "Variable temporary files cleaned"
    fi
    
    # Clean up Docker if it exists
    if execute_command "which docker >/dev/null 2>&1" "Check if Docker exists"; then
        print_status "Performing aggressive Docker cleanup..."
        
        # Stop all containers
        if execute_command "sudo docker stop \$(sudo docker ps -aq) 2>/dev/null || true" "Stop all containers"; then
            print_success "All containers stopped"
        fi
        
        # Remove all containers
        if execute_command "sudo docker rm \$(sudo docker ps -aq) 2>/dev/null || true" "Remove all containers"; then
            print_success "All containers removed"
        fi
        
        # Remove all images (including dangling)
        if execute_command "sudo docker rmi \$(sudo docker images -aq) 2>/dev/null || true" "Remove all images"; then
            print_success "All images removed"
        fi
        
        # Remove all volumes
        if execute_command "sudo docker volume rm \$(sudo docker volume ls -q) 2>/dev/null || true" "Remove all volumes"; then
            print_success "All volumes removed"
        fi
        
        # Remove all networks (except default)
        if execute_command "sudo docker network rm \$(sudo docker network ls -q --filter type=custom) 2>/dev/null || true" "Remove custom networks"; then
            print_success "Custom networks removed"
        fi
        
        # System prune with all options
        if execute_command "sudo docker system prune -af --volumes" "Docker system prune with volumes"; then
            print_success "Docker system pruned with volumes"
        fi
        
        # Remove Docker build cache
        if execute_command "sudo docker builder prune -af" "Docker builder prune"; then
            print_success "Docker build cache pruned"
        fi
        
        # Clean up Docker temporary files
        if execute_command "sudo rm -rf /var/lib/docker/tmp/*" "Clean Docker temp files"; then
            print_success "Docker temp files cleaned"
        fi
        
        # Clean up Docker overlay2 (if exists)
        if execute_command "sudo rm -rf /var/lib/docker/overlay2/*" "Clean Docker overlay2"; then
            print_success "Docker overlay2 cleaned"
        fi
        
        # Restart Docker daemon to clear any corrupted state
        print_status "Restarting Docker daemon to clear corrupted state..."
        if execute_command "sudo systemctl restart docker" "Restart Docker daemon"; then
            print_success "Docker daemon restarted"
        fi
        
        # Wait for Docker to be ready
        sleep 5
        
        # Verify Docker is working
        if execute_command "sudo docker info" "Verify Docker daemon"; then
            print_success "Docker daemon is working"
        else
            print_warning "Docker daemon may have issues"
        fi
    fi
    
    # Clean up old kernels (if on Ubuntu/Debian)
    print_status "Cleaning old kernels..."
    if execute_command "sudo apt autoremove --purge -y" "Remove old kernels"; then
        print_success "Old kernels removed"
    fi
    
    # Show disk usage after cleanup
    print_status "Disk usage after cleanup:"
    execute_command "df -h /" "Show disk usage after cleanup"
    
    print_success "Aggressive disk cleanup completed"
}


# Function to ensure sufficient disk space with cleanup if needed
ensure_sufficient_disk_space() {
    local min_space_mb=2048  # 2GB minimum
    local available_space
    local cleanup_attempts=0
    local max_cleanup_attempts=3
    
    while [ $cleanup_attempts -lt $max_cleanup_attempts ]; do
        available_space=$(check_disk_space)
        
        if [ "$available_space" -ge "$min_space_mb" ]; then
            print_success "Sufficient disk space available: ${available_space}MB"
            return 0
        fi
        
        cleanup_attempts=$((cleanup_attempts + 1))
        print_warning "Insufficient disk space: ${available_space}MB available, ${min_space_mb}MB required"
        print_status "Performing cleanup attempt $cleanup_attempts/$max_cleanup_attempts..."
        
        aggressive_disk_cleanup
        
        # Wait a moment for cleanup to complete
        sleep 5
    done
    
    available_space=$(check_disk_space)
    if [ "$available_space" -lt "$min_space_mb" ]; then
        print_error "Still insufficient disk space after $max_cleanup_attempts cleanup attempts: ${available_space}MB"
        return 1
    fi
    
    return 0
}

# Function to install curl
install_curl() {
    print_status "Installing curl..."
    
    if execute_command "which curl" "Check if curl is installed"; then
        print_success "curl is already installed"
        return 0
    fi
    
    # Ensure internet connectivity before installation
    if ! ensure_internet_connectivity; then
        print_error "Cannot install curl: internet connectivity failed"
        return 1
    fi
    
    print_status "curl not found, installing..."
    
    # Use only apt package manager
    if execute_command "sudo apt update && sudo apt install -y curl" "Install curl via apt"; then
        print_success "curl installed via apt"
    else
        print_error "Failed to install curl via apt"
        return 1
    fi
    
    # Verify installation
    if execute_command "curl --version" "Verify curl installation"; then
        print_success "curl installation verified"
    else
        print_error "curl installation verification failed"
        return 1
    fi
}

# Function to fix DNS configuration
fix_dns_configuration() {
    print_status "Checking DNS configuration..."
    
    # First, test if DNS is already working
    print_status "Testing current DNS resolution..."
    local dns_working=false
    
    # Try multiple DNS test methods
    if execute_command "which dig >/dev/null 2>&1 && dig google.com +short" "Test DNS with dig"; then
        print_success "DNS resolution working with dig"
        dns_working=true
    elif execute_command "which host >/dev/null 2>&1 && host google.com" "Test DNS with host"; then
        print_success "DNS resolution working with host"
        dns_working=true
    elif execute_command "which nslookup >/dev/null 2>&1 && nslookup google.com" "Test DNS with nslookup"; then
        print_success "DNS resolution working with nslookup"
        dns_working=true
    elif execute_command "getent hosts google.com" "Test DNS with getent"; then
        print_success "DNS resolution working with getent"
        dns_working=true
    elif execute_command "ping -c 1 -W 5 google.com" "Test DNS with ping"; then
        print_success "DNS resolution working with ping"
        dns_working=true
    elif execute_command "curl -s --connect-timeout 5 http://google.com >/dev/null" "Test DNS with curl"; then
        print_success "DNS resolution working with curl"
        dns_working=true
    else
        print_warning "DNS resolution test failed"
        dns_working=false
    fi
    
    # If DNS is already working, skip the fix
    if [ "$dns_working" = true ]; then
        print_success "DNS is already working correctly - no fix needed"
        return 0
    fi
    
    print_status "DNS is not working properly - proceeding with DNS fix..."
    
    # Install DNS tools if missing
    print_status "Installing DNS tools if missing..."
    if execute_command "which nslookup >/dev/null 2>&1 || (apt-get update -y && apt-get install -y dnsutils)" "Install DNS tools"; then
        print_success "DNS tools available"
    else
        print_warning "Could not install DNS tools, will use alternative methods"
    fi
    
    # Check current DNS configuration
    print_status "Current DNS configuration:"
    execute_command "cat /etc/resolv.conf" "Show current DNS config"
    
    # Check if systemd-resolved is managing DNS
    if execute_command "systemctl is-active systemd-resolved" "Check systemd-resolved status"; then
        print_status "systemd-resolved is active, configuring DNS through systemd..."
        
        # Configure systemd-resolved to use Google DNS
        print_status "Configuring systemd-resolved with Google DNS..."
        if execute_command "sudo mkdir -p /etc/systemd/resolved.conf.d" "Create systemd resolved config directory"; then
            print_success "systemd resolved config directory created"
        fi
        
        # Create systemd-resolved configuration
        local resolved_config='[Resolve]
DNS=8.8.8.8 8.8.4.4
FallbackDNS=1.1.1.1 1.0.0.1
DNSSEC=no
DNSOverTLS=no
Cache=yes
CacheFromLocalhost=no'
        
        if execute_command "echo '$resolved_config' | sudo tee /etc/systemd/resolved.conf.d/dns_servers.conf" "Create systemd resolved config"; then
            print_success "systemd-resolved configuration created"
        fi
        
        # Also configure main resolved.conf to ensure persistence
        print_status "Configuring main systemd-resolved.conf for persistence..."
        if execute_command "sudo cp /etc/systemd/resolved.conf /etc/systemd/resolved.conf.backup" "Backup original resolved.conf"; then
            print_success "Original resolved.conf backed up"
        fi
        
        # Add DNS configuration to main resolved.conf if not already present
        if execute_command "grep -q '^DNS=' /etc/systemd/resolved.conf"; then
            print_status "DNS configuration already present in main resolved.conf"
        else
            if execute_command "echo -e '\n# DNS servers configured by network_config.sh\nDNS=8.8.8.8 8.8.4.4' | sudo tee -a /etc/systemd/resolved.conf" "Add DNS to main resolved.conf"; then
                print_success "DNS configuration added to main resolved.conf"
            fi
        fi
        
        # Restart systemd-resolved
        print_status "Restarting systemd-resolved service..."
        if execute_command "sudo systemctl restart systemd-resolved" "Restart systemd-resolved"; then
            print_success "systemd-resolved restarted"
        fi
        
        # Wait for service to be ready
        sleep 3
        
        # Flush DNS cache
        print_status "Flushing DNS cache..."
        if execute_command "sudo systemctl flush-dns" "Flush DNS cache"; then
            print_success "DNS cache flushed"
        elif execute_command "sudo resolvectl flush-caches" "Flush DNS cache with resolvectl"; then
            print_success "DNS cache flushed with resolvectl"
        else
            print_warning "Could not flush DNS cache, but configuration should still work"
        fi
        
        # Configure NetworkManager DNS if present (for additional persistence)
        print_status "Checking for NetworkManager DNS configuration..."
        if execute_command "which nmcli >/dev/null 2>&1"; then
            print_status "NetworkManager found, configuring DNS..."
            # Get active connection
            local active_connection=$(execute_command "nmcli -t -f NAME connection show --active | head -1" "Get active connection")
            if [ -n "$active_connection" ]; then
                print_status "Configuring DNS for connection: $active_connection"
                if execute_command "sudo nmcli connection modify '$active_connection' ipv4.dns '8.8.8.8,8.8.4.4'" "Configure NetworkManager DNS"; then
                    print_success "NetworkManager DNS configured"
                fi
                if execute_command "sudo nmcli connection modify '$active_connection' ipv4.ignore-auto-dns yes" "Disable auto DNS"; then
                    print_success "Auto DNS disabled in NetworkManager"
                fi
            fi
        else
            print_status "NetworkManager not found, skipping NetworkManager DNS configuration"
        fi
        
        # Create a systemd service to ensure DNS persistence across reboots
        print_status "Creating DNS persistence service..."
        local dns_service='[Unit]
Description=Ensure DNS Configuration Persistence
After=network.target systemd-resolved.service
Wants=systemd-resolved.service

[Service]
Type=oneshot
ExecStart=/bin/bash -c "if [ -f /etc/systemd/resolved.conf.d/dns_servers.conf ]; then systemctl restart systemd-resolved; fi"
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target'
        
        if execute_command "echo '$dns_service' | sudo tee /etc/systemd/system/dns-persistence.service" "Create DNS persistence service"; then
            print_success "DNS persistence service created"
            if execute_command "sudo systemctl daemon-reload" "Reload systemd daemon"; then
                print_success "Systemd daemon reloaded"
            fi
            if execute_command "sudo systemctl enable dns-persistence.service" "Enable DNS persistence service"; then
                print_success "DNS persistence service enabled"
            fi
        fi
        
    else
        print_status "systemd-resolved not active, configuring /etc/resolv.conf directly..."
        
        # Check if Google DNS is already configured
        if execute_command "grep -q '8.8.8.8' /etc/resolv.conf" "Check for Google DNS"; then
            print_success "Google DNS (8.8.8.8) already configured"
            return 0
        fi
        
        # Backup current resolv.conf
        print_status "Backing up current DNS configuration..."
        if execute_command "sudo cp /etc/resolv.conf /etc/resolv.conf.backup" "Backup DNS config"; then
            print_success "DNS configuration backed up"
        fi
        
        # Add Google DNS to resolv.conf
        print_status "Adding Google DNS (8.8.8.8) to configuration..."
        if execute_command "echo 'nameserver 8.8.8.8' | sudo tee -a /etc/resolv.conf" "Add Google DNS"; then
            print_success "Google DNS added to configuration"
        else
            print_error "Failed to add Google DNS"
            return 1
        fi
        
        # Also add 8.8.4.4 as secondary DNS
        print_status "Adding secondary Google DNS (8.8.4.4)..."
        if execute_command "echo 'nameserver 8.8.4.4' | sudo tee -a /etc/resolv.conf" "Add secondary Google DNS"; then
            print_success "Secondary Google DNS added"
        fi
    fi
    
    # Show updated DNS configuration
    print_status "Updated DNS configuration:"
    execute_command "cat /etc/resolv.conf" "Show updated DNS config"
    
    # Verify DNS configuration was applied
    print_status "Verifying DNS configuration..."
    
    # Check systemd-resolved status if available
    if execute_command "which resolvectl >/dev/null 2>&1"; then
        print_status "Checking systemd-resolved status..."
        execute_command "resolvectl status" "Check systemd-resolved status"
        execute_command "resolvectl dns" "Check active DNS servers"
    fi
    
    # Wait for DNS configuration to take effect
    sleep 2
    
    # Quick verification test
    print_status "Quick DNS verification test..."
    if execute_command "ping -c 1 -W 5 google.com" "Quick DNS test with ping"; then
        print_success "DNS fix appears to be working"
    else
        print_warning "DNS test failed - configuration may need manual verification"
        print_status "Please test manually: nslookup google.com"
    fi
    
    print_success "DNS configuration fixed"
}

# Function to check internet connectivity and DNS
check_internet_dns() {
    print_status "Checking internet connectivity and DNS..."
    
    # First, test basic internet connectivity
    print_status "Testing basic internet connectivity..."
    if execute_command "ping -c 1 -W 5 8.8.8.8" "Internet connectivity test"; then
        print_success "Internet connectivity working"
    else
        print_warning "Internet connectivity failed - this may be the root cause"
        print_status "Checking network interface status..."
        execute_command "ip addr show" "Show network interfaces"
        execute_command "ip route show" "Show routing table"
        return 1
    fi
    
    # Test DNS resolution
    print_status "Testing DNS resolution..."
    if execute_command "which nslookup >/dev/null 2>&1 && nslookup google.com" "DNS resolution test"; then
        print_success "DNS resolution working"
    elif execute_command "which dig >/dev/null 2>&1 && dig google.com +short" "DNS resolution test with dig"; then
        print_success "DNS resolution working with dig"
    elif execute_command "getent hosts google.com" "DNS resolution test with getent"; then
        print_success "DNS resolution working with getent"
    else
        print_warning "DNS resolution failed - attempting to fix..."
        fix_dns_configuration
    fi
    
    # Test internet connectivity
    print_status "Testing internet connectivity..."
    if execute_command "ping -c 3 8.8.8.8" "Internet connectivity test"; then
        print_success "Internet connectivity working"
    else
        print_warning "Internet connectivity failed"
    fi
    
    # Test HTTP connectivity
    print_status "Testing HTTP connectivity..."
    if execute_command "curl -s -o /dev/null -w '%{http_code}' http://google.com" "HTTP connectivity test"; then
        http_status=$(execute_command "curl -s -o /dev/null -w '%{http_code}' http://google.com" "Get HTTP status")
        if [ "$http_status" = "200" ]; then
            print_success "HTTP connectivity working"
        else
            print_warning "HTTP connectivity returned status: $http_status"
        fi
    else
        print_warning "HTTP connectivity failed"
    fi
    
    print_success "Internet and DNS check completed"
}

# Function to install Docker
install_docker() {
    print_status "Installing Docker..."
    
    # Check if both Docker and Docker Compose are already installed
    docker_installed=false
    compose_installed=false
    
    if execute_command "docker --version" "Check if Docker is installed"; then
        docker_installed=true
        docker_version=$(execute_command "docker --version" "Get Docker version")
        print_success "Docker is already installed: $docker_version"
    fi
    
    if execute_command "docker compose version" "Check if Docker Compose plugin is installed"; then
        compose_installed=true
        compose_version=$(execute_command "docker compose version" "Get Docker Compose version")
        print_success "Docker Compose plugin is already installed: $compose_version"
    elif execute_command "docker-compose --version" "Check if standalone docker-compose is installed"; then
        compose_installed=true
        compose_version=$(execute_command "docker-compose --version" "Get docker-compose version")
        print_success "Standalone docker-compose is already installed: $compose_version"
    fi
    
    # If both are installed, we're done
    if [ "$docker_installed" = true ] && [ "$compose_installed" = true ]; then
        print_success "Both Docker and Docker Compose are already installed"
        return 0
    fi
    
    # Ensure internet connectivity before installation
    if ! ensure_internet_connectivity; then
        print_error "Cannot install Docker: internet connectivity failed"
        return 1
    fi
    
    # Ensure sufficient disk space before installation
    if ! ensure_sufficient_disk_space; then
        print_error "Cannot install Docker: insufficient disk space"
        return 1
    fi
    
    print_status "Installing Docker and Docker Compose plugin..."
    
    # Check if apt is available (Debian/Ubuntu system)
    if execute_command "which apt" "Check if Debian/Ubuntu system"; then
        print_status "Detected Debian/Ubuntu system, installing Docker via apt..."
        
        # Update apt index
        print_status "Updating apt index..."
        if execute_command "sudo apt-get update -y" "Update apt index"; then
            print_success "Apt index updated"
        else
            print_warning "Failed to update apt index"
        fi
        
        # Install required packages
        print_status "Installing required packages..."
        if execute_command "sudo apt-get install -y ca-certificates curl gnupg lsb-release" "Install Docker dependencies"; then
            print_success "Docker dependencies installed"
        else
            print_error "Failed to install Docker dependencies"
            return 1
        fi
        
        # Add Docker's official GPG key
        print_status "Adding Docker's official GPG key..."
        if execute_command "sudo install -m 0755 -d /etc/apt/keyrings" "Create keyrings directory"; then
            print_success "Keyrings directory created"
        fi
        
        # Remove existing GPG key if it exists to avoid conflicts
        execute_command "sudo rm -f /etc/apt/keyrings/docker.gpg" "Remove existing Docker GPG key"
        
        # Try multiple methods to add the GPG key
        gpg_added=false
        
        # Method 1: Direct curl and gpg dearmor
        print_status "Attempting to add Docker GPG key (method 1)..."
        if execute_command "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --batch --dearmor -o /etc/apt/keyrings/docker.gpg" "Add Docker GPG key via curl and gpg"; then
            gpg_added=true
            print_success "Docker GPG key added successfully (method 1)"
        else
            print_warning "Method 1 failed, trying alternative method..."
            
            # Method 2: Download to temp file first, then process
            print_status "Attempting to add Docker GPG key (method 2)..."
            if execute_command "curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /tmp/docker.gpg.tmp" "Download Docker GPG key to temp file"; then
                if execute_command "sudo gpg --batch --dearmor -o /etc/apt/keyrings/docker.gpg /tmp/docker.gpg.tmp" "Process Docker GPG key from temp file"; then
                    gpg_added=true
                    print_success "Docker GPG key added successfully (method 2)"
                    execute_command "rm -f /tmp/docker.gpg.tmp" "Clean up temp GPG file"
                else
                    print_warning "Method 2 failed, trying final method..."
                    execute_command "rm -f /tmp/docker.gpg.tmp" "Clean up temp GPG file"
                fi
            fi
        fi
        
        # Method 3: Use apt-key as fallback (deprecated but might work)
        if [ "$gpg_added" = false ]; then
            print_status "Attempting to add Docker GPG key (method 3 - fallback)..."
            if execute_command "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -" "Add Docker GPG key via apt-key (fallback)"; then
                gpg_added=true
                print_success "Docker GPG key added successfully (method 3 - fallback)"
            fi
        fi
        
        if [ "$gpg_added" = false ]; then
            print_error "Failed to add Docker GPG key with all methods"
            return 1
        fi
        
        # Set permissions if the keyring file exists
        if [ -f "/etc/apt/keyrings/docker.gpg" ]; then
            if execute_command "sudo chmod a+r /etc/apt/keyrings/docker.gpg" "Set GPG key permissions"; then
                print_success "GPG key permissions set"
            fi
        fi
        
        # Set up the stable Docker repository
        print_status "Setting up Docker repository..."
        
        # Choose the appropriate repository format based on which GPG method worked
        if [ -f "/etc/apt/keyrings/docker.gpg" ]; then
            # Use modern keyring format
            repo_line="deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \$(lsb_release -cs) stable"
        else
            # Use legacy format (for apt-key fallback)
            repo_line="deb [arch=\$(dpkg --print-architecture)] https://download.docker.com/linux/ubuntu \$(lsb_release -cs) stable"
        fi
        
        if execute_command "echo \"$repo_line\" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null" "Add Docker repository"; then
            print_success "Docker repository added"
        else
            print_error "Failed to add Docker repository"
            return 1
        fi
        
        # Update apt index again
        print_status "Updating apt index with Docker repository..."
        if execute_command "sudo apt-get update -y" "Update apt index with Docker repo"; then
            print_success "Apt index updated with Docker repository"
        else
            print_error "Failed to update apt index with Docker repository"
            return 1
        fi
        
        # Install Docker engine, CLI, containerd, and Docker Compose plugin (single reliable method)
        print_status "Installing Docker engine, CLI, containerd, and Docker Compose plugin..."
        if execute_command "sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin" "Install Docker packages"; then
            print_success "Docker packages installed successfully"
        else
            print_error "Failed to install Docker packages"
            return 1
        fi
        
    else
        print_error "apt package manager not found. This script only supports Debian/Ubuntu systems for Docker installation."
        return 1
    fi
    
    # Enable and start Docker service
    print_status "Enabling and starting Docker service..."
    if execute_command "sudo systemctl enable docker" "Enable Docker service"; then
        print_success "Docker service enabled"
    else
        print_warning "Failed to enable Docker service (may not be systemd-based)"
    fi
    
    if execute_command "sudo systemctl start docker" "Start Docker service"; then
        print_success "Docker service started"
    else
        print_warning "Failed to start Docker service (may not be systemd-based)"
    fi
    
    # Add user to docker group (if not root)
    if [ "$USE_SSH" = true ] && [ -n "$REMOTE_USER" ] && [ "$REMOTE_USER" != "root" ]; then
        print_status "Adding remote user '$REMOTE_USER' to docker group..."
        if execute_command "sudo usermod -aG docker $REMOTE_USER" "Add remote user to docker group"; then
            print_success "Remote user '$REMOTE_USER' added to docker group"
            print_warning "Please log out and log back in for group changes to take effect"
        else
            print_warning "Failed to add remote user '$REMOTE_USER' to docker group"
        fi
    elif [ "$USE_SSH" = false ] && [ "$USER" != "root" ]; then
        print_status "Adding local user '$USER' to docker group..."
        if execute_command "sudo usermod -aG docker $USER" "Add local user to docker group"; then
            print_success "Local user '$USER' added to docker group"
            print_warning "Please log out and log back in for group changes to take effect"
        else
            print_warning "Failed to add local user '$USER' to docker group"
        fi
    fi
    
    # Verify Docker installation
    print_status "Verifying Docker installation..."
    if execute_command "docker --version" "Verify Docker installation"; then
        docker_version=$(execute_command "docker --version" "Get Docker version")
        print_success "Docker installation verified: $docker_version"
    else
        print_error "Docker installation verification failed"
        return 1
    fi
    
    # Verify Docker Compose installation (plugin should be installed with Docker CE)
    print_status "Verifying Docker Compose installation..."
    if execute_command "docker compose version" "Verify Docker Compose plugin"; then
        compose_version=$(execute_command "docker compose version" "Get Docker Compose version")
        print_success "Docker Compose plugin verified: $compose_version"
    else
        print_error "Docker Compose plugin installation failed - this should not happen with Docker CE installation"
        return 1
    fi
    
    # Test Docker with hello-world
    print_status "Testing Docker with hello-world container..."
    if execute_command "docker run --rm hello-world" "Test Docker with hello-world"; then
        print_success "Docker test successful"
    else
        print_warning "Docker test failed (may need internet connection or container registry access)"
    fi
    
    print_success "Docker and Docker Compose plugin installation completed successfully"
}

# Function to install Node-RED with Docker Compose
install_nodered_docker() {
    print_status "Installing Node-RED with Docker Compose..."
    
    # Check if Node-RED container is already running
    if execute_command "sudo docker ps | grep nodered" "Check if Node-RED is running"; then
        print_success "Node-RED container is already running, skipping installation"
        return 0
    fi
    
    # Check if Node-RED container exists but is stopped
    if execute_command "sudo docker ps -a | grep nodered" "Check if Node-RED container exists"; then
        print_status "Node-RED container exists but is stopped - starting it..."
        if execute_command "sudo docker start nodered" "Start existing Node-RED container"; then
            print_success "Node-RED container started successfully"
            return 0
        else
            print_warning "Failed to start existing Node-RED container - will recreate"
        fi
    fi
    
    # Ensure internet connectivity before installation (needed for Docker image download)
    if ! ensure_internet_connectivity; then
        print_error "Cannot install Node-RED: internet connectivity failed"
        return 1
    fi
    
    # Fix Docker networking issues before starting containers
    if ! fix_docker_networking; then
        print_warning "Docker networking fix failed, but continuing with installation"
    fi
    
    # Create Node-RED data directory
    print_status "Creating Node-RED data directory..."
    if execute_command "sudo mkdir -p /data/nodered" "Create Node-RED directory"; then
        print_success "Node-RED directory created"
    else
        print_error "Failed to create Node-RED directory"
        return 1
    fi
    
    # Set proper permissions
    if execute_command "sudo chown -R 1000:1000 /data/nodered" "Set Node-RED permissions"; then
        print_success "Node-RED permissions set"
    else
        print_warning "Failed to set Node-RED permissions"
    fi
    
    # Create Docker Compose file for Node-RED
    print_status "Creating Node-RED Docker Compose configuration..."
    nodered_compose='version: "3.8"

services:
  nodered:
    image: nodered/node-red:latest
    container_name: nodered
    restart: unless-stopped
    ports:
      - "1880:1880"
    volumes:
      - /data/nodered:/data
    environment:
      - TZ=UTC
    privileged: true
    devices:
      - /dev/ttyUSB0:/dev/ttyUSB0
      - /dev/ttyUSB1:/dev/ttyUSB1
      - /dev/ttyACM0:/dev/ttyACM0
      - /dev/ttyACM1:/dev/ttyACM1
    networks:
      - nodered_network

networks:
  nodered_network:
    driver: bridge'
    
    # Write Docker Compose file
    if execute_command "echo '$nodered_compose' | sudo tee /data/nodered/docker-compose.yml > /dev/null" "Create Node-RED compose file"; then
        print_success "Node-RED Docker Compose file created"
    else
        print_error "Failed to create Node-RED Docker Compose file"
        return 1
    fi
    
    # Create environment file for Node-RED
    print_status "Creating Node-RED environment configuration..."
    local nodered_env='# Node-RED Environment Configuration
NODE_RED_CREDENTIAL_SECRET=admin
TZ=UTC
NODE_RED_LOG_LEVEL=info'
    
    # Write environment file
    if execute_command "echo '$nodered_env' | sudo tee /data/nodered/.env > /dev/null" "Create Node-RED environment file"; then
        print_success "Node-RED environment file created"
    else
        print_error "Failed to create Node-RED environment file"
        return 1
    fi
    
    # Set proper permissions for environment file
    if execute_command "sudo chown 1000:1000 /data/nodered/.env" "Set Node-RED environment file permissions"; then
        print_success "Node-RED environment file permissions set"
    else
        print_warning "Could not set Node-RED environment file permissions"
    fi
    
    # Create Node-RED settings.js with authentication
    print_status "Creating Node-RED settings with authentication..."
    local nodered_settings='module.exports = {
    uiPort: process.env.PORT || 1880,
    mqttReconnectTime: 15000,
    serialReconnectTime: 15000,
    debugMaxLength: 1000,
    debugUseColors: true,
    flowFile: "flows.json",
    flowFilePretty: true,
    userDir: "/data/",
    nodesDir: "/data/nodes",
    functionGlobalContext: {},
    exportGlobalContextKeys: false,
    editorTheme: {
        projects: {
            enabled: false
        }
    },
    adminAuth: {
        type: "credentials",
        users: [{
            username: "admin",
            password: "$2a$08$zZWtXTja0fB1pzD4sHCMyOCMYz2Z6dNbM6tl8sJogENOMcxWV9DN.",
            permissions: "*"
        }]
    },
    httpAdminRoot: "/admin",
    httpNodeRoot: "/api",
    httpStatic: [
        {
            path: "/static",
            root: "/usr/src/node-red/public"
        }
    ],
    httpStaticRoot: "/static/",
    contextStorage: {
        default: {
            module: "localfilesystem"
        }
    },
    exportGlobalContextKeys: false,
    logging: {
        console: {
            level: "info",
            metrics: false,
            audit: false
        }
    },
    editorTheme: {
        page: {
            title: "Node-RED",
            favicon: "/absolute/path/to/theme/icon",
            css: "/absolute/path/to/custom/css/file",
            scripts: "/absolute/path/to/custom/script/file"
        },
        header: {
            title: "Node-RED",
            image: "/absolute/path/to/header/image", // or null to remove image
            url: "http://nodered.org" // optional url to make the header text/image a link to this url
        },
        deployButton: {
            type: "simple",
            label: "Save",
            icon: "/absolute/path/to/deploy/button/image" // or null to remove image
        },
        menu: { "menu-item-import-library": false, "menu-item-export-library": false, "menu-item-keyboard-shortcuts": false, "menu-item-help": { label: "Alternative Help Link", url: "http://example.com" } },
        userMenu: false, // Hide the user-menu even if adminAuth is enabled
        login: {
            image: "/absolute/path/to/login/page/big/image" // a 256x256 image
        },
        logout: {
            redirect: "/"
        }
    }
};'
    
    # Write settings.js file
    if execute_command "echo '$nodered_settings' | sudo tee /data/nodered/settings.js > /dev/null" "Create Node-RED settings file"; then
        print_success "Node-RED settings file created with authentication"
    else
        print_error "Failed to create Node-RED settings file"
        return 1
    fi
    
    # Set proper permissions for settings file
    if execute_command "sudo chown 1000:1000 /data/nodered/settings.js" "Set Node-RED settings file permissions"; then
        print_success "Node-RED settings file permissions set"
    else
        print_warning "Could not set Node-RED settings file permissions"
    fi
    
    # Ensure sufficient disk space before pulling images
    if ! ensure_sufficient_disk_space; then
        print_error "Cannot install Node-RED: insufficient disk space"
        return 1
    fi
    
    # Pre-pull Node-RED image with retry logic
    print_status "Pulling Node-RED Docker image with retry logic..."
    local pull_attempts=0
    local max_attempts=3
    local pull_success=false
    
    while [ $pull_attempts -lt $max_attempts ] && [ "$pull_success" = false ]; do
        pull_attempts=$((pull_attempts + 1))
        print_status "Docker pull attempt $pull_attempts/$max_attempts..."
        
        # Clean up any failed pulls before retry
        if [ $pull_attempts -gt 1 ]; then
            print_status "Cleaning up failed pull artifacts..."
            execute_command "sudo docker system prune -af --volumes" "Clean failed pull artifacts"
            execute_command "sudo docker builder prune -af" "Clean build cache"
            execute_command "sudo rm -rf /var/lib/docker/tmp/*" "Clean Docker temp files"
            
            # Perform more aggressive cleanup on retry
            print_status "Performing additional cleanup for retry..."
            execute_command "sudo apt clean" "Clean apt cache"
            execute_command "sudo rm -rf /tmp/*" "Clean /tmp directory"
            
            # Check disk space again after cleanup
            local available_space=$(check_disk_space)
            print_status "Available disk space after cleanup: ${available_space}MB"
            
            if [ "$available_space" -lt 1024 ]; then
                print_error "Still insufficient disk space after cleanup: ${available_space}MB"
                break
            fi
        fi
        
        # Check disk space before each pull attempt
        local available_space=$(check_disk_space)
        print_status "Available disk space: ${available_space}MB"
        
        if execute_command "sudo docker pull nodered/node-red:latest" "Pull Node-RED image (attempt $pull_attempts)"; then
            print_success "Node-RED image pulled successfully"
            pull_success=true
        else
            print_warning "Docker pull attempt $pull_attempts failed"
            if [ $pull_attempts -lt $max_attempts ]; then
                print_status "Waiting 15 seconds before retry..."
                sleep 15
            fi
        fi
    done
    
    if [ "$pull_success" = false ]; then
        print_error "Failed to pull Node-RED image after $max_attempts attempts"
        print_error "Possible causes:"
        print_error "- Insufficient disk space on target device"
        print_error "- Docker daemon issues"
        print_error "- Network connectivity problems"
        print_error "- Docker Hub rate limiting"
        return 1
    fi
    
    # Start Node-RED container with environment file
    print_status "Starting Node-RED container with environment configuration..."
    if execute_command "sudo docker run -d --name nodered --restart unless-stopped -p 1880:1880 -v /data/nodered:/data --env-file /data/nodered/.env --privileged --device /dev/ttyUSB0 --device /dev/ttyUSB1 --device /dev/ttyACM0 --device /dev/ttyACM1 nodered/node-red:latest" "Start Node-RED container"; then
        print_success "Node-RED container started with environment configuration"
    else
        print_error "Failed to start Node-RED container"
        return 1
    fi
    
    # Wait for container to be ready
    print_status "Waiting for Node-RED to be ready..."
    sleep 10
    
    # Verify Node-RED is running
    if execute_command "sudo docker ps | grep nodered" "Verify Node-RED container"; then
        print_success "Node-RED container is running"
    else
        print_error "Node-RED container verification failed"
        return 1
    fi
    
    print_success "Node-RED installation completed"
}

# Function to update Node-RED authentication with custom password
update_nodered_auth() {
    local new_password="${1:-admin}"
    print_status "Updating Node-RED authentication with new password..."
    
    # Check if Node-RED container is running
    if ! execute_command "sudo docker ps | grep nodered" "Check if Node-RED is running"; then
        print_error "Node-RED container is not running. Please install Node-RED first."
        return 1
    fi
    
    # Generate bcrypt hash for the new password
    print_status "Generating bcrypt hash for password..."
    local bcrypt_hash
    if bcrypt_hash=$(sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "sudo docker exec nodered node -e \"console.log(require('bcryptjs').hashSync(process.argv[1], 8))\" '$new_password'" 2>/dev/null | tail -1); then
        print_success "Bcrypt hash generated successfully"
        print_status "Generated hash: $bcrypt_hash"
    else
        print_error "Failed to generate bcrypt hash"
        return 1
    fi
    
    # Stop Node-RED container to update settings
    print_status "Stopping Node-RED container for settings update..."
    if execute_command "sudo docker stop nodered" "Stop Node-RED container"; then
        print_success "Node-RED container stopped"
    else
        print_error "Failed to stop Node-RED container"
        return 1
    fi
    
    # Create new settings.js with updated authentication
    print_status "Creating updated Node-RED settings with new authentication..."
    local nodered_settings="module.exports = {
    uiPort: process.env.PORT || 1880,
    mqttReconnectTime: 15000,
    serialReconnectTime: 15000,
    debugMaxLength: 1000,
    debugUseColors: true,
    flowFile: \"flows.json\",
    flowFilePretty: true,
    userDir: \"/data/\",
    nodesDir: \"/data/nodes\",
    functionGlobalContext: {},
    exportGlobalContextKeys: false,
    editorTheme: {
        projects: {
            enabled: false
        }
    },
    adminAuth: {
        type: \"credentials\",
        users: [{
            username: \"admin\",
            password: \"$bcrypt_hash\",
            permissions: \"*\"
        }]
    },
    httpAdminRoot: \"/admin\",
    httpNodeRoot: \"/api\",
    httpStatic: [
        {
            path: \"/static\",
            root: \"/usr/src/node-red/public\"
        }
    ],
    httpStaticRoot: \"/static/\",
    contextStorage: {
        default: {
            module: \"localfilesystem\"
        }
    },
    exportGlobalContextKeys: false,
    logging: {
        console: {
            level: \"info\",
            metrics: false,
            audit: false
        }
    },
    editorTheme: {
        page: {
            title: \"Node-RED\",
            favicon: \"/absolute/path/to/theme/icon\",
            css: \"/absolute/path/to/custom/css/file\",
            scripts: \"/absolute/path/to/custom/script/file\"
        },
        header: {
            title: \"Node-RED\",
            image: \"/absolute/path/to/header/image\",
            url: \"http://nodered.org\"
        },
        deployButton: {
            type: \"simple\",
            label: \"Save\",
            icon: \"/absolute/path/to/deploy/button/image\"
        },
        menu: { \"menu-item-import-library\": false, \"menu-item-export-library\": false, \"menu-item-keyboard-shortcuts\": false, \"menu-item-help\": { label: \"Alternative Help Link\", url: \"http://example.com\" } },
        userMenu: false,
        login: {
            image: \"/absolute/path/to/login/page/big/image\"
        },
        logout: {
            redirect: \"/\"
        }
    }
};"
    
    # Write updated settings.js file
    if execute_command "echo '$nodered_settings' | sudo tee /data/nodered/settings.js > /dev/null" "Create updated Node-RED settings file"; then
        print_success "Updated Node-RED settings file created with new authentication"
    else
        print_error "Failed to create updated Node-RED settings file"
        return 1
    fi
    
    # Set proper permissions for settings file
    if execute_command "sudo chown 1000:1000 /data/nodered/settings.js" "Set Node-RED settings file permissions"; then
        print_success "Node-RED settings file permissions set"
    else
        print_warning "Could not set Node-RED settings file permissions"
    fi
    
    # Start Node-RED container
    print_status "Starting Node-RED container with updated authentication..."
    if execute_command "sudo docker start nodered" "Start Node-RED container"; then
        print_success "Node-RED container started with updated authentication"
    else
        print_error "Failed to start Node-RED container"
        return 1
    fi
    
    # Wait for Node-RED to be ready
    print_status "Waiting for Node-RED to be ready..."
    sleep 15
    
    # Verify Node-RED is running
    if execute_command "sudo docker ps | grep nodered" "Verify Node-RED container"; then
        print_success "Node-RED container is running with updated authentication"
        print_success "New password: $new_password"
        print_success "Access Node-RED at: http://192.168.1.1:1880/admin"
    else
        print_error "Node-RED container verification failed"
        return 1
    fi
    
    print_success "Node-RED authentication updated successfully"
}

# Function to install Portainer with Docker Compose
install_portainer_docker() {
    print_status "Installing Portainer with Docker Compose..."
    
    # Check if Portainer container is already running
    if execute_command "sudo docker ps | grep portainer" "Check if Portainer is running"; then
        print_success "Portainer container is already running, skipping installation"
        return 0
    fi
    
    # Check if Portainer container exists but is stopped
    if execute_command "sudo docker ps -a | grep portainer" "Check if Portainer container exists"; then
        print_status "Portainer container exists but is stopped - starting it..."
        if execute_command "sudo docker start portainer" "Start existing Portainer container"; then
            print_success "Portainer container started successfully"
            return 0
        else
            print_warning "Failed to start existing Portainer container - will recreate"
        fi
    fi
    
    # Ensure internet connectivity before installation (needed for Docker image download)
    if ! ensure_internet_connectivity; then
        print_error "Cannot install Portainer: internet connectivity failed"
        return 1
    fi
    
    # Fix Docker networking issues before starting containers
    if ! fix_docker_networking; then
        print_warning "Docker networking fix failed, but continuing with installation"
    fi
    
    # Create Portainer data directory
    print_status "Creating Portainer data directory..."
    if execute_command "sudo mkdir -p /data/portainer" "Create Portainer directory"; then
        print_success "Portainer directory created"
    else
        print_error "Failed to create Portainer directory"
        return 1
    fi
    
    # Create Docker Compose file for Portainer
    print_status "Creating Portainer Docker Compose configuration..."
    portainer_compose='version: "3.8"

services:
  portainer:
    image: portainer/portainer-ce:latest
    container_name: portainer
    restart: unless-stopped
    ports:
      - "9000:9000"
      - "9443:9443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /data/portainer:/data
    networks:
      - portainer_network

networks:
  portainer_network:
    driver: bridge'
    
    # Write Docker Compose file
    if execute_command "echo '$portainer_compose' | sudo tee /data/portainer/docker-compose.yml > /dev/null" "Create Portainer compose file"; then
        print_success "Portainer Docker Compose file created"
    else
        print_error "Failed to create Portainer Docker Compose file"
        return 1
    fi
    
    # Create environment file for Portainer
    print_status "Creating Portainer environment configuration..."
    local portainer_env='# Portainer Environment Configuration
PORTAINER_ADMIN_USERNAME=admin
PORTAINER_ADMIN_PASSWORD=L@ranet2025
PORTAINER_LOG_LEVEL=INFO
PORTAINER_DEBUG=false'
    
    # Write environment file
    if execute_command "echo '$portainer_env' | sudo tee /data/portainer/.env > /dev/null" "Create Portainer environment file"; then
        print_success "Portainer environment file created"
    else
        print_error "Failed to create Portainer environment file"
        return 1
    fi
    
    # Set proper permissions for environment file
    if execute_command "sudo chown admin:admin /data/portainer/.env" "Set Portainer environment file permissions"; then
        print_success "Portainer environment file permissions set"
    else
        print_warning "Could not set Portainer environment file permissions"
    fi
    
    # Pre-pull Portainer image with retry logic
    print_status "Pulling Portainer Docker image with retry logic..."
    local pull_attempts=0
    local max_attempts=3
    local pull_success=false
    
    while [ $pull_attempts -lt $max_attempts ] && [ "$pull_success" = false ]; do
        pull_attempts=$((pull_attempts + 1))
        print_status "Docker pull attempt $pull_attempts/$max_attempts..."
        
        # Clean up any failed pulls before retry
        if [ $pull_attempts -gt 1 ]; then
            print_status "Cleaning up failed pull artifacts..."
            execute_command "sudo docker system prune -f" "Clean failed pull artifacts"
        fi
        
        if execute_command "sudo docker pull portainer/portainer-ce:latest" "Pull Portainer image (attempt $pull_attempts)"; then
            print_success "Portainer image pulled successfully"
            pull_success=true
        else
            print_warning "Docker pull attempt $pull_attempts failed"
            if [ $pull_attempts -lt $max_attempts ]; then
                print_status "Waiting 15 seconds before retry..."
                sleep 15
            fi
        fi
    done
    
    if [ "$pull_success" = false ]; then
        print_error "Failed to pull Portainer image after $max_attempts attempts"
        print_error "Possible causes:"
        print_error "- Insufficient disk space on target device"
        print_error "- Docker daemon issues"
        print_error "- Network connectivity problems"
        print_error "- Docker Hub rate limiting"
        return 1
    fi
    
    # Start Portainer container with environment file
    print_status "Starting Portainer container with environment configuration..."
    if execute_command "sudo docker run -d --name portainer --restart unless-stopped -p 9000:9000 -p 9443:9443 -v /var/run/docker.sock:/var/run/docker.sock -v /data/portainer:/data --env-file /data/portainer/.env portainer/portainer-ce:latest" "Start Portainer container"; then
        print_success "Portainer container started with environment configuration"
    else
        print_error "Failed to start Portainer container"
        return 1
    fi
    
    # Wait for container to be ready
    print_status "Waiting for Portainer to be ready..."
    sleep 10
    
    # Verify Portainer is running
    if execute_command "sudo docker ps | grep portainer" "Verify Portainer container"; then
        print_success "Portainer container is running"
    else
        print_error "Portainer container verification failed"
        return 1
    fi
    
    print_success "Portainer installation completed"
}

# Function to install Restreamer with Docker Compose
install_restreamer_docker() {
    print_status "Installing Restreamer with Docker Compose..."
    
    # Check if Restreamer container is already running
    if execute_command "sudo docker ps | grep restreamer" "Check if Restreamer is running"; then
        print_success "Restreamer container is already running, skipping installation"
        return 0
    fi
    
    # Check if Restreamer container exists but is stopped
    if execute_command "sudo docker ps -a | grep restreamer" "Check if Restreamer container exists"; then
        print_status "Restreamer container exists but is stopped - starting it..."
        if execute_command "sudo docker start restreamer" "Start existing Restreamer container"; then
            print_success "Restreamer container started successfully"
            return 0
        else
            print_warning "Failed to start existing Restreamer container - will recreate"
        fi
    fi
    
    # Ensure internet connectivity before installation (needed for Docker image download)
    if ! ensure_internet_connectivity; then
        print_error "Cannot install Restreamer: internet connectivity failed"
        return 1
    fi
    
    # Fix Docker networking issues before starting containers
    if ! fix_docker_networking; then
        print_warning "Docker networking fix failed, but continuing with installation"
    fi
    
    # Create Restreamer data directory
    print_status "Creating Restreamer data directory..."
    if execute_command "sudo mkdir -p /data/restreamer" "Create Restreamer directory"; then
        print_success "Restreamer directory created"
    else
        print_error "Failed to create Restreamer directory"
        return 1
    fi
    
    # Create Docker Compose file for Restreamer
    print_status "Creating Restreamer Docker Compose configuration..."
    restreamer_compose='version: "3.8"

services:
  restreamer:
    image: datarhei/restreamer:latest
    container_name: restreamer
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - /data/restreamer:/restreamer/db
    environment:
      - RS_USERNAME=admin
      - RS_PASSWORD=L@ranet2025
    privileged: true
    devices:
      - /dev/video0:/dev/video0
      - /dev/video1:/dev/video1
    networks:
      - restreamer_network

networks:
  restreamer_network:
    driver: bridge'
    
    # Write Docker Compose file
    if execute_command "echo '$restreamer_compose' | sudo tee /data/restreamer/docker-compose.yml > /dev/null" "Create Restreamer compose file"; then
        print_success "Restreamer Docker Compose file created"
    else
        print_error "Failed to create Restreamer Docker Compose file"
        return 1
    fi
    
    # Create environment file for Restreamer
    print_status "Creating Restreamer environment configuration..."
    
    # Write environment file line by line to avoid SSH issues with multi-line strings
    if execute_command "sudo tee /data/restreamer/.env > /dev/null << 'EOF'
# Restreamer Environment Configuration
RS_USERNAME=admin
RS_PASSWORD=L@ranet2025
RS_LOGLEVEL=info
RS_DEBUG=false
EOF" "Create Restreamer environment file"; then
        print_success "Restreamer environment file created"
    else
        print_error "Failed to create Restreamer environment file"
        return 1
    fi
    
    # Set proper permissions for environment file
    if execute_command "sudo chown admin:admin /data/restreamer/.env" "Set environment file permissions"; then
        print_success "Environment file permissions set"
    else
        print_warning "Could not set environment file permissions"
    fi
    
    # Pre-pull Restreamer image with retry logic
    print_status "Pulling Restreamer Docker image with retry logic..."
    local pull_attempts=0
    local max_attempts=3
    local pull_success=false
    
    while [ $pull_attempts -lt $max_attempts ] && [ "$pull_success" = false ]; do
        pull_attempts=$((pull_attempts + 1))
        print_status "Docker pull attempt $pull_attempts/$max_attempts..."
        
        # Clean up any failed pulls before retry
        if [ $pull_attempts -gt 1 ]; then
            print_status "Cleaning up failed pull artifacts..."
            execute_command "sudo docker system prune -f" "Clean failed pull artifacts"
        fi
        
        if execute_command "sudo docker pull datarhei/restreamer:latest" "Pull Restreamer image (attempt $pull_attempts)"; then
            print_success "Restreamer image pulled successfully"
            pull_success=true
        else
            print_warning "Docker pull attempt $pull_attempts failed"
            if [ $pull_attempts -lt $max_attempts ]; then
                print_status "Waiting 15 seconds before retry..."
                sleep 15
            fi
        fi
    done
    
    if [ "$pull_success" = false ]; then
        print_error "Failed to pull Restreamer image after $max_attempts attempts"
        print_error "Possible causes:"
        print_error "- Insufficient disk space on target device"
        print_error "- Docker daemon issues"
        print_error "- Network connectivity problems"
        print_error "- Docker Hub rate limiting"
        return 1
    fi
    
    # Start Restreamer container with environment file
    print_status "Starting Restreamer container with environment configuration..."
    if execute_command "sudo docker run -d --name restreamer --restart unless-stopped -p 8080:8080 -v /data/restreamer:/restreamer/db --env-file /data/restreamer/.env --privileged --device /dev/video0 --device /dev/video1 datarhei/restreamer:latest" "Start Restreamer container"; then
        print_success "Restreamer container started with environment configuration"
    else
        print_error "Failed to start Restreamer container"
        return 1
    fi
    
    # Wait for container to be ready
    print_status "Waiting for Restreamer to be ready..."
    sleep 10
    
    # Verify Restreamer is running
    if execute_command "sudo docker ps | grep restreamer" "Verify Restreamer container"; then
        print_success "Restreamer container is running"
    else
        print_error "Restreamer container verification failed"
        return 1
    fi
    
    print_success "Restreamer installation completed"
}

# Function to install all Docker services
install_docker_services() {
    print_status "Installing all Docker services (Node-RED, Portainer, Restreamer)..."
    
    # Ensure sufficient disk space before starting
    if ! ensure_sufficient_disk_space; then
        print_error "Cannot install Docker services: insufficient disk space"
        return 1
    fi
    
    # Install Node-RED
    if install_nodered_docker; then
        print_success "Node-RED installed successfully"
    else
        print_error "Node-RED installation failed"
        return 1
    fi
    
    # Install Portainer
    if install_portainer_docker; then
        print_success "Portainer installed successfully"
    else
        print_error "Portainer installation failed"
        return 1
    fi
    
    # Install Restreamer
    if install_restreamer_docker; then
        print_success "Restreamer installed successfully"
    else
        print_error "Restreamer installation failed"
        return 1
    fi
    
    print_success "All Docker services installed successfully"
}

# Function to install Node-RED nodes
install_nodered_nodes() {
    print_status "Installing Node-RED nodes..."
    
    # Check if Node-RED container is running
    if ! execute_command "sudo docker ps | grep nodered" "Check if Node-RED is running"; then
        print_error "Node-RED container is not running. Please install Node-RED first."
        return 1
    fi
    
    # Ensure internet connectivity before installation (needed for npm package downloads)
    if ! ensure_internet_connectivity; then
        print_error "Cannot install Node-RED nodes: internet connectivity failed"
        return 1
    fi
    
    # Determine package.json source based on parameter or auto-detect
    local package_source_type="${PACKAGE_SOURCE:-${FLOWS_SOURCE:-auto}}"
    local package_file=""
    local package_source=""
    
    if [ "$package_source_type" = "github" ]; then
        # Force GitHub download
        print_status "Forcing GitHub download for package.json..."
        if download_package_from_github; then
            if [ "$USE_SSH" = true ] && [ -n "$REMOTE_HOST" ]; then
                package_file="/home/$REMOTE_USER/package.json"
            else
                package_file="$HOME/package.json"
            fi
            package_source="GitHub download (forced)"
        else
            print_error "Failed to download package.json from GitHub"
            return 1
        fi
    elif [ "$package_source_type" = "local" ]; then
        # Force local file search
        print_status "Searching for local package.json files..."
        if [ -f "./nodered_flows_backup/package.json" ]; then
            package_file="./nodered_flows_backup/package.json"
            package_source="local directory (forced)"
        elif [ -f "../nodered_flows_backup/package.json" ]; then
            package_file="../nodered_flows_backup/package.json"
            package_source="parent directory (forced)"
        elif [ -f "$(dirname "$0")/nodered_flows_backup/package.json" ]; then
            package_file="$(dirname "$0")/nodered_flows_backup/package.json"
            package_source="script directory (forced)"
        elif [ -f "$HOME/nodered_flows_backup/package.json" ]; then
            package_file="$HOME/nodered_flows_backup/package.json"
            package_source="home directory (forced)"
        else
            print_error "No local package.json found in any of these locations:"
            print_error "  - ./nodered_flows_backup/package.json"
            print_error "  - ../nodered_flows_backup/package.json"
            print_error "  - ~/nodered_flows_backup/package.json"
            return 1
        fi
    elif [ "$package_source_type" = "uploaded" ]; then
        # Use uploaded package.json file
        if [ -n "$UPLOADED_PACKAGE_FILE" ] && [ -f "$UPLOADED_PACKAGE_FILE" ]; then
            package_file="$UPLOADED_PACKAGE_FILE"
            package_source="uploaded file"
        else
            print_error "No uploaded package.json file specified or file not found"
            return 1
        fi
    else
        # Auto-detect (default behavior)
        print_status "Auto-detecting package.json source..."
        if [ -f "./nodered_flows_backup/package.json" ]; then
            package_file="./nodered_flows_backup/package.json"
            package_source="local directory (auto-detected)"
        elif [ -f "../nodered_flows_backup/package.json" ]; then
            package_file="../nodered_flows_backup/package.json"
            package_source="parent directory (auto-detected)"
        elif [ -f "$(dirname "$0")/nodered_flows_backup/package.json" ]; then
            package_file="$(dirname "$0")/nodered_flows_backup/package.json"
            package_source="script directory (auto-detected)"
        elif [ -f "$HOME/nodered_flows_backup/package.json" ]; then
            package_file="$HOME/nodered_flows_backup/package.json"
            package_source="home directory (auto-detected)"
        else
            print_status "No local package.json found, downloading from GitHub..."
            if download_package_from_github; then
                if [ "$USE_SSH" = true ] && [ -n "$REMOTE_HOST" ]; then
                    package_file="/home/$REMOTE_USER/package.json"
                else
                    package_file="$HOME/package.json"
                fi
                package_source="GitHub download (auto-detected)"
            else
                print_warning "Failed to download package.json from GitHub, using default nodes"
                package_file=""
                package_source="default hardcoded"
            fi
        fi
    fi
    
    if [ -n "$package_file" ] && [ "$package_source" != "default hardcoded" ]; then
        print_status "Found package.json: $package_file (source: $package_source)"
        
        # Ensure Node-RED data directory exists and has proper permissions
        print_status "Ensuring Node-RED data directory exists..."
        if execute_command "sudo mkdir -p /data/nodered && sudo chown 1000:1000 /data/nodered && sudo chmod 755 /data/nodered" "Create Node-RED data directory"; then
            print_success "Node-RED data directory ready"
        else
            print_warning "Could not create Node-RED data directory"
        fi
        
        # Copy package.json to Node-RED data directory
        if [[ "$package_source" != *"GitHub download"* ]]; then
            print_status "Copying package.json to Node-RED data directory..."
            if [ "$USE_SSH" = true ] && [ -n "$REMOTE_HOST" ]; then
                # For remote systems, copy to temp location first, then move with sudo
                if copy_to_remote "$package_file" "/tmp/package.json" "Copy package.json to temp location"; then
                    if execute_command "sudo mv /tmp/package.json /data/nodered/package.json" "Move package.json to Node-RED data directory"; then
                        print_success "package.json copied to Node-RED data directory"
                    else
                        print_error "Failed to move package.json to Node-RED data directory"
                        return 1
                    fi
                else
                    print_error "Failed to copy package.json to temp location"
                    return 1
                fi
            else
                # For local systems, copy directly to /data/nodered/
                if copy_to_remote "$package_file" "/data/nodered/package.json" "Copy package.json to Node-RED data directory"; then
                    print_success "package.json copied to Node-RED data directory"
                else
                    print_error "Failed to copy package.json to Node-RED data directory"
                    return 1
                fi
            fi
        else
            print_status "Package.json already downloaded to remote system, skipping copy"
        fi
        
        # Set proper permissions for the package.json file
        print_status "Setting proper permissions for package.json file..."
        if execute_command "sudo chown 1000:1000 /data/nodered/package.json" "Set package.json permissions"; then
            print_success "package.json permissions set"
        else
            print_warning "Could not set package.json permissions"
        fi
        
        # Install nodes from package.json
        print_status "Installing Node-RED nodes from package.json..."
        if execute_command "sudo docker exec -w /data nodered npm install --production" "Install nodes from package.json"; then
            print_success "Node-RED nodes installed from package.json successfully"
        else
            print_error "Failed to install nodes from package.json"
            return 1
        fi
    else
        # Fallback to hardcoded nodes
        print_status "Using default hardcoded Node-RED nodes..."
        
        # Define the nodes to install (fallback)
        local nodes=(
            "node-red-contrib-ffmpeg@~0.1.1"
            "node-red-contrib-queue-gate@~1.5.5"
            "node-red-node-sqlite@~1.1.0"
            "node-red-node-serialport@2.0.3"
        )
        
        # Install each node
        for node in "${nodes[@]}"; do
            print_status "Installing Node-RED node: $node"
            if execute_command "sudo docker exec nodered npm install $node" "Install $node"; then
                print_success "Successfully installed $node"
            else
                print_error "Failed to install $node"
                return 1
            fi
        done
    fi
    
    # Restart Node-RED container to load new nodes
    print_status "Restarting Node-RED container to load new nodes..."
    if execute_command "sudo docker restart nodered" "Restart Node-RED container"; then
        print_success "Node-RED container restarted"
    else
        print_error "Failed to restart Node-RED container"
        return 1
    fi
    
    # Wait for Node-RED to be ready
    print_status "Waiting for Node-RED to be ready..."
    sleep 15
    
    # Verify Node-RED is running
    if execute_command "sudo docker ps | grep nodered" "Verify Node-RED container"; then
        print_success "Node-RED container is running with new nodes"
    else
        print_error "Node-RED container verification failed"
        return 1
    fi
    
    print_success "Node-RED nodes installation completed"
}

# Function to download flows from GitHub
download_flows_from_github() {
    print_status "Downloading Node-RED flows from GitHub..."
    
    # GitHub URLs for flows (you can customize these)
    local github_flows_url="https://raw.githubusercontent.com/Loranet-Technologies/bivicom-config-bot/main/uploaded_files/flows.json"
    local github_package_url="https://raw.githubusercontent.com/Loranet-Technologies/bivicom-config-bot/main/uploaded_files/package.json"
    
    # Check if curl is available
    if ! command -v curl >/dev/null 2>&1; then
        print_error "curl is not installed. Cannot download from GitHub."
        return 1
    fi
    
    # Download flows.json to a safer location
    print_status "Downloading flows.json from GitHub..."
    local download_path
    if [ "$USE_SSH" = true ] && [ -n "$REMOTE_HOST" ]; then
        download_path="/home/$REMOTE_USER/flows.json"
    else
        download_path="$HOME/flows.json"
    fi
    if execute_command "curl -s -L -o $download_path '$github_flows_url'" "Download flows.json"; then
        print_success "flows.json downloaded successfully"
    else
        print_error "Failed to download flows.json from GitHub"
        return 1
    fi
    
    # Verify the downloaded file
    print_status "Verifying downloaded flows file..."
    execute_command "ls -la $download_path" "Check flows file details"
    execute_command "wc -c $download_path" "Check flows file size"
    execute_command "test -f $download_path && echo 'File exists' || echo 'File missing'" "Test flows file existence"
    execute_command "test -s $download_path && echo 'File not empty' || echo 'File is empty'" "Test flows file size"
    
    # Use a more explicit verification
    if execute_command "test -f $download_path && test -s $download_path" "Verify flows file exists and not empty"; then
        print_success "Flows file verification passed"
    else
        print_error "Downloaded flows.json is empty or missing"
        return 1
    fi
    
    # Download package.json (optional)
    print_status "Downloading package.json from GitHub..."
    if execute_command "curl -s -L -o /tmp/package.json '$github_package_url'" "Download package.json"; then
        print_success "package.json downloaded successfully"
    else
        print_warning "Failed to download package.json (optional)"
    fi
    
    print_success "GitHub download completed"
    return 0
}

# Function to download package.json from GitHub
download_package_from_github() {
    print_status "Downloading package.json from GitHub..."
    
    # GitHub URL for package.json (you can customize this)
    local github_package_url="https://raw.githubusercontent.com/Loranet-Technologies/bivicom-config-bot/main/uploaded_files/package.json"
    
    # Check if curl is available
    if ! command -v curl >/dev/null 2>&1; then
        print_error "curl is not installed. Cannot download from GitHub."
        return 1
    fi
    
    # Download package.json to a safer location
    print_status "Downloading package.json from GitHub..."
    local download_path
    if [ "$USE_SSH" = true ] && [ -n "$REMOTE_HOST" ]; then
        download_path="/home/$REMOTE_USER/package.json"
    else
        download_path="$HOME/package.json"
    fi
    
    # Download package.json and check for success
    if execute_command "curl -s -L -f -o $download_path '$github_package_url'" "Download package.json"; then
        print_success "package.json downloaded successfully"
    else
        print_error "Failed to download package.json from GitHub"
        execute_command "rm -f $download_path" "Clean up failed download"
        return 1
    fi
    
    # Verify the downloaded file
    print_status "Verifying downloaded file..."
    execute_command "ls -la $download_path" "Check file details"
    execute_command "wc -c $download_path" "Check file size"
    execute_command "test -f $download_path && echo 'File exists' || echo 'File missing'" "Test file existence"
    execute_command "test -s $download_path && echo 'File not empty' || echo 'File is empty'" "Test file size"
    
    # Use a more explicit verification
    if execute_command "test -f $download_path && test -s $download_path" "Verify file exists and not empty"; then
        print_success "File verification passed"
    else
        print_error "Downloaded package.json is empty or missing"
        return 1
    fi
    
    print_success "package.json GitHub download completed"
    return 0
}

# Function to import Node-RED flows
import_nodered_flows() {
    print_status "Importing Node-RED flows..."
    
    # Check if Node-RED container is running
    if ! execute_command "sudo docker ps | grep nodered" "Check if Node-RED is running"; then
        print_error "Node-RED container is not running. Please install Node-RED first."
        return 1
    fi
    
    # Ensure internet connectivity before installation (needed for GitHub downloads)
    if ! ensure_internet_connectivity; then
        print_error "Cannot import Node-RED flows: internet connectivity failed"
        return 1
    fi
    
    # Determine flows source based on parameter or auto-detect
    local flows_source_type="${FLOWS_SOURCE:-auto}"
    local flows_file=""
    local flows_source=""
    
    if [ "$flows_source_type" = "github" ]; then
        # Force GitHub download
        print_status "Forcing GitHub download for flows..."
        if download_flows_from_github; then
            if [ "$USE_SSH" = true ] && [ -n "$REMOTE_HOST" ]; then
                flows_file="/home/$REMOTE_USER/flows.json"
            else
                flows_file="$HOME/flows.json"
            fi
            flows_source="GitHub download (forced)"
        else
            print_error "Failed to download flows from GitHub"
            return 1
        fi
    elif [ "$flows_source_type" = "local" ]; then
        # Force local file search
        print_status "Searching for local flows.json files..."
        if [ -f "./nodered_flows_backup/flows.json" ]; then
            flows_file="./nodered_flows_backup/flows.json"
            flows_source="local directory (forced)"
        elif [ -f "../nodered_flows_backup/flows.json" ]; then
            flows_file="../nodered_flows_backup/flows.json"
            flows_source="parent directory (forced)"
        elif [ -f "$(dirname "$0")/nodered_flows_backup/flows.json" ]; then
            flows_file="$(dirname "$0")/nodered_flows_backup/flows.json"
            flows_source="script directory (forced)"
        elif [ -f "$HOME/nodered_flows_backup/flows.json" ]; then
            flows_file="$HOME/nodered_flows_backup/flows.json"
            flows_source="home directory (forced)"
        else
            print_error "No local flows.json found in any of these locations:"
            print_error "  - ./nodered_flows_backup/flows.json"
            print_error "  - ../nodered_flows_backup/flows.json"
            print_error "  - ~/nodered_flows_backup/flows.json"
            return 1
        fi
    elif [ "$flows_source_type" = "uploaded" ]; then
        # Use uploaded flows.json file
        if [ -n "$UPLOADED_FLOWS_FILE" ] && [ -f "$UPLOADED_FLOWS_FILE" ]; then
            flows_file="$UPLOADED_FLOWS_FILE"
            flows_source="uploaded file"
        else
            print_error "No uploaded flows.json file specified or file not found"
            return 1
        fi
    else
        # Auto-detect (default behavior)
        print_status "Auto-detecting flows source..."
        if [ -f "./nodered_flows_backup/flows.json" ]; then
            flows_file="./nodered_flows_backup/flows.json"
            flows_source="local directory (auto-detected)"
        elif [ -f "../nodered_flows_backup/flows.json" ]; then
            flows_file="../nodered_flows_backup/flows.json"
            flows_source="parent directory (auto-detected)"
        elif [ -f "$(dirname "$0")/nodered_flows_backup/flows.json" ]; then
            flows_file="$(dirname "$0")/nodered_flows_backup/flows.json"
            flows_source="script directory (auto-detected)"
        elif [ -f "$HOME/nodered_flows_backup/flows.json" ]; then
            flows_file="$HOME/nodered_flows_backup/flows.json"
            flows_source="home directory (auto-detected)"
        else
            print_status "No local flows.json found, downloading from GitHub..."
            if download_flows_from_github; then
                if [ "$USE_SSH" = true ] && [ -n "$REMOTE_HOST" ]; then
                    flows_file="/home/$REMOTE_USER/flows.json"
                else
                    flows_file="$HOME/flows.json"
                fi
                flows_source="GitHub download (auto-detected)"
            else
                print_error "Failed to download flows from GitHub and no local flows.json found"
                print_error "Please ensure flows.json exists in one of these locations:"
                print_error "  - ./nodered_flows_backup/flows.json"
                print_error "  - ../nodered_flows_backup/flows.json"
                print_error "  - ~/nodered_flows_backup/flows.json"
                return 1
            fi
        fi
    fi
    
    print_status "Found flows file: $flows_file (source: $flows_source)"
    
    # Ensure Node-RED data directory exists and has proper permissions
    print_status "Ensuring Node-RED data directory exists..."
    if execute_command "sudo mkdir -p /data/nodered && sudo chown 1000:1000 /data/nodered && sudo chmod 755 /data/nodered" "Create Node-RED data directory"; then
        print_success "Node-RED data directory ready"
    else
        print_warning "Could not create Node-RED data directory"
    fi
    
    # Copy flows.json to Node-RED data directory
    if [[ "$flows_source" != *"GitHub download"* ]]; then
        print_status "Copying flows.json to Node-RED data directory..."
        if [ "$USE_SSH" = true ] && [ -n "$REMOTE_HOST" ]; then
            # For remote systems, copy to temp location first, then move with sudo
            if copy_to_remote "$flows_file" "/tmp/flows.json" "Copy flows file to temp location"; then
                if execute_command "sudo mv /tmp/flows.json /data/nodered/flows.json" "Move flows file to Node-RED data directory"; then
                    print_success "Flows file copied to Node-RED data directory"
                else
                    print_error "Failed to move flows file to Node-RED data directory"
                    return 1
                fi
            else
                print_error "Failed to copy flows file to temp location"
                return 1
            fi
        else
            # For local systems, copy directly to /data/nodered/
            if copy_to_remote "$flows_file" "/data/nodered/flows.json" "Copy flows file to Node-RED data directory"; then
                print_success "Flows file copied to Node-RED data directory"
            else
                print_error "Failed to copy flows file to Node-RED data directory"
                return 1
            fi
        fi
    else
        print_status "Flows.json already downloaded to remote system, skipping copy"
    fi
    
    # Set proper permissions for the flows file
    print_status "Setting proper permissions for flows file..."
    if execute_command "sudo chown 1000:1000 /data/nodered/flows.json" "Set flows permissions"; then
        print_success "Flows permissions set"
    else
        print_warning "Could not set flows permissions"
    fi
    
    # Restart Node-RED container to load new flows
    print_status "Restarting Node-RED container to load new flows..."
    if execute_command "sudo docker restart nodered" "Restart Node-RED container"; then
        print_success "Node-RED container restarted"
    else
        print_error "Failed to restart Node-RED container"
        return 1
    fi
    
    # Wait for Node-RED to be ready
    print_status "Waiting for Node-RED to load new flows..."
    sleep 20
    
    # Verify Node-RED is running
    if execute_command "sudo docker ps | grep nodered" "Verify Node-RED container"; then
        print_success "Node-RED container is running with imported flows"
    else
        print_error "Node-RED container verification failed"
        return 1
    fi
    
    print_success "Node-RED flows import completed"
}


# Function to install Tailscale with Docker
install_tailscale_docker() {
    local custom_auth_key="$1"
    print_status "Installing Tailscale with Docker..."
    
    # Check if Tailscale container is already running
    if execute_command "sudo docker ps | grep tailscale" "Check if Tailscale is running"; then
        print_success "Tailscale container is already running, skipping installation"
        return 0
    fi
    
    # Check if Tailscale container exists but is stopped
    if execute_command "sudo docker ps -a | grep tailscale" "Check if Tailscale container exists"; then
        print_status "Tailscale container exists but is stopped - starting it..."
        if execute_command "sudo docker start tailscale" "Start existing Tailscale container"; then
            print_success "Tailscale container started successfully"
            return 0
        else
            print_warning "Failed to start existing Tailscale container - will recreate"
        fi
    fi
    
    # Ensure internet connectivity before installation (needed for Docker image download)
    if ! ensure_internet_connectivity; then
        print_error "Cannot install Tailscale: internet connectivity failed"
        return 1
    fi
    
    # Fix Docker networking issues before starting containers
    if ! fix_docker_networking; then
        print_warning "Docker networking fix failed, but continuing with installation"
    fi
    
    # Create Tailscale data directory
    print_status "Creating Tailscale data directory..."
    if execute_command "sudo mkdir -p /data/tailscale" "Create Tailscale directory"; then
        print_success "Tailscale directory created"
    else
        print_error "Failed to create Tailscale directory"
        return 1
    fi
    
    # Create environment file for Tailscale
    print_status "Creating Tailscale environment configuration..."
    
    # Use custom auth key if provided, otherwise use default
    local auth_key="tskey-auth-kvwRxYc6o321CNTRL-6kggdogXnMdAdewR7Y7cMdNSp7yrJsSC"
    if [ -n "$custom_auth_key" ]; then
        auth_key="$custom_auth_key"
        print_status "Using custom auth key provided by user"
    else
        print_status "Using default auth key"
    fi
    
    local tailscale_env="# Tailscale Environment Configuration
TS_AUTHKEY=$auth_key
TS_STATE_DIR=/var/lib/tailscale
TS_USERSPACE=false
TS_ACCEPT_DNS=true"
    
    # Write environment file
    if execute_command "echo '$tailscale_env' | sudo tee /data/tailscale/.env > /dev/null" "Create Tailscale environment file"; then
        print_success "Tailscale environment file created"
    else
        print_error "Failed to create Tailscale environment file"
        return 1
    fi
    
    # Set proper permissions for environment file
    if execute_command "sudo chown admin:admin /data/tailscale/.env" "Set Tailscale environment file permissions"; then
        print_success "Tailscale environment file permissions set"
    else
        print_warning "Could not set Tailscale environment file permissions"
    fi
    
    # Create Docker Compose file for Tailscale
    print_status "Creating Tailscale Docker Compose file..."
    local tailscale_compose='version: "3.8"

services:
  tailscale:
    image: tailscale/tailscale:latest
    container_name: tailscale
    restart: unless-stopped
    env_file:
      - .env
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    devices:
      - /dev/net/tun
    volumes:
      - ./:/var/lib/tailscale
    network_mode: host'
    
    # Write Docker Compose file
    if execute_command "echo '$tailscale_compose' | sudo tee /data/tailscale/docker-compose.yml > /dev/null" "Create Tailscale compose file"; then
        print_success "Tailscale Docker Compose file created"
    else
        print_error "Failed to create Tailscale Docker Compose file"
        return 1
    fi
    
    # Create README.md file
    print_status "Creating Tailscale README documentation..."
    local tailscale_readme='# Tailscale VPN Router Configuration

This directory contains the configuration and data for the Tailscale VPN router container.

## Files

- `.env` - Environment configuration file
- `docker-compose.yml` - Docker Compose configuration
- `README.md` - This documentation file

## Configuration

### Environment Variables (.env)

The `.env` file contains the following configuration options:

```bash
# Tailscale Environment Configuration
TS_AUTHKEY=tskey-auth-kvwRxYc6o321CNTRL-6kggdogXnMdAdewR7Y7cMdNSp7yrJsSC
TS_STATE_DIR=/var/lib/tailscale
TS_USERSPACE=false
TS_ACCEPT_DNS=true
```


## Management Commands

### Start Tailscale
```bash
cd /data/tailscale
sudo docker compose up -d
```

### Stop Tailscale
```bash
cd /data/tailscale
sudo docker compose down
```

### Restart Tailscale
```bash
cd /data/tailscale
sudo docker compose restart
```

### Check Status
```bash
sudo docker exec tailscale tailscale status
```

### View Logs
```bash
sudo docker compose logs -f tailscale
```


## Network Configuration

### Default Settings
- **DNS**: Accepts Tailscale DNS servers
- **User Space**: Disabled (kernel mode for better performance)
- **Network Mode**: Host networking for full network access


## Troubleshooting

### Container Not Starting
1. Check if Docker is running: `sudo systemctl status docker`
2. Check logs: `sudo docker compose logs tailscale`
3. Verify permissions: `ls -la /data/tailscale/`


### Authentication Issues
1. Verify auth key in `.env` file
2. Check Tailscale admin console
3. Generate new auth key if needed

## Security Notes

- The auth key provides automatic authentication
- Regularly rotate auth keys for security

## Support

For more information, visit:
- [Tailscale Documentation](https://tailscale.com/kb/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
'
    
    # Write README file
    if execute_command "echo '$tailscale_readme' | sudo tee /data/tailscale/README.md > /dev/null" "Create Tailscale README"; then
        print_success "Tailscale README documentation created"
    else
        print_error "Failed to create Tailscale README"
        return 1
    fi
    
    # Set proper permissions for all files
    if execute_command "sudo chown -R admin:admin /data/tailscale" "Set Tailscale directory permissions"; then
        print_success "Tailscale directory permissions set"
    else
        print_warning "Could not set Tailscale directory permissions"
    fi
    
    # Check if Docker Compose is available (should be installed with Docker)
    if execute_command "which docker-compose >/dev/null 2>&1 || docker compose version >/dev/null 2>&1" "Check Docker Compose availability"; then
        # Start Tailscale container using Docker Compose
        print_status "Starting Tailscale container with Docker Compose..."
        if execute_command "cd /data/tailscale && sudo docker-compose up -d" "Start Tailscale container with docker-compose"; then
            print_success "Tailscale container started with Docker Compose"
        else
            print_error "Failed to start Tailscale container with docker-compose, trying docker compose..."
            if execute_command "cd /data/tailscale && sudo docker compose up -d" "Start Tailscale container with docker compose"; then
                print_success "Tailscale container started with Docker Compose"
            else
                print_error "Failed to start Tailscale container with Docker Compose, falling back to docker run..."
                # Fallback to docker run
                if execute_command "sudo docker run -d --name tailscale --restart unless-stopped --cap-add=NET_ADMIN --cap-add=SYS_MODULE --device=/dev/net/tun -v /data/tailscale:/var/lib/tailscale --network host --env-file /data/tailscale/.env tailscale/tailscale:latest" "Start Tailscale container with docker run"; then
                    print_success "Tailscale container started with Docker run"
                else
                    print_error "Failed to start Tailscale container"
                    return 1
                fi
            fi
        fi
    else
        # Docker Compose not available, use docker run
        print_status "Docker Compose not available, using Docker run..."
        if execute_command "sudo docker run -d --name tailscale --restart unless-stopped --cap-add=NET_ADMIN --cap-add=SYS_MODULE --device=/dev/net/tun -v /data/tailscale:/var/lib/tailscale --network host --env-file /data/tailscale/.env tailscale/tailscale:latest" "Start Tailscale container with docker run"; then
            print_success "Tailscale container started with Docker run"
        else
            print_error "Failed to start Tailscale container"
            return 1
        fi
    fi
    
    # Wait for Tailscale to be ready
    print_status "Waiting for Tailscale to be ready..."
    sleep 15
    
    # Verify Tailscale is running
    if execute_command "sudo docker ps | grep tailscale" "Verify Tailscale container"; then
        print_success "Tailscale container is running"
    else
        print_error "Tailscale container verification failed"
        return 1
    fi
    
    # Check Tailscale status
    print_status "Checking Tailscale status..."
    if execute_command "sudo docker exec tailscale tailscale status" "Check Tailscale status"; then
        print_success "Tailscale status checked"
    else
        print_warning "Could not check Tailscale status (may still be connecting)"
    fi
    
    print_success "Tailscale installation completed"
    print_status "Tailscale is now managed with Docker Compose in /data/tailscale/"
    print_status "Documentation: /data/tailscale/README.md"
    print_status "Management: cd /data/tailscale && sudo docker compose [up|down|restart|logs]"
}

# Function to stop Tailscale container
tailscale_down() {
    print_status "Stopping Tailscale..."
    execute_command "cd /data/tailscale && sudo docker compose down" "Stop Tailscale"
}

# Function to restart Tailscale container
tailscale_restart() {
    local custom_auth_key="$1"
    print_status "Restarting Tailscale..."
    
    # Update auth key if provided
    if [ -n "$custom_auth_key" ]; then
        execute_command "echo 'TS_AUTHKEY=$custom_auth_key' | sudo tee /data/tailscale/.env > /dev/null" "Update auth key"
    fi
    
    # Restart with docker compose
    execute_command "cd /data/tailscale && sudo docker compose restart" "Restart Tailscale"
}

# Function to start Tailscale container with current auth key
tailscale_up() {
    local custom_auth_key="$1"
    print_status "Starting Tailscale..."
    
    # Update auth key if provided
    if [ -n "$custom_auth_key" ]; then
        execute_command "echo 'TS_AUTHKEY=$custom_auth_key' | sudo tee /data/tailscale/.env > /dev/null" "Update auth key"
    fi
    
    # Start with docker compose
    execute_command "cd /data/tailscale && sudo docker compose up -d" "Start Tailscale"
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

# Function to reset device to default state
reset_device() {
    print_status "Starting device reset to default state..."
    print_warning "This will remove all Docker containers, reset network to REVERSE mode, and restore default credentials"
    
    # Ping remote host once (if using SSH)
    if [ "$USE_SSH" = true ] && [ -n "$REMOTE_HOST" ]; then
        if ! ping_remote_host; then
            print_error "Cannot reset device: Remote host is not reachable"
            return 1
        fi
    fi
    
    # Check if UCI is available
    if ! check_uci_available; then
        print_error "UCI command not found! This device may not be running OpenWrt."
        print_error "Cannot perform network reset without UCI. Please ensure the target device is running OpenWrt."
        return 1
    fi
    
    print_success "UCI is available, proceeding with device reset..."
    
    # Check if Docker is installed (used throughout the function)
    docker_installed=false
    if execute_command "which docker >/dev/null 2>&1" "Check if Docker is installed"; then
        docker_installed=true
    fi
    
    # Step 1: Check if Docker is installed and perform cleanup
    print_status "Step 1: Checking Docker installation and performing cleanup..."
    if [ "$docker_installed" = true ]; then
        print_success "Docker is installed, proceeding with comprehensive cleanup"
        
        # Stop all containers
        if execute_command "sudo docker stop \$(sudo docker ps -aq) 2>/dev/null || true" "Stop all containers"; then
            print_success "All containers stopped"
        fi
        
        # Remove all containers
        if execute_command "sudo docker rm \$(sudo docker ps -aq) 2>/dev/null || true" "Remove all containers"; then
            print_success "All containers removed"
        fi
        
        # Remove all images
        if execute_command "sudo docker rmi \$(sudo docker images -q) 2>/dev/null || true" "Remove all images"; then
            print_success "All Docker images removed"
        fi
        
        # Remove all volumes
        if execute_command "sudo docker volume rm \$(sudo docker volume ls -q) 2>/dev/null || true" "Remove all volumes"; then
            print_success "All Docker volumes removed"
        fi
        
        # Remove custom networks (except default)
        if execute_command "sudo docker network rm \$(sudo docker network ls -q --filter type=custom) 2>/dev/null || true" "Remove custom networks"; then
            print_success "Custom Docker networks removed"
        fi
    else
        print_warning "Docker is not installed, skipping Docker cleanup"
    fi
    
    # Step 2: Stop and remove all services
    print_status "Step 2: Stopping and removing all services..."
    
    # Stop all systemd services that might be running
    services_to_stop=("docker" "nodered" "portainer" "restreamer" "tailscale" "nginx" "apache2" "mysql" "postgresql" "redis" "mongodb")
    
    for service in "${services_to_stop[@]}"; do
        print_status "Checking service: $service"
        if execute_command "systemctl is-active $service >/dev/null 2>&1" "Check if $service is active"; then
            print_status "Stopping service: $service"
            if execute_command "sudo systemctl stop $service" "Stop $service"; then
                print_success "Service $service stopped"
            else
                print_warning "Failed to stop service $service"
            fi
            
            if execute_command "sudo systemctl disable $service" "Disable $service"; then
                print_success "Service $service disabled"
            else
                print_warning "Failed to disable service $service"
            fi
        else
            print_status "Service $service is not active, skipping"
        fi
    done
    
    # Special handling for Docker - also stop and disable the socket
    if [ "$docker_installed" = true ]; then
        print_status "Stopping and disabling Docker socket..."
        if execute_command "sudo systemctl stop docker.socket" "Stop Docker socket"; then
            print_success "Docker socket stopped"
        fi
        
        if execute_command "sudo systemctl disable docker.socket" "Disable Docker socket"; then
            print_success "Docker socket disabled"
        fi
        
        # Also stop containerd if it's running
        if execute_command "sudo systemctl stop containerd" "Stop containerd"; then
            print_success "Containerd stopped"
        fi
        
        if execute_command "sudo systemctl disable containerd" "Disable containerd"; then
            print_success "Containerd disabled"
        fi
    fi
    
    # Stop any remaining Docker containers that might be running
    print_status "Ensuring all Docker containers are stopped..."
    if [ "$docker_installed" = true ]; then
        if execute_command "sudo docker ps -q" "Check for running containers"; then
            running_containers=$(execute_command "sudo docker ps -q" "Get running container IDs")
            if [ -n "$running_containers" ]; then
                print_status "Force stopping remaining containers..."
                if execute_command "sudo docker stop $running_containers" "Force stop containers"; then
                    print_success "All remaining containers stopped"
                fi
            fi
        fi
    fi
    
    print_success "All services stopped and disabled"
    
    # Step 3: Remove Docker data directories
    print_status "Step 3: Removing Docker data directories..."
    if execute_command "sudo rm -rf /data/nodered /data/portainer /data/restreamer /data/tailscale 2>/dev/null || true" "Remove data directories"; then
        print_success "Docker data directories removed"
    fi
    
    # Step 4: Remove user from docker group
    print_status "Step 4: Removing user from docker group..."
    if execute_command "sudo deluser admin docker 2>/dev/null || true" "Remove admin from docker group"; then
        print_success "Admin removed from docker group"
    fi
    
    # Step 5: Uninstall Docker packages (if Docker was installed)
    if [ "$docker_installed" = true ]; then
        print_status "Step 5: Uninstalling Docker packages..."
        
        # Stop all Docker services first
        print_status "Ensuring all Docker services are stopped before uninstallation..."
        execute_command "sudo systemctl stop docker.service docker.socket containerd 2>/dev/null || true" "Stop all Docker services"
        
        # Try to remove Docker CE packages first
        if execute_command "sudo apt remove -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin 2>/dev/null || true" "Uninstall Docker CE packages"; then
            print_success "Docker CE packages uninstalled"
        fi
        
        # Try to remove Ubuntu Docker.io package
        if execute_command "sudo apt remove -y docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc 2>/dev/null || true" "Uninstall Docker.io packages"; then
            print_success "Docker.io packages uninstalled"
        fi
        
        # Remove any remaining Docker-related packages
        if execute_command "sudo apt remove -y docker-ce-rootless-extras 2>/dev/null || true" "Remove Docker rootless extras"; then
            print_success "Docker rootless extras removed"
        fi
        
        if execute_command "sudo apt autoremove -y 2>/dev/null || true" "Remove unused packages"; then
            print_success "Unused packages removed"
        fi
        
        # Purge Docker packages to remove configuration files
        if execute_command "sudo apt purge -y docker.io docker-ce docker-ce-cli containerd.io 2>/dev/null || true" "Purge Docker packages"; then
            print_success "Docker packages purged"
        fi
        
        # Final cleanup
        if execute_command "sudo apt autoremove -y && sudo apt autoclean 2>/dev/null || true" "Final package cleanup"; then
            print_success "Final package cleanup completed"
        fi
    else
        print_status "Step 5: Skipping Docker uninstallation (Docker was not installed)"
    fi
    
    # Step 6: Configure network to REVERSE mode (LTE WAN)
    print_status "Step 6: Configuring network to REVERSE mode (LTE WAN)..."
    print_warning "IMPORTANT: This will configure the device to use LTE WAN while keeping LAN accessible"
    configure_network_settings_reverse
    
    # Verify network is still accessible after configuration
    print_status "Verifying network accessibility after configuration..."
    if [ "$USE_SSH" = true ] && [ -n "$REMOTE_HOST" ]; then
        if ping_remote_host; then
            print_success "Device remains accessible after network configuration"
        else
            print_warning "Device may have lost connectivity - this is normal for network changes"
            print_warning "Please wait for network services to restart before attempting to reconnect"
        fi
    fi
    
    # Step 7: Reset password to admin/admin
    print_status "Step 7: Resetting password to admin/admin..."
    configure_password_admin
    
    # Step 8: Clean up any remaining Docker files (if Docker was installed)
    if [ "$docker_installed" = true ]; then
        print_status "Step 8: Cleaning up remaining Docker files..."
        
        # Remove Docker data directories
        if execute_command "sudo rm -rf /var/lib/docker 2>/dev/null || true" "Remove Docker lib directory"; then
            print_success "Docker lib directory removed"
        fi
        
        if execute_command "sudo rm -rf /etc/docker 2>/dev/null || true" "Remove Docker config directory"; then
            print_success "Docker config directory removed"
        fi
        
        # Remove Docker socket and other runtime files
        if execute_command "sudo rm -rf /var/run/docker* 2>/dev/null || true" "Remove Docker runtime files"; then
            print_success "Docker runtime files removed"
        fi
        
        # Remove Docker systemd service files
        if execute_command "sudo rm -f /lib/systemd/system/docker* 2>/dev/null || true" "Remove Docker systemd files"; then
            print_success "Docker systemd files removed"
        fi
        
        # Remove Docker binaries
        if execute_command "sudo rm -f /usr/bin/docker* /usr/local/bin/docker* 2>/dev/null || true" "Remove Docker binaries"; then
            print_success "Docker binaries removed"
        fi
        
        # Reload systemd to reflect removed services
        if execute_command "sudo systemctl daemon-reload" "Reload systemd daemon"; then
            print_success "Systemd daemon reloaded"
        fi
    else
        print_status "Step 8: Skipping Docker file cleanup (Docker was not installed)"
    fi
    
    # Step 9: Final network service restart (after all cleanup)
    print_status "Step 9: Final network service restart (after all cleanup)..."
    
    # Use the same method as web interface Save & Apply
    if execute_command "sudo luci-reload network" "Final LuCI network reload (web interface method)"; then
        print_success "Final LuCI network reload completed (web interface method)"
    elif execute_command "sudo /usr/sbin/network_config" "Final OpenWrt native network config"; then
        print_success "Final OpenWrt native network config completed"
    elif execute_command "sudo /etc/init.d/network restart" "Final network service restart (fallback)"; then
        print_success "Final network service restart completed (fallback)"
    fi
    
    print_success "Device reset completed successfully!"
    print_warning "Device has been reset to default state:"
    print_warning "- All Docker containers, images, and volumes removed"
    print_warning "- Docker service completely uninstalled and removed"
    print_warning "- All services stopped and disabled"
    print_warning "- Network configured to REVERSE mode (LTE WAN)"
    print_warning "- Password reset to admin/admin"
    print_warning "- IP address reset to 192.168.1.1"
    print_warning "- All custom configurations removed"
    print_warning ""
    print_warning "IMPORTANT: Device should remain accessible at 192.168.1.1"
    print_warning "If you cannot connect, wait 2-3 minutes for network services to fully restart"
}

# Function to show help
show_help() {
    echo "Network Configuration Script"
    echo
    echo "Usage: $0 [OPTIONS] [COMMAND]"
    echo
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  --remote HOST [USER] [PASS|SSH_KEY]  Execute commands on remote host via SSH"
    echo "                        If 4th parameter is a file path, it's treated as SSH key"
    echo "                        Otherwise, it's treated as password"
    echo
    echo "Commands:"
    echo "  forward             Configure network FORWARD (WAN=eth1 DHCP, LAN=eth0 static)"
    echo "  reverse [LAN_IP]    Configure network REVERSE (WAN=enx0250f4000000 LTE, LAN=eth0 static with optional custom IP)"
    echo "  set-password-admin  Change password back to admin"
    echo "  set-password PASSWORD  Change password to custom value"
    echo "  install-docker      Install Docker container engine (requires network FORWARD first)"
    echo "  forward-and-docker  Configure network FORWARD and install Docker"
    echo "  add-user-to-docker  Add user to docker group"
    echo "  install-nodered     Install Node-RED with Docker Compose (hardware privileges)"
    echo "  install-portainer   Install Portainer with Docker Compose"
    echo "  install-restreamer  Install Restreamer with Docker Compose (hardware privileges)"
    echo "  install-services    Install all Docker services (Node-RED, Portainer, Restreamer)"
    echo "  install-nodered-nodes [SOURCE] Install Node-RED nodes from package.json (auto|local|github|uploaded)"
    echo "  import-nodered-flows [SOURCE] Import Node-RED flows (auto|local|github|uploaded)"
    echo "  update-nodered-auth [PASSWORD] Update Node-RED authentication with custom password"
    echo "  install-tailscale [AUTH_KEY] Install Tailscale VPN router in Docker (optional custom auth key)"
    echo "  tailscale-down      Stop Tailscale VPN router container"
    echo "  tailscale-up [AUTH_KEY] Start Tailscale VPN router with optional new auth key"
    echo "  tailscale-restart [AUTH_KEY] Restart Tailscale VPN router with optional new auth key"
    echo "  install-curl        Install curl package"
    echo "  check-dns           Check internet connectivity and DNS"
    echo "  fix-dns             Fix DNS configuration by adding Google DNS (8.8.8.8)"
    echo "  verify-network      Verify current network configuration"
    echo "  cleanup-disk        Perform aggressive disk cleanup to free space"
    echo "  reset-device        Reset device to default state (remove all Docker, reset network, restore defaults)"
    echo
    echo "Examples:"
    echo "  $0 forward                    # Configure network locally"
    echo "  $0 --remote 192.168.1.1 admin admin forward  # Configure network remotely"
    echo "  $0 reverse                    # Configure network REVERSE locally (default 192.168.1.1)"
    echo "  $0 reverse 192.168.100.1      # Configure network REVERSE with custom LAN IP"
    echo "  $0 set-password-admin         # Change password to admin locally"
    echo "  $0 set-password mypass        # Change password to custom value locally"
    echo "  $0 forward-and-docker         # Configure network and install Docker locally"
    echo "  $0 add-user-to-docker         # Add user to docker group locally"
    echo "  $0 install-services           # Install all Docker services locally"
    echo "  $0 install-nodered-nodes      # Install Node-RED nodes (auto-detect package.json)"
    echo "  $0 install-nodered-nodes local # Install Node-RED nodes from local package.json"
    echo "  $0 install-nodered-nodes github # Install Node-RED nodes from GitHub package.json"
    echo "  $0 --uploaded-package file.json install-nodered-nodes uploaded # Install from uploaded package"
    echo "  $0 import-nodered-flows       # Import Node-RED flows (auto-detect source)"
    echo "  $0 import-nodered-flows local # Import Node-RED flows from local files"
    echo "  $0 import-nodered-flows github # Import Node-RED flows from GitHub"
    echo "  $0 --uploaded-flows file.json import-nodered-flows uploaded # Import from uploaded file"
    echo "  $0 update-nodered-auth mypass # Update Node-RED password locally"
    echo "  $0 install-tailscale          # Install Tailscale VPN router locally (default auth key)"
    echo "  $0 install-tailscale tskey-auth-xxx  # Install Tailscale with custom auth key"
    echo "  $0 tailscale-down             # Stop Tailscale VPN router locally"
    echo "  $0 tailscale-up               # Start Tailscale VPN router locally (current auth key)"
    echo "  $0 tailscale-up tskey-auth-xxx  # Start Tailscale with new auth key"
    echo "  $0 tailscale-restart          # Restart Tailscale VPN router locally (current auth key)"
    echo "  $0 tailscale-restart tskey-auth-xxx  # Restart Tailscale with new auth key"
    echo "  $0 install-curl               # Install curl locally"
    echo "  $0 check-dns                  # Check DNS locally"
    echo "  $0 reset-device               # Reset device to default state locally"
    echo "  $0 --remote 192.168.1.1 admin admin reset-device  # Reset device remotely"
}

# Main function
main() {
    local command=""
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            --remote)
                if [ -n "$2" ]; then
                    USE_SSH=true
                    REMOTE_HOST="$2"
                    shift 2  # Shift --remote and HOST
                    
                    # Check for USER argument
                    if [ -n "$1" ] && [[ "$1" != -* ]]; then
                        REMOTE_USER="$1"
                        shift 1
                        
                        # Check for PASSWORD argument
                        if [ -n "$1" ] && [[ "$1" != -* ]]; then
                            REMOTE_PASSWORD="$1"
                            shift 1
                        fi
                    fi
                    
                    print_success "Remote deployment mode enabled for $REMOTE_HOST"
                else
                    print_error "Remote host required"
                    exit 1
                fi
                ;;
            --final-ip)
                if [ -n "$2" ]; then
                    CUSTOM_LAN_IP="$2"
                    shift 2
                else
                    print_error "Final IP required"
                    exit 1
                fi
                ;;
            --final-password)
                if [ -n "$2" ]; then
                    NODERED_PASSWORD="$2"
                    shift 2
                else
                    print_error "Final password required"
                    exit 1
                fi
                ;;
            --flows-source)
                if [ -n "$2" ]; then
                    FLOWS_SOURCE="$2"
                    shift 2
                else
                    print_error "Flows source required"
                    exit 1
                fi
                ;;
            --package-source)
                if [ -n "$2" ]; then
                    PACKAGE_SOURCE="$2"
                    shift 2
                else
                    print_error "Package source required"
                    exit 1
                fi
                ;;
            --uploaded-flows)
                if [ -n "$2" ]; then
                    UPLOADED_FLOWS_FILE="$2"
                    shift 2
                else
                    print_error "Uploaded flows file required"
                    exit 1
                fi
                ;;
            --uploaded-package)
                if [ -n "$2" ]; then
                    UPLOADED_PACKAGE_FILE="$2"
                    shift 2
                else
                    print_error "Uploaded package file required"
                    exit 1
                fi
                ;;
            forward)
                command="forward"
                shift
                ;;
            reverse)
                command="reverse"
                # Check if next argument is a custom LAN IP
                if [[ $# -gt 0 && $2 =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
                    CUSTOM_LAN_IP="$2"
                    shift 2
                else
                    shift
                fi
                ;;
            install-curl)
                command="install-curl"
                shift
                ;;
            install-docker)
                command="install-docker"
                shift
                ;;
            forward-and-docker)
                command="forward-and-docker"
                shift
                ;;
            add-user-to-docker)
                command="add-user-to-docker"
                shift
                ;;
            install-nodered)
                command="install-nodered"
                shift
                ;;
            install-portainer)
                command="install-portainer"
                shift
                ;;
            install-restreamer)
                command="install-restreamer"
                shift
                ;;
            install-services)
                command="install-services"
                shift
                ;;
            install-nodered-nodes)
                command="install-nodered-nodes"
                # Check if flows source is provided as next argument
                if [[ $# -gt 0 && $2 =~ ^(auto|local|github|uploaded)$ ]]; then
                    FLOWS_SOURCE="$2"
                    shift 2
                else
                    shift
                fi
                ;;
            import-nodered-flows)
                command="import-nodered-flows"
                # Check if flows source is provided as next argument
                if [[ $# -gt 0 && $2 =~ ^(auto|local|github|uploaded)$ ]]; then
                    FLOWS_SOURCE="$2"
                    shift 2
                else
                    shift
                fi
                ;;
            update-nodered-auth)
                command="update-nodered-auth"
                # Check if password is provided as next argument
                if [ -n "$2" ] && [[ "$2" != -* ]]; then
                    NODERED_PASSWORD="$2"
                    shift 2
                else
                    shift
                fi
                ;;
            install-tailscale)
                command="install-tailscale"
                # Check if auth key is provided as next argument
                if [ -n "$2" ] && [[ "$2" != -* ]]; then
                    TAILSCALE_AUTH_KEY="$2"
                    shift 2
                else
                    shift
                fi
                ;;
            tailscale-down)
                command="tailscale-down"
                shift
                ;;
            tailscale-up)
                command="tailscale-up"
                # Check if auth key is provided as next argument
                if [ -n "$2" ] && [[ "$2" != -* ]]; then
                    TAILSCALE_AUTH_KEY="$2"
                    shift 2
                else
                    shift
                fi
                ;;
            tailscale-restart)
                command="tailscale-restart"
                # Check if auth key is provided as next argument
                if [ -n "$2" ] && [[ "$2" != -* ]]; then
                    TAILSCALE_AUTH_KEY="$2"
                    shift 2
                else
                    shift
                fi
                ;;
            check-dns)
                command="check-dns"
                shift
                ;;
            fix-dns)
                command="fix-dns"
                shift
                ;;
            verify-network)
                command="verify-network"
                shift
                ;;
            cleanup-disk)
                command="cleanup-disk"
                shift
                ;;
            set-password-admin)
                command="set-password-admin"
                shift
                ;;
            set-password)
                command="set-password"
                shift  # Move past 'set-password'
                CUSTOM_PASSWORD="$1"  # Now $1 is the password
                if [ -z "$CUSTOM_PASSWORD" ]; then
                    print_error "set-password requires a password argument"
                    show_help
                    exit 1
                fi
                shift  # Move past the password
                ;;
            reset-device)
                command="reset-device"
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Execute command
    case $command in
        forward)
            print_status "Starting FORWARD network configuration..."
            configure_network_settings_forward
            ;;
        reverse)
            print_status "Starting REVERSE network configuration..."
            configure_network_settings_reverse
            ;;
        install-curl)
            print_status "Installing curl..."
            install_curl
            ;;
        install-docker)
            print_status "Installing Docker..."
            install_docker
            ;;
        forward-and-docker)
            print_status "Starting FORWARD network configuration and Docker installation..."
            configure_network_settings_forward
            print_status "Waiting 10 seconds for network to stabilize..."
            sleep 10
            print_status "Checking internet connectivity before Docker installation..."
            check_internet_dns
            print_status "Installing Docker..."
            install_docker
            ;;
        add-user-to-docker)
            print_status "Adding user to docker group..."
            add_user_to_docker_group
            ;;
        install-nodered)
            print_status "Installing Node-RED with Docker Compose..."
            install_nodered_docker
            ;;
        install-portainer)
            print_status "Installing Portainer with Docker Compose..."
            install_portainer_docker
            ;;
        install-restreamer)
            print_status "Installing Restreamer with Docker Compose..."
            install_restreamer_docker
            ;;
        install-services)
            print_status "Installing all Docker services..."
            install_docker_services
            ;;
        install-nodered-nodes)
            print_status "Installing Node-RED nodes..."
            install_nodered_nodes
            ;;
        import-nodered-flows)
            print_status "Importing Node-RED flows..."
            import_nodered_flows
            ;;
        update-nodered-auth)
            print_status "Updating Node-RED authentication..."
            update_nodered_auth "$NODERED_PASSWORD"
            ;;
        install-tailscale)
            print_status "Installing Tailscale VPN router..."
            install_tailscale_docker "$TAILSCALE_AUTH_KEY"
            ;;
        tailscale-down)
            print_status "Stopping Tailscale VPN router..."
            tailscale_down
            ;;
        tailscale-up)
            print_status "Starting Tailscale VPN router..."
            tailscale_up "$TAILSCALE_AUTH_KEY"
            ;;
        tailscale-restart)
            print_status "Restarting Tailscale VPN router..."
            tailscale_restart "$TAILSCALE_AUTH_KEY"
            ;;
        check-dns)
            print_status "Checking internet and DNS..."
            check_internet_dns
            ;;
        fix-dns)
            print_status "Fixing DNS configuration..."
            fix_dns_configuration
            ;;
        verify-network)
            print_status "Verifying network configuration..."
            # Auto-detect mode based on current configuration
            local current_wan_proto=$(execute_command "sudo uci get network.wan.proto 2>/dev/null || echo 'not_set'" "Get current WAN protocol" | tail -1)
            local current_wan_ifname=$(execute_command "sudo uci get network.wan.ifname 2>/dev/null || echo 'not_set'" "Get current WAN interface" | tail -1)
            
            if [ "$current_wan_proto" = "lte" ] && ([ "$current_wan_ifname" = "enx0250f4000000" ] || [ "$current_wan_ifname" = "usb0" ]); then
                verify_network_config "REVERSE"
            elif [ "$current_wan_proto" = "dhcp" ] && [ "$current_wan_ifname" = "eth1" ]; then
                verify_network_config "FORWARD"
            else
                print_warning "Unknown network configuration detected - showing current state"
                # Show current configuration without mode-specific validation
                local current_lan_proto=$(execute_command "sudo uci get network.lan.proto 2>/dev/null || echo 'not_set'" "Get current LAN protocol")
                local current_lan_ifname=$(execute_command "sudo uci get network.lan.ifname 2>/dev/null || echo 'not_set'" "Get current LAN interface")
                local current_lan_ip=$(execute_command "sudo uci get network.lan.ipaddr 2>/dev/null || echo 'not_set'" "Get current LAN IP")
                
                print_status "Current UCI Configuration:"
                print_status "  WAN: $current_wan_ifname ($current_wan_proto)"
                print_status "  LAN: $current_lan_ifname ($current_lan_proto, $current_lan_ip)"
                
                print_status "Interface Status:"
                execute_command "ip addr show | grep -E '(eth0|eth1|enx0250f4000000|usb0|br-lan):' -A 2" "Show interface status"
                
                print_status "Routing Table:"
                execute_command "ip route" "Show routing table"
            fi
            ;;
        cleanup-disk)
            print_status "Performing aggressive disk cleanup..."
            aggressive_disk_cleanup
            ;;
        set-password-admin)
            print_status "Changing password to admin..."
            configure_password_admin
            ;;
        set-password)
            print_status "Changing password to custom value..."
            configure_password_custom "$CUSTOM_PASSWORD"
            ;;
        reset-device)
            print_status "Resetting device to default state..."
            reset_device
            ;;
        "")
            print_error "No command specified"
            show_help
            exit 1
            ;;
    esac
    
    print_success "Operation completed successfully!"
}

# Check for SSH mode and run main function
check_ssh_mode "$@"
main "$@"
