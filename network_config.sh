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
    
    # WAN Configuration (LTE on USB device) - REVERSE
    print_status "Configuring WAN interface (enx0250f4000000) for LTE..."
    wan_commands=(
        "sudo uci set network.wan.proto='lte'"
        "sudo uci set network.wan.ifname='enx0250f4000000'"
        "sudo uci set network.wan.mtu=1500"
    )
    
    # LAN Configuration (Static on eth0) - Keep same
    print_status "Configuring LAN interface (eth0) for static..."
    lan_commands=(
        "sudo uci set network.lan.proto='static'"
        "sudo uci set network.lan.ifname='eth0'"
        "sudo uci set network.lan.ipaddr='192.168.1.1'"
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
    elif execute_command "apt update && apt install -y curl" "Install curl via apt"; then
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

# Function to check internet connectivity and DNS
check_internet_dns() {
    print_status "Checking internet connectivity and DNS..."
    
    # Test DNS resolution
    print_status "Testing DNS resolution..."
    if execute_command "nslookup google.com" "DNS resolution test"; then
        print_success "DNS resolution working"
    else
        print_warning "DNS resolution failed"
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
    
    print_status "Docker not found, installing..."
    
    # Check if apt is available (Debian/Ubuntu system)
    if execute_command "which apt" "Check if Debian/Ubuntu system"; then
        print_status "Detected Debian/Ubuntu system, installing Docker via apt..."
        
        # Update package list
        if execute_command "sudo apt update" "Update package list"; then
            print_success "Package list updated"
        else
            print_warning "Failed to update package list"
        fi
        
        # Try to install Docker from default repositories first
        print_status "Trying to install Docker from default repositories..."
        if execute_command "sudo apt install -y docker.io" "Install Docker from default repo"; then
            print_success "Docker installed from default repository"
        else
            print_warning "Docker not available in default repositories, trying official Docker repository..."
            
            # Install required packages for official Docker repo
            if execute_command "sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release" "Install Docker dependencies"; then
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
            if execute_command "sudo apt update" "Update package list with Docker repo"; then
                print_success "Package list updated with Docker repository"
            else
                print_warning "Failed to update package list with Docker repository"
            fi
            
            # Install Docker CE
            if execute_command "sudo apt install -y docker-ce docker-ce-cli containerd.io" "Install Docker CE"; then
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
    
    # Define the nodes to install
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

# Function to import Node-RED flows
import_nodered_flows() {
    print_status "Importing Node-RED flows..."
    
    # Check if Node-RED container is running
    if ! execute_command "sudo docker ps | grep nodered" "Check if Node-RED is running"; then
        print_error "Node-RED container is not running. Please install Node-RED first."
        return 1
    fi
    
    # Check if flows.json file exists locally
    local flows_file="/Users/shamry/Projects/bivicom-radar/nodered_flows/nodered_flows_backup/flows.json"
    if [ ! -f "$flows_file" ]; then
        print_error "Flows file not found at: $flows_file"
        return 1
    fi
    
    print_status "Found flows file: $flows_file"
    
    # Copy flows.json to the remote system
    print_status "Copying flows.json to remote system..."
    if copy_to_remote "$flows_file" "/tmp/flows.json" "Copy flows file"; then
        print_success "Flows file copied successfully"
    else
        print_error "Failed to copy flows file"
        return 1
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
TS_ACCEPT_DNS=true
TS_ROUTES=192.168.1.0/24,192.168.14.0/24
TS_EXTRA_ARGS=--advertise-routes=192.168.1.0/24,192.168.14.0/24'
    
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
    
    # Start Tailscale container
    print_status "Starting Tailscale container with router configuration..."
    if execute_command "sudo docker run -d --name tailscale --restart unless-stopped --env-file /data/tailscale/.env --cap-add=NET_ADMIN --cap-add=SYS_MODULE --device=/dev/net/tun --volume /data/tailscale:/var/lib/tailscale --network host tailscale/tailscale:latest" "Start Tailscale container"; then
        print_success "Tailscale container started with router configuration"
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
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

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
    echo "  reverse             Configure network REVERSE (WAN=enx0250f4000000 LTE, LAN=eth0 static)"
    echo "  set-password-admin  Change password back to admin"
    echo "  install-docker      Install Docker container engine (requires network FORWARD first)"
    echo "  forward-and-docker  Configure network FORWARD and install Docker"
    echo "  add-user-to-docker  Add user to docker group"
    echo "  install-nodered     Install Node-RED with Docker Compose (hardware privileges)"
    echo "  install-portainer   Install Portainer with Docker Compose"
    echo "  install-restreamer  Install Restreamer with Docker Compose (hardware privileges)"
    echo "  install-services    Install all Docker services (Node-RED, Portainer, Restreamer)"
    echo "  install-nodered-nodes Install Node-RED nodes (ffmpeg, queue-gate, sqlite, serialport)"
    echo "  import-nodered-flows Import Node-RED flows from backup"
    echo "  install-tailscale   Install Tailscale VPN router in Docker"
    echo "  install-curl        Install curl package"
    echo "  check-dns           Check internet connectivity and DNS"
    echo
    echo "Examples:"
    echo "  $0 forward                    # Configure network locally"
    echo "  $0 --remote 192.168.1.1 admin admin forward  # Configure network remotely"
    echo "  $0 reverse                    # Configure network REVERSE locally"
    echo "  $0 set-password-admin         # Change password to admin locally"
    echo "  $0 forward-and-docker         # Configure network and install Docker locally"
    echo "  $0 add-user-to-docker         # Add user to docker group locally"
    echo "  $0 install-services           # Install all Docker services locally"
    echo "  $0 install-nodered-nodes      # Install Node-RED nodes locally"
    echo "  $0 import-nodered-flows       # Import Node-RED flows locally"
    echo "  $0 install-tailscale          # Install Tailscale VPN router locally"
    echo "  $0 install-curl               # Install curl locally"
    echo "  $0 check-dns                  # Check DNS locally"
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
                shift
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
                shift
                ;;
            import-nodered-flows)
                command="import-nodered-flows"
                shift
                ;;
            install-tailscale)
                command="install-tailscale"
                shift
                ;;
            check-dns)
                command="check-dns"
                shift
                ;;
            set-password-admin)
                command="set-password-admin"
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
        install-tailscale)
            print_status "Installing Tailscale VPN router..."
            install_tailscale_docker
            ;;
        check-dns)
            print_status "Checking internet and DNS..."
            check_internet_dns
            ;;
        set-password-admin)
            print_status "Changing password to admin..."
            configure_password_admin
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
