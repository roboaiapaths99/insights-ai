# 🚀 Academic Insights Deployment Guide

This guide contains the real commands to deploy your project to your **Hostinger VPS (KPM2)** using the subdomain **insights.agpkacademy.in**.

## 1. Prerequisites (Run on VPS)
Ensure your VPS is updated and has **Docker** installed. If not, run these commands:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install -y docker-compose
```

## 2. Upload Project to VPS
The easiest way is to use Git or SFTP. If using Git:
```bash
# Clone your repository (if using git)
# git clone <your-repo-url>
# cd academics_insights
```

## 3. Configure Environments
Ensure your `.env` file on the VPS is correct:
```bash
nano .env
```
Make sure it matches your OpenAI keys and secure passwords.

## 4. Deploy with Docker Compose
Run this command to build and start the entire stack:

```bash
docker-compose up -d --build
```
*Wait for a few minutes while it downloads images and builds your app.*

## 5. Verify Installation
- **Check if containers are running**: `docker ps`
- **Check logs (if something breaks)**: `docker-compose logs -f`
- Open your browser and go to: `http://insights.agpkacademy.in`

## 6. 🔒 Setup SSL (HTTPS)
To make your site secure with HTTPS, run these commands:

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL Certificate
sudo certbot --nginx -d insights.agpkacademy.in
```
Follow the prompts (enter your email, agree to terms). Certbot will automatically update your Nginx configuration to support HTTPS.

## 7. Restart for SSL
After Certbot finishes, you might need to restart Nginx:
```bash
docker-compose restart nginx
```

---

### Useful Commands
- **Stop everything**: `docker-compose down`
- **Restart everything**: `docker-compose restart`
- **Rebuild after code changes**: `docker-compose up -d --build`
