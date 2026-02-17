# 🚀 Quick Deployment Guide

Get your Autonomous Artist application running in production in minutes!

## 📋 Prerequisites

- Docker & Docker Compose installed
- Git (to clone the repository)
- API keys (HuggingFace required, others optional)

---

## ⚡ Option 1: Docker Deployment (Recommended - 5 minutes)

### Step 1: Clone and Configure

```bash
# Clone repository
git clone <your-repo-url>
cd autonomous-artist

# Create environment file
cp .env.example .env

# Edit with your API keys
nano .env  # or vim, code, etc.
```

**Required in `.env`:**
```bash
HF_API_TOKEN=your_huggingface_token_here
```

### Step 2: Deploy!

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

That's it! 🎉

**Your application is now running at:**
- 🌐 Main app: http://localhost:5001
- 💚 Health check: http://localhost:5001/health
- 📊 Metrics: http://localhost:5001/metrics

### Quick Commands

```bash
# View logs
docker-compose logs -f app

# Restart
docker-compose restart

# Stop
docker-compose down

# Update and redeploy
git pull
docker-compose up -d --build
```

---

## 🐧 Option 2: Systemd Deployment (Linux Servers)

For production Linux servers with systemd.

### Step 1: Prepare Server

```bash
# Install Python 3.14
sudo apt update
sudo apt install python3.14 python3.14-venv python3-pip

# Clone repository
git clone <your-repo-url>
cd autonomous-artist
```

### Step 2: Configure

```bash
# Create environment file
cp .env.example .env
nano .env  # Add your API keys
```

### Step 3: Deploy with Systemd

```bash
# Make script executable
chmod +x deploy-systemd.sh

# Run deployment (requires sudo)
sudo ./deploy-systemd.sh
```

### Systemd Commands

```bash
# View logs
sudo journalctl -u autonomous-artist -f

# Restart service
sudo systemctl restart autonomous-artist

# Stop service
sudo systemctl stop autonomous-artist

# Check status
sudo systemctl status autonomous-artist
```

---

## 🌐 Option 3: Manual Deployment

For maximum control.

### Step 1: Install Dependencies

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### Step 2: Configure

```bash
# Set up environment
cp .env.example .env
nano .env  # Add your API keys
```

### Step 3: Run Production Server

```bash
# With Gunicorn (recommended)
gunicorn -w 4 -b 0.0.0.0:5001 app:app

# Or Flask development server (not for production!)
python app.py
```

---

## 🔧 Production Checklist

Before going live, ensure:

- [ ] ✅ `DEBUG=False` in `.env`
- [ ] ✅ Strong secret keys configured
- [ ] ✅ Rate limiting enabled
- [ ] ✅ CORS origins restricted (not `*`)
- [ ] ✅ HTTPS/SSL certificate configured
- [ ] ✅ Firewall rules configured
- [ ] ✅ Backups configured
- [ ] ✅ Monitoring enabled
- [ ] ✅ Log rotation configured

### Quick Production Validation

```bash
# Run production check
python production_check.py

# Should show all green ✅
```

---

## 🔐 SSL/HTTPS Setup

### Option A: Let's Encrypt (Free)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

### Option B: Update nginx.conf

Uncomment the HTTPS section in `nginx.conf` and update:

```nginx
server_name your-domain.com;
ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
```

Then restart:

```bash
docker-compose restart nginx
# or for systemd
sudo systemctl restart nginx
```

---

## 📊 Enable Monitoring

### Step 1: Install OpenTelemetry

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-flask
```

### Step 2: Configure

In `.env`:

```bash
MONITORING_ENABLED=True
OTEL_EXPORTER_OTLP_ENDPOINT=localhost:4317
```

### Step 3: Set Up Collector (Optional)

See [MONITORING.md](MONITORING.md) for full OpenTelemetry setup with Prometheus & Grafana.

---

## 🆘 Troubleshooting

### Application won't start

```bash
# Check logs
docker-compose logs app
# or
sudo journalctl -u autonomous-artist

# Verify environment
python production_check.py
```

### Health check fails

```bash
# Test directly
curl http://localhost:5001/health

# Check if port is in use
sudo lsof -i :5001
```

### Port already in use

Change port in `.env`:

```bash
PORT=8080
```

Then restart.

### Out of memory

Increase Docker memory limit or add swap space:

```bash
# Check current usage
docker stats

# Reduce workers in docker-compose.yml
CMD ["gunicorn", "--workers", "2", ...]
```

---

## 📈 Scaling

### Horizontal Scaling

Run multiple instances behind a load balancer:

```bash
docker-compose up -d --scale app=3
```

### Vertical Scaling

Increase resources in `docker-compose.yml`:

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

---

## 🔄 CI/CD Integration

The repository includes a GitHub Actions workflow in `.github/workflows/ci-cd.yml`.

### Setup:

1. Add secrets to GitHub:
   - `HUGGINGFACE_API_KEY`
   - `DEPLOY_HOST`
   - `DEPLOY_USER`
   - `DEPLOY_SSH_KEY`

2. Push to main branch
3. Automatic deployment happens! 🚀

---

## 📚 Additional Resources

- **Full Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Security Best Practices**: [SECURITY.md](SECURITY.md)
- **Performance Tuning**: [PERFORMANCE.md](PERFORMANCE.md)
- **Monitoring Setup**: [MONITORING.md](MONITORING.md)
- **API Documentation**: [API.md](API.md)

---

## ✅ Success Checklist

After deployment, verify:

```bash
# Health check returns 200
curl http://localhost:5001/health

# Can create a painting
curl -X POST http://localhost:5001/api/paint \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'

# Metrics are being collected
curl http://localhost:5001/metrics
```

---

## 🎉 You're Live!

Your Autonomous Artist is now running in production!

**Next Steps:**
- Set up monitoring alerts
- Configure backups
- Enable auto-scaling
- Add a CDN for static files
- Set up log aggregation

Need help? Check the detailed guides or open an issue on GitHub.

---

**Happy Creating! 🎨**
