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
    
    if [ "$USE_SSH" = true ] && [ -n "$REMOTE_HOST" ]; then
        print_status "Executing on $REMOTE_HOST: $description"
        if [ -n "$REMOTE_SSH_KEY" ]; then
            ssh -i "$REMOTE_SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "$cmd"
        else
            sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "$cmd"
        fi
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
            REMOTE_PASSWORD="$4"
        fi
        print_success "Remote deployment mode enabled for $REMOTE_HOST"
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
    
    # Change password back to admin (REVERSE specific)
    print_status "Changing password back to admin (REVERSE mode)..."
    configure_password_admin
    
    # Apply WAN configuration
    print_status "Applying WAN configuration with enhanced process..."
    apply_wan_config
    
    # Wait for configuration to settle
    print_status "Waiting 5 seconds for configuration to settle..."
    sleep 5
    
    print_success "Network configuration REVERSE completed (NO REBOOT)"
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
    
    # Run network configuration
    print_status "Running network configuration..."
    if execute_command "sudo /etc/init.d/network restart" "Network restart"; then
        print_success "Network config successful"
    else
        print_error "Network config failed"
        return 1
    fi
    
    # Skip luci-reload if network restart was successful
    print_status "Skipping luci-reload - network restart already completed successfully"
    
    # Clean up routes again
    cleanup_empty_routes
    
    print_success "WAN configuration applied successfully"
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
    print_status "Configuring password back to admin..."
    
    # Set password using UCI
    password_commands=(
        "sudo uci set system.@system[0].password='admin'"
        "sudo uci commit system"
    )
    
    for cmd in "${password_commands[@]}"; do
        print_status "Executing: $cmd"
        if execute_command "$cmd" "Password configuration"; then
            print_success "Command successful: $cmd"
        else
            print_warning "Command failed: $cmd"
        fi
    done
    
    # Alternative method using passwd command
    print_status "Setting password using passwd command..."
    if execute_command "echo -e 'admin\nadmin' | sudo passwd admin" "Set password via passwd"; then
        print_success "Password set to admin via passwd command"
    else
        print_warning "Password setting via passwd failed, UCI method should work"
    fi
    
    print_success "Password configuration completed"
}

# Function to configure custom password
configure_password_custom() {
    local new_password="$1"
    
    if [ -z "$new_password" ]; then
        print_error "No password provided for custom password configuration"
        return 1
    fi
    
    print_status "Configuring password to: $new_password"
    
    # Set password using UCI
    password_commands=(
        "sudo uci set system.@system[0].password='$new_password'"
        "sudo uci commit system"
    )
    
    for cmd in "${password_commands[@]}"; do
        print_status "Executing: $cmd"
        if execute_command "$cmd" "Password configuration"; then
            print_success "Command successful: $cmd"
        else
            print_warning "Command failed: $cmd"
        fi
    done
    
    # Alternative method using passwd command
    print_status "Setting password using passwd command..."
    if execute_command "echo -e '$new_password\n$new_password' | sudo passwd admin" "Set password via passwd"; then
        print_success "Password set to $new_password via passwd command"
    else
        print_warning "Password setting via passwd failed, UCI method should work"
    fi
    
    print_success "Custom password configuration completed"
}

# =============================================================================
# USER MANAGEMENT FUNCTIONS
# =============================================================================

# Function to add user to docker group
add_user_to_docker_group() {
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
}

# =============================================================================
# SYSTEM UTILITY FUNCTIONS
# =============================================================================

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
    if execute_command "sudo apt-get clean" "Clean apt cache"; then
        print_success "Package cache cleaned"
    fi
    
    if execute_command "sudo apt-get autoremove -y" "Remove unused packages"; then
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
    if execute_command "sudo apt-get autoremove --purge -y" "Remove old kernels"; then
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
    
    print_status "curl not found, installing..."
    
    # Try different package managers
    if execute_command "opkg update && opkg install curl" "Install curl via opkg"; then
        print_success "curl installed via opkg"
    elif execute_command "echo 'debconf debconf/frontend select Noninteractive' | sudo debconf-set-selections && apt update && DEBIAN_FRONTEND=noninteractive apt install -y curl" "Install curl via apt"; then
        print_success "curl installed via apt"
    elif execute_command "yum install -y curl" "Install curl via yum"; then
        print_success "curl installed via yum"
    else
        print_error "Failed to install curl"
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
    print_status "Fixing DNS configuration..."
    
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
FallbackDNS=1.1.1.1 1.0.0.1'
        
        if execute_command "echo '$resolved_config' | sudo tee /etc/systemd/resolved.conf.d/dns_servers.conf" "Create systemd resolved config"; then
            print_success "systemd-resolved configuration created"
        fi
        
        # Restart systemd-resolved
        print_status "Restarting systemd-resolved service..."
        if execute_command "sudo systemctl restart systemd-resolved" "Restart systemd-resolved"; then
            print_success "systemd-resolved restarted"
        fi
        
        # Wait for service to be ready
        sleep 3
        
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
    
    # Test DNS resolution with multiple methods
    print_status "Testing DNS resolution with new configuration..."
    
    # Try dig first
    if execute_command "dig google.com +short" "Test DNS with dig"; then
        print_success "DNS resolution working with dig"
    # Try host command
    elif execute_command "host google.com" "Test DNS with host"; then
        print_success "DNS resolution working with host"
    # Try nslookup
    elif execute_command "nslookup google.com" "Test DNS with nslookup"; then
        print_success "DNS resolution working with nslookup"
    # Try ping as last resort
    elif execute_command "ping -c 1 google.com" "Test DNS with ping"; then
        print_success "DNS resolution working with ping"
    else
        print_warning "DNS resolution test failed, but configuration may still work"
    fi
    
    print_success "DNS configuration fixed"
}

# Function to check internet connectivity and DNS
check_internet_dns() {
    print_status "Checking internet connectivity and DNS..."
    
    # Test DNS resolution
    print_status "Testing DNS resolution..."
    if execute_command "nslookup google.com" "DNS resolution test"; then
        print_success "DNS resolution working"
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
    
    # Check if Docker is already installed
    if execute_command "docker --version" "Check if Docker is installed"; then
        print_success "Docker is already installed"
        return 0
    fi
    
    # Ensure sufficient disk space before installation
    if ! ensure_sufficient_disk_space; then
        print_error "Cannot install Docker: insufficient disk space"
        return 1
    fi
    
    print_status "Docker not found, installing..."
    
    # Check if apt is available (Debian/Ubuntu system)
    if execute_command "which apt" "Check if Debian/Ubuntu system"; then
        print_status "Detected Debian/Ubuntu system, installing Docker via apt..."
        
        # Set non-interactive environment for debconf
        print_status "Setting non-interactive environment for package installation..."
        if execute_command "export DEBIAN_FRONTEND=noninteractive && export DEBIAN_PRIORITY=critical" "Set non-interactive frontend"; then
            print_success "Non-interactive environment set"
        fi
        
        # Configure debconf to be non-interactive
        if execute_command "echo 'debconf debconf/frontend select Noninteractive' | sudo debconf-set-selections" "Configure debconf non-interactive"; then
            print_success "debconf configured for non-interactive mode"
        fi
        
        # Update package list
        if execute_command "sudo DEBIAN_FRONTEND=noninteractive apt update" "Update package list"; then
            print_success "Package list updated"
        else
            print_warning "Failed to update package list"
        fi
        
        # Try to install Docker from default repositories first
        print_status "Trying to install Docker from default repositories..."
        if execute_command "sudo DEBIAN_FRONTEND=noninteractive apt install -y docker.io" "Install Docker from default repo"; then
            print_success "Docker installed from default repository"
        else
            print_warning "Docker not available in default repositories, trying official Docker repository..."
            
            # Install required packages for official Docker repo
            if execute_command "sudo DEBIAN_FRONTEND=noninteractive apt install -y apt-transport-https ca-certificates curl gnupg lsb-release" "Install Docker dependencies"; then
                print_success "Docker dependencies installed"
            else
                print_warning "Failed to install some dependencies"
            fi
            
            # Add Docker's official GPG key (non-interactive)
            if execute_command "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --batch --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg" "Add Docker GPG key"; then
                print_success "Docker GPG key added"
            else
                print_warning "Failed to add Docker GPG key"
            fi
            
            # Add Docker repository
            if execute_command "echo \"deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \$(lsb_release -cs) stable\" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null" "Add Docker repository"; then
                print_success "Docker repository added"
            else
                print_warning "Failed to add Docker repository"
            fi
            
            # Update package list again
            if execute_command "sudo DEBIAN_FRONTEND=noninteractive apt update" "Update package list with Docker repo"; then
                print_success "Package list updated with Docker repository"
            else
                print_warning "Failed to update package list with Docker repository"
            fi
            
            # Install Docker CE
            if execute_command "sudo DEBIAN_FRONTEND=noninteractive apt install -y docker-ce docker-ce-cli containerd.io" "Install Docker CE"; then
                print_success "Docker CE installed"
            else
                print_error "Failed to install Docker CE"
                return 1
            fi
        fi
        
    else
        print_error "apt package manager not found. This script only supports Debian/Ubuntu systems for Docker installation."
        return 1
    fi
    
    # Start and enable Docker service
    print_status "Starting Docker service..."
    if execute_command "sudo systemctl start docker" "Start Docker service"; then
        print_success "Docker service started"
    else
        print_warning "Failed to start Docker service (may not be systemd-based)"
    fi
    
    if execute_command "sudo systemctl enable docker" "Enable Docker service"; then
        print_success "Docker service enabled"
    else
        print_warning "Failed to enable Docker service (may not be systemd-based)"
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
    
    # Verify installation
    print_status "Verifying Docker installation..."
    if execute_command "docker --version" "Verify Docker installation"; then
        docker_version=$(execute_command "docker --version" "Get Docker version")
        print_success "Docker installation verified: $docker_version"
    else
        print_error "Docker installation verification failed"
        return 1
    fi
    
    # Test Docker with hello-world
    print_status "Testing Docker with hello-world container..."
    if execute_command "docker run --rm hello-world" "Test Docker with hello-world"; then
        print_success "Docker test successful"
    else
        print_warning "Docker test failed (may need internet connection or container registry access)"
    fi
    
    print_success "Docker installation completed successfully"
}

# Function to install Node-RED with Docker Compose
install_nodered_docker() {
    print_status "Installing Node-RED with Docker Compose..."
    
    # Check if Node-RED container is already running
    if execute_command "sudo docker ps | grep nodered" "Check if Node-RED is running"; then
        print_success "Node-RED container is already running, skipping installation"
        return 0
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
            execute_command "sudo apt-get clean" "Clean apt cache"
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
    local restreamer_env='# Restreamer Environment Configuration
RS_USERNAME=admin
RS_PASSWORD=L@ranet2025
RS_LOGLEVEL=info
RS_DEBUG=false'
    
    # Write environment file
    if execute_command "echo '$restreamer_env' | sudo tee /data/restreamer/.env > /dev/null" "Create Restreamer environment file"; then
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
    
    # Determine package.json source based on parameter or auto-detect
    local flows_source_type="${FLOWS_SOURCE:-auto}"
    local package_file=""
    local package_source=""
    
    if [ "$flows_source_type" = "github" ]; then
        # Force GitHub download
        print_status "Forcing GitHub download for package.json..."
        if download_package_from_github; then
            package_file="/tmp/package.json"
            package_source="GitHub download (forced)"
        else
            print_error "Failed to download package.json from GitHub"
            return 1
        fi
    elif [ "$flows_source_type" = "local" ]; then
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
                package_file="/tmp/package.json"
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
        
        # Copy package.json to the remote system (if not already downloaded)
        if [ "$package_source" != "GitHub download" ]; then
            print_status "Copying package.json to remote system..."
            if copy_to_remote "$package_file" "/tmp/package.json" "Copy package.json"; then
                print_success "package.json copied successfully"
            else
                print_error "Failed to copy package.json"
                return 1
            fi
        fi
        
        # Copy package.json to Node-RED container
        print_status "Copying package.json to Node-RED container..."
        if execute_command "sudo docker cp /tmp/package.json nodered:/data/package.json" "Copy package.json to container"; then
            print_success "package.json copied to Node-RED container"
        else
            print_error "Failed to copy package.json to Node-RED container"
            return 1
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
    local github_flows_url="https://raw.githubusercontent.com/Loranet-Technologies/bivicom-radar/main/nodered_flows/flows.json"
    local github_package_url="https://raw.githubusercontent.com/Loranet-Technologies/bivicom-radar/main/nodered_flows/package.json"
    
    # Check if curl is available
    if ! command -v curl >/dev/null 2>&1; then
        print_error "curl is not installed. Cannot download from GitHub."
        return 1
    fi
    
    # Download flows.json
    print_status "Downloading flows.json from GitHub..."
    if execute_command "curl -s -L -o /tmp/flows.json '$github_flows_url'" "Download flows.json"; then
        print_success "flows.json downloaded successfully"
    else
        print_error "Failed to download flows.json from GitHub"
        return 1
    fi
    
    # Verify the downloaded file
    if [ ! -f "/tmp/flows.json" ] || [ ! -s "/tmp/flows.json" ]; then
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
    local github_package_url="https://raw.githubusercontent.com/Loranet-Technologies/bivicom-radar/main/nodered_flows/package.json"
    
    # Check if curl is available
    if ! command -v curl >/dev/null 2>&1; then
        print_error "curl is not installed. Cannot download from GitHub."
        return 1
    fi
    
    # Download package.json
    print_status "Downloading package.json from GitHub..."
    if execute_command "curl -s -L -o /tmp/package.json '$github_package_url'" "Download package.json"; then
        print_success "package.json downloaded successfully"
    else
        print_error "Failed to download package.json from GitHub"
        return 1
    fi
    
    # Verify the downloaded file
    if [ ! -f "/tmp/package.json" ] || [ ! -s "/tmp/package.json" ]; then
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
    
    # Determine flows source based on parameter or auto-detect
    local flows_source_type="${FLOWS_SOURCE:-auto}"
    local flows_file=""
    local flows_source=""
    
    if [ "$flows_source_type" = "github" ]; then
        # Force GitHub download
        print_status "Forcing GitHub download for flows..."
        if download_flows_from_github; then
            flows_file="/tmp/flows.json"
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
                flows_file="/tmp/flows.json"
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
    
    # Copy flows.json to the remote system (if not already downloaded)
    if [ "$flows_source" != "GitHub download" ]; then
        print_status "Copying flows.json to remote system..."
        if copy_to_remote "$flows_file" "/tmp/flows.json" "Copy flows file"; then
            print_success "Flows file copied successfully"
        else
            print_error "Failed to copy flows file"
            return 1
        fi
    fi
    
    # Stop Node-RED container to import flows
    print_status "Stopping Node-RED container for flow import..."
    if execute_command "sudo docker stop nodered" "Stop Node-RED container"; then
        print_success "Node-RED container stopped"
    else
        print_error "Failed to stop Node-RED container"
        return 1
    fi
    
    # Backup existing flows
    print_status "Backing up existing flows..."
    if execute_command "sudo docker cp nodered:/data/flows.json /tmp/flows_backup.json 2>/dev/null || echo 'No existing flows to backup'" "Backup existing flows"; then
        print_success "Existing flows backed up (if any)"
    else
        print_warning "Could not backup existing flows"
    fi
    
    # Copy new flows to container
    print_status "Importing new flows to Node-RED container..."
    if execute_command "sudo docker cp /tmp/flows.json nodered:/data/flows.json" "Import flows to container"; then
        print_success "Flows imported to Node-RED container"
    else
        print_error "Failed to import flows to container"
        return 1
    fi
    
    # Set proper permissions
    print_status "Setting proper permissions for flows file..."
    if execute_command "sudo docker exec nodered chown 1000:1000 /data/flows.json" "Set flows permissions"; then
        print_success "Flows permissions set"
    else
        print_warning "Could not set flows permissions"
    fi
    
    # Start Node-RED container
    print_status "Starting Node-RED container with new flows..."
    if execute_command "sudo docker start nodered" "Start Node-RED container"; then
        print_success "Node-RED container started"
    else
        print_error "Failed to start Node-RED container"
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
    
    # Clean up temporary files
    print_status "Cleaning up temporary files..."
    execute_command "rm -f /tmp/flows.json" "Clean up flows file"
    
    print_success "Node-RED flows import completed"
}

# Function to install Tailscale with Docker
install_tailscale_docker() {
    print_status "Installing Tailscale with Docker..."
    
    # Check if Tailscale container is already running
    if execute_command "sudo docker ps | grep tailscale" "Check if Tailscale is running"; then
        print_success "Tailscale container is already running, skipping installation"
        return 0
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
    local tailscale_env='# Tailscale Environment Configuration
TS_AUTHKEY=tskey-auth-kvwRxYc6o321CNTRL-6kggdogXnMdAdewR7Y7cMdNSp7yrJsSC
TS_STATE_DIR=/var/lib/tailscale
TS_USERSPACE=false
TS_ACCEPT_DNS=true'
    
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
    network_mode: host

networks:
  default:
    driver: bridge'
    
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

### Adding Route Advertisement

To advertise local network routes to other Tailscale devices, add these lines to your `.env` file:

```bash
# Add these lines to advertise local networks
TS_ROUTES=192.168.1.0/24,192.168.14.0/24
TS_EXTRA_ARGS=--advertise-routes=192.168.1.0/24,192.168.14.0/24
```

**Replace the network ranges with your actual local networks.**

## Management Commands

### Start Tailscale
```bash
cd /data/tailscale
sudo docker-compose up -d
```

### Stop Tailscale
```bash
cd /data/tailscale
sudo docker-compose down
```

### Restart Tailscale
```bash
cd /data/tailscale
sudo docker-compose restart
```

### Check Status
```bash
sudo docker exec tailscale tailscale status
```

### View Logs
```bash
sudo docker-compose logs -f tailscale
```

### Manual Route Advertisement
```bash
# Advertise specific routes manually
sudo docker exec tailscale tailscale up --advertise-routes=192.168.1.0/24,192.168.14.0/24

# Check advertised routes
sudo docker exec tailscale tailscale status
```

## Network Configuration

### Default Settings
- **DNS**: Accepts Tailscale DNS servers
- **User Space**: Disabled (kernel mode for better performance)
- **Network Mode**: Host networking for full network access

### Custom Networks
To advertise different networks, modify the `TS_ROUTES` and `TS_EXTRA_ARGS` in the `.env` file:

```bash
# Example: Advertise multiple networks
TS_ROUTES=192.168.1.0/24,192.168.14.0/24,10.0.0.0/8
TS_EXTRA_ARGS=--advertise-routes=192.168.1.0/24,192.168.14.0/24,10.0.0.0/8
```

## Troubleshooting

### Container Not Starting
1. Check if Docker is running: `sudo systemctl status docker`
2. Check logs: `sudo docker-compose logs tailscale`
3. Verify permissions: `ls -la /data/tailscale/`

### Routes Not Advertised
1. Verify routes in `.env` file
2. Check Tailscale status: `sudo docker exec tailscale tailscale status`
3. Restart container: `sudo docker-compose restart`

### Authentication Issues
1. Verify auth key in `.env` file
2. Check Tailscale admin console
3. Generate new auth key if needed

## Security Notes

- The auth key provides automatic authentication
- Routes are only advertised to authenticated Tailscale devices
- Use specific network ranges to limit exposure
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
    
    # Start Tailscale container using Docker Compose
    print_status "Starting Tailscale container with Docker Compose..."
    if execute_command "cd /data/tailscale && sudo docker-compose up -d" "Start Tailscale container"; then
        print_success "Tailscale container started with Docker Compose"
    else
        print_error "Failed to start Tailscale container"
        return 1
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
    print_info "Tailscale is now managed with Docker Compose in /data/tailscale/"
    print_info "Documentation: /data/tailscale/README.md"
    print_info "Note: Routes are not automatically advertised. Configure routes manually if needed:"
    print_info "  - Edit /data/tailscale/.env to add TS_ROUTES and TS_EXTRA_ARGS"
    print_info "  - Or use: docker exec tailscale tailscale up --advertise-routes=192.168.1.0/24"
    print_info "Management: cd /data/tailscale && sudo docker-compose [up|down|restart|logs]"
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
    
    # Step 1: Stop and remove all Docker containers (if Docker is installed)
    print_status "Step 1: Checking Docker installation and stopping containers..."
    if execute_command "which docker >/dev/null 2>&1" "Check if Docker is installed"; then
        print_success "Docker is installed, proceeding with container cleanup"
        
        if execute_command "sudo docker stop \$(sudo docker ps -aq) 2>/dev/null || true" "Stop all containers"; then
            print_success "All containers stopped"
        fi
        
        if execute_command "sudo docker rm \$(sudo docker ps -aq) 2>/dev/null || true" "Remove all containers"; then
            print_success "All containers removed"
        fi
    else
        print_warning "Docker is not installed, skipping container cleanup"
    fi
    
    # Step 2: Remove all Docker images (if Docker is installed)
    if execute_command "which docker >/dev/null 2>&1" "Check Docker for image cleanup"; then
        print_status "Step 2: Removing all Docker images..."
        if execute_command "sudo docker rmi \$(sudo docker images -q) 2>/dev/null || true" "Remove all images"; then
            print_success "All Docker images removed"
        fi
        
        # Step 3: Remove Docker volumes
        print_status "Step 3: Removing Docker volumes..."
        if execute_command "sudo docker volume rm \$(sudo docker volume ls -q) 2>/dev/null || true" "Remove all volumes"; then
            print_success "All Docker volumes removed"
        fi
        
        # Step 4: Remove Docker networks (except default)
        print_status "Step 4: Removing custom Docker networks..."
        if execute_command "sudo docker network rm \$(sudo docker network ls -q --filter type=custom) 2>/dev/null || true" "Remove custom networks"; then
            print_success "Custom Docker networks removed"
        fi
    else
        print_warning "Docker not installed, skipping image/volume/network cleanup"
    fi
    
    # Step 5: Remove Docker data directories
    print_status "Step 5: Removing Docker data directories..."
    if execute_command "sudo rm -rf /data/nodered /data/portainer /data/restreamer /data/tailscale 2>/dev/null || true" "Remove data directories"; then
        print_success "Docker data directories removed"
    fi
    
    # Step 6: Remove user from docker group
    print_status "Step 6: Removing user from docker group..."
    if execute_command "sudo deluser admin docker 2>/dev/null || true" "Remove admin from docker group"; then
        print_success "Admin removed from docker group"
    fi
    
    # Step 7: Uninstall Docker (if installed)
    print_status "Step 7: Checking and uninstalling Docker..."
    if execute_command "which docker >/dev/null 2>&1" "Check if Docker needs uninstalling"; then
        print_status "Docker is installed, proceeding with uninstallation..."
        if execute_command "sudo apt-get remove -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin 2>/dev/null || true" "Uninstall Docker packages"; then
            print_success "Docker packages uninstalled"
        fi
        
        if execute_command "sudo apt-get autoremove -y 2>/dev/null || true" "Remove unused packages"; then
            print_success "Unused packages removed"
        fi
    else
        print_warning "Docker is not installed, skipping uninstallation"
    fi
    
    # Step 8: Configure network to REVERSE mode (LTE WAN)
    print_status "Step 8: Configuring network to REVERSE mode (LTE WAN)..."
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
    
    # Step 9: Reset password to admin/admin
    print_status "Step 9: Resetting password to admin/admin..."
    configure_password_admin
    
    # Step 10: Clean up any remaining Docker files
    print_status "Step 10: Cleaning up remaining Docker files..."
    if execute_command "sudo rm -rf /var/lib/docker 2>/dev/null || true" "Remove Docker lib directory"; then
        print_success "Docker lib directory removed"
    fi
    
    if execute_command "sudo rm -rf /etc/docker 2>/dev/null || true" "Remove Docker config directory"; then
        print_success "Docker config directory removed"
    fi
    
    # Step 11: Commit UCI changes and ensure network is properly configured
    print_status "Step 11: Committing UCI changes and ensuring network stability..."
    if execute_command "sudo uci commit network" "Commit network configuration"; then
        print_success "Network configuration committed"
    fi
    
    # Verify network interfaces are properly configured
    if execute_command "sudo uci show network | grep -E 'network\.(wan|lan)\.' | head -10" "Verify network configuration"; then
        print_success "Network interfaces verified"
    fi
    
    # Step 12: Perform aggressive disk cleanup
    print_status "Step 12: Performing aggressive disk cleanup..."
    aggressive_disk_cleanup
    
    # Step 13: Restart network services
    print_status "Step 13: Restarting network services..."
    if execute_command "sudo /etc/init.d/network restart" "Restart network service"; then
        print_success "Network service restarted"
    fi
    
    print_success "Device reset completed successfully!"
    print_warning "Device has been reset to default state:"
    print_warning "- All Docker containers, images, and volumes removed"
    print_warning "- Network configured to REVERSE mode (LTE WAN)"
    print_warning "- Password reset to admin/admin"
    print_warning "- IP address reset to 192.168.1.1"
    print_warning "- All custom configurations removed"
    print_warning "- Aggressive disk cleanup performed (logs, cache, temp files)"
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
    echo "  --remote HOST [USER] [PASS]  Execute commands on remote host via SSH"
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
    echo "  install-nodered-nodes [SOURCE] Install Node-RED nodes from package.json (auto|local|github)"
    echo "  import-nodered-flows [SOURCE] Import Node-RED flows (auto|local|github)"
    echo "  update-nodered-auth [PASSWORD] Update Node-RED authentication with custom password"
    echo "  install-tailscale   Install Tailscale VPN router in Docker"
    echo "  install-curl        Install curl package"
    echo "  check-dns           Check internet connectivity and DNS"
    echo "  fix-dns             Fix DNS configuration by adding Google DNS (8.8.8.8)"
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
    echo "  $0 import-nodered-flows       # Import Node-RED flows (auto-detect source)"
    echo "  $0 import-nodered-flows local # Import Node-RED flows from local files"
    echo "  $0 import-nodered-flows github # Import Node-RED flows from GitHub"
    echo "  $0 update-nodered-auth mypass # Update Node-RED password locally"
    echo "  $0 install-tailscale          # Install Tailscale VPN router locally"
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
                if [[ $# -gt 0 && $2 =~ ^(auto|local|github)$ ]]; then
                    FLOWS_SOURCE="$2"
                    shift 2
                else
                    shift
                fi
                ;;
            import-nodered-flows)
                command="import-nodered-flows"
                # Check if flows source is provided as next argument
                if [[ $# -gt 0 && $2 =~ ^(auto|local|github)$ ]]; then
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
                shift
                ;;
            check-dns)
                command="check-dns"
                shift
                ;;
            fix-dns)
                command="fix-dns"
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
                CUSTOM_PASSWORD="$2"
                if [ -z "$CUSTOM_PASSWORD" ]; then
                    print_error "set-password requires a password argument"
                    show_help
                    exit 1
                fi
                shift 2
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
            install_tailscale_docker
            ;;
        check-dns)
            print_status "Checking internet and DNS..."
            check_internet_dns
            ;;
        fix-dns)
            print_status "Fixing DNS configuration..."
            fix_dns_configuration
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
