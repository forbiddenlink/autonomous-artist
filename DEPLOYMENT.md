# Production Deployment Guide

## Complete Production Deployment Guide for Autonomous Artist

This guide covers deploying your Flask application to production with Gunicorn, Nginx, SSL, and comprehensive monitoring.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Application Deployment](#application-deployment)
4. [Gunicorn Configuration](#gunicorn-configuration)
5. [Nginx Setup](#nginx-setup)
6. [SSL/HTTPS Configuration](#ssl-https-configuration)
7. [Process Management](#process-management)
8. [Monitoring & Logging](#monitoring--logging)
9. [Performance Optimization](#performance-optimization)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- Ubuntu 22.04+ or similar Linux distribution
- Python 3.11+
- Nginx
- Certbot (for SSL)
- Supervisor or systemd (process management)

### Required Access
- SSH access to server
- Sudo privileges
- Domain name pointing to server IP

---

## Server Setup

### 1. Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx supervisor certbot python3-certbot-nginx -y
```

### 2. Create Application User
```bash
sudo useradd -m -s /bin/bash artist
sudo usermod -aG www-data artist
```

### 3. Setup Application Directory
```bash
sudo mkdir -p /var/www/autonomous-artist
sudo chown artist:www-data /var/www/autonomous-artist
sudo chmod 755 /var/www/autonomous-artist
```

---

## Application Deployment

### 1. Transfer Application Files
```bash
# From your local machine
rsync -av --exclude='.venv' --exclude='__pycache__' \
  /path/to/autonomous-artist/ artist@your-server:/var/www/autonomous-artist/
```

### 2. Setup Virtual Environment
```bash
ssh artist@your-server
cd /var/www/autonomous-artist
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn[gevent]
```

### 3. Configure Environment
```bash
cp .env.example .env
nano .env
```

Set these critical values:
```bash
DEBUG=False
ALLOWED_ORIGINS=https://yourdomain.com
HF_API_TOKEN=your_actual_token_here
HOST=127.0.0.1
PORT=8000
```

### 4. Test Application
```bash
python3 production_check.py
python3 -m pytest test_comprehensive.py
```

---

## Gunicorn Configuration

### 1. Create Gunicorn Configuration File
```bash
sudo nano /etc/gunicorn/autonomous-artist.py
```

```python
# /etc/gunicorn/autonomous-artist.py
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"  # Async worker for better performance
worker_connections = 1000
max_requests = 10000  # Restart workers after N requests (prevents memory leaks)
max_requests_jitter = 1000  # Add randomness to prevent all workers restarting at once
timeout = 120
keepalive = 5

# Logging
accesslog = "/var/log/gunicorn/autonomous-artist-access.log"
errorlog = "/var/log/gunicorn/autonomous-artist-error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "autonomous-artist"

# Server mechanics
daemon = False
pidfile = "/var/run/gunicorn/autonomous-artist.pid"
umask = 0o007
tmp_upload_dir = None

# SSL (if terminating SSL at Gunicorn instead of Nginx)
# keyfile = "/path/to/key.pem"
# certfile = "/path/to/cert.pem"
```

### 2. Create Log Directories
```bash
sudo mkdir -p /var/log/gunicorn /var/run/gunicorn /etc/gunicorn
sudo chown artist:www-data /var/log/gunicorn /var/run/gunicorn
sudo chmod 755 /var/log/gunicorn /var/run/gunicorn
```

### 3. Test Gunicorn
```bash
cd /var/www/autonomous-artist
source venv/bin/activate
gunicorn --config /etc/gunicorn/autonomous-artist.py app:app
```

---

## Nginx Setup

### 1. Create Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/autonomous-artist
```

```nginx
# /etc/nginx/sites-available/autonomous-artist

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=50r/m;
limit_req_zone $binary_remote_addr zone=paint_limit:10m rate=10r/h;
limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

# Upstream Gunicorn
upstream autonomous_artist {
    server 127.0.0.1:8000 fail_timeout=0;
    keepalive 32;
}

# HTTP -> HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/letsencrypt;
    }
    
    # Redirect all HTTP to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration (will be added by Certbot)
    # ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL Best Practices (added by Certbot)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # Logging
    access_log /var/log/nginx/autonomous-artist-access.log;
    error_log /var/log/nginx/autonomous-artist-error.log;
    
    # Max upload size
    client_max_body_size 10M;
    client_body_buffer_size 128k;
    
    # Connection limits
    limit_conn conn_limit 10;
    
    # Timeouts
    proxy_connect_timeout 120s;
    proxy_send_timeout 120s;
    proxy_read_timeout 120s;
    
    # Static files
    location /static/ {
        alias /var/www/autonomous-artist/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Health check (no rate limit)
    location /health {
        proxy_pass http://autonomous_artist;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        access_log off;
    }
    
    # Paint endpoint (strict rate limit)
    location /api/paint {
        limit_req zone=paint_limit burst=2 nodelay;
        limit_req_status 429;
        
        proxy_pass http://autonomous_artist;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        proxy_http_version 1.1;
    }
    
    # Other API endpoints
    location /api/ {
        limit_req zone=api_limit burst=10 nodelay;
        limit_req_status 429;
        
        proxy_pass http://autonomous_artist;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        proxy_http_version 1.1;
    }
    
    # Root and other paths
    location / {
        proxy_pass http://autonomous_artist;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        proxy_http_version 1.1;
        proxy_redirect off;
        proxy_buffering off;
    }
}
```

### 2. Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/autonomous-artist /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## SSL/HTTPS Configuration

### 1. Install SSL Certificate with Certbot
```bash
# Create directory for Let's Encrypt challenges
sudo mkdir -p /var/www/letsencrypt
sudo chown www-data:www-data /var/www/letsencrypt

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 2. Auto-renewal
```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot automatically adds a cron job for renewal
# Verify it exists:
sudo systemctl list-timers | grep certbot
```

---

## Process Management

### Option A: Systemd (Recommended)

Create systemd service file:
```bash
sudo nano /etc/systemd/system/autonomous-artist.service
```

```ini
[Unit]
Description=Autonomous Artist Gunicorn daemon
Requires=network.target
After=network.target

[Service]
Type=notify
User=artist
Group=www-data
RuntimeDirectory=gunicorn
WorkingDirectory=/var/www/autonomous-artist
Environment="PATH=/var/www/autonomous-artist/venv/bin"
Environment="PYTHONPATH=/var/www/autonomous-artist"
ExecStart=/var/www/autonomous-artist/venv/bin/gunicorn \
    --config /etc/gunicorn/autonomous-artist.py \
    --pid /var/run/gunicorn/autonomous-artist.pid \
    app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable autonomous-artist
sudo systemctl start autonomous-artist
sudo systemctl status autonomous-artist
```

### Option B: Supervisor

```bash
sudo nano /etc/supervisor/conf.d/autonomous-artist.conf
```

```ini
[program:autonomous-artist]
command=/var/www/autonomous-artist/venv/bin/gunicorn --config /etc/gunicorn/autonomous-artist.py app:app
directory=/var/www/autonomous-artist
user=artist
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/autonomous-artist.log
environment=PATH="/var/www/autonomous-artist/venv/bin"
```

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start autonomous-artist
```

---

## Monitoring & Logging

### 1. Log Rotation
```bash
sudo nano /etc/logrotate.d/autonomous-artist
```

```
/var/log/gunicorn/autonomous-artist-*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 artist www-data
    sharedscripts
    postrotate
        systemctl reload autonomous-artist > /dev/null 2>&1 || true
    endscript
}

/var/www/autonomous-artist/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 artist www-data
}
```

### 2. Monitoring Script
```bash
nano /var/www/autonomous-artist/monitor.sh
```

```bash
#!/bin/bash
# Simple monitoring script

# Check if service is running
if ! systemctl is-active --quiet autonomous-artist; then
    echo "ALERT: Autonomous Artist service is down!"
    systemctl restart autonomous-artist
    # Send alert (configure email/Slack webhook)
fi

# Check disk space
DISK_USAGE=$(df -h /var/www/autonomous-artist | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "ALERT: Disk usage is at ${DISK_USAGE}%"
fi

# Check memory usage
MEM_USAGE=$(free | grep Mem | awk '{print ($3/$2) * 100.0}' | cut -d'.' -f1)
if [ "$MEM_USAGE" -gt 85 ]; then
    echo "ALERT: Memory usage is at ${MEM_USAGE}%"
fi

# Check application health
if ! curl -sf http://localhost:8000/health > /dev/null; then
    echo "ALERT: Health check failed!"
fi
```

Add to crontab:
```bash
chmod +x /var/www/autonomous-artist/monitor.sh
crontab -e
# Add: */5 * * * * /var/www/autonomous-artist/monitor.sh >> /var/log/monitoring.log 2>&1
```

---

## Performance Optimization

### 1. Gunicorn Performance
- Workers: `(2 * CPU_cores) + 1`
- Use `gevent` worker class for async I/O
- Set `max_requests` to prevent memory leaks
- Enable keepalive connections

### 2. Nginx Performance
- Enable gzip compression
- Set appropriate buffer sizes
- Use HTTP/2
- Enable caching for static files

### 3. Application Performance
- Use Redis for rate limiting persistence
- Implement connection pooling for external APIs
- Enable caching aggressively
- Monitor and optimize slow endpoints

---

## Troubleshooting

### Service Won't Start
```bash
# Check logs
sudo journalctl -u autonomous-artist -n 50
sudo tail -f /var/log/gunicorn/autonomous-artist-error.log

# Test manually
cd /var/www/autonomous-artist
source venv/bin/activate
gunicorn --config /etc/gunicorn/autonomous-artist.py app:app
```

### 502 Bad Gateway
- Check if Gunicorn is running: `sudo systemctl status autonomous-artist`
- Check firewall: `sudo ufw status`
- Check Gunicorn logs
- Verify socket/port configuration

### High Memory Usage
- Reduce number of Gunicorn workers
- Set `max_requests` lower to restart workers more frequently
- Check for memory leaks in application code
- Monitor with: `htop` or `top`

### Slow Responses
- Check HuggingFace API response times
- Review cache hit rates
- Monitor Gunicorn worker count
- Check Nginx access logs for slow requests

---

## Commands Reference

```bash
# Service management
sudo systemctl start/stop/restart/status autonomous-artist
sudo systemctl reload autonomous-artist  # Graceful reload

# View logs
sudo journalctl -u autonomous-artist -f
sudo tail -f /var/log/gunicorn/autonomous-artist-error.log
sudo tail -f /var/log/nginx/autonomous-artist-access.log

# Nginx
sudo nginx -t  # Test configuration
sudo systemctl reload nginx  # Reload without downtime

# Application
cd /var/www/autonomous-artist
source venv/bin/activate
python3 production_check.py
python3 -m pytest test_comprehensive.py

# SSL
sudo certbot renew
sudo certbot certificates
```

---

## Security Checklist

- [ ] Firewall configured (UFW)
- [ ] SSH key-based authentication only
- [ ] Regular system updates scheduled
- [ ] SSL certificate auto-renewal working
- [ ] Security headers configured
- [ ] Rate limiting active
- [ ] Environment variables secured
- [ ] File permissions correct (644 for files, 755 for directories)
- [ ] Database credentials (if any) in environment
- [ ] Fail2ban installed and configured
- [ ] Regular backup system in place

---

## Next Steps

1. Set up monitoring (Prometheus, Grafana, or similar)
2. Configure alerts (email, Slack, PagerDuty)
3. Implement log aggregation (ELK stack, CloudWatch)
4. Set up automated backups
5. Document runbooks for common issues
6. Create disaster recovery plan

---

**Last Updated**: February 6, 2026
**Deployment Guide Version**: 1.0.0
