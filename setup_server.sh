#!/bin/bash

# PollAgg Lightsail Auto-Setup Script
echo "🚀 Starting PollAgg Server Setup..."

# 1. Update and install basic tools
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y curl git build-essential

# 2. Install Docker
if ! command -v docker &> /dev/null
then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

# 3. Install Docker Compose
sudo apt-get install -y docker-compose

# 4. Firewall Setup (only public-facing ports — backend/frontend stay behind nginx)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

echo "Server Basic Setup Complete"
echo "Next steps:"
echo "1. git clone the repository into /home/<user>/pollagg"
echo "2. cp .env.example .env && edit .env (set strong POSTGRES_PASSWORD, NEXT_PUBLIC_API_URL)"
echo "3. docker compose up -d --build"
echo "4. After DNS A-records resolve to this host, run certbot to issue Let's Encrypt certs"
echo "   then uncomment the HTTPS server blocks in nginx/conf.d/pollagg.conf and reload nginx."
