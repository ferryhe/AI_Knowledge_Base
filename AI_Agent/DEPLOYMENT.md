# Quick Start Deployment Guide

This guide helps you deploy the AI Knowledge Base RAG system with Docker.

## Prerequisites

- Docker and Docker Compose installed
- OpenAI API key
- Pre-built FAISS index (see below)

## Step 1: Build the Vector Index

Before deploying, you need to build the FAISS index from your markdown files:

```bash
cd AI_Agent

# Install dependencies locally (one-time setup)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Set your OpenAI API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Build the index
python scripts/build_index.py --source ../Knowledge_Base_MarkDown
```

This creates:
- `knowledge_base.faiss` - Vector index
- `knowledge_base.meta.pkl` - Document metadata

## Step 2: Configure Environment

Edit `AI_Agent/.env` with your configuration:

```bash
OPENAI_API_KEY=sk-your-actual-key-here
MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-large
```

## Step 3: Deploy with Docker

### Option A: Simple Deployment (Streamlit only)

```bash
cd AI_Agent

# Build and start the container
docker-compose up -d rag-app

# Check logs
docker-compose logs -f rag-app

# Access at http://localhost:8501
```

### Option B: Full Deployment (with Caddy reverse proxy)

1. Edit `Caddyfile` with your domain name:
```bash
vim Caddyfile
# Replace 'yourdomain.com' with your actual domain
```

2. Start all services:
```bash
docker-compose up -d

# Check logs
docker-compose logs -f
```

3. Access at:
- Direct: http://localhost:8501 (Streamlit)
- Proxied: https://yourdomain.com (via Caddy with automatic HTTPS)

## Step 4: Verify Deployment

1. **Health Check**:
```bash
# Check container health
docker-compose ps

# Manual health check
curl http://localhost:8501/_stcore/health
```

2. **Test Query**:
- Open http://localhost:8501 in browser
- Ask a question: "What are the AI governance frameworks?"
- Verify you get a response with citations

## Step 5: Maintenance

### Update the Index

When you add new documents:

```bash
# Rebuild the index locally
cd AI_Agent
python scripts/build_index.py

# Restart the container to pick up changes
docker-compose restart rag-app
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f rag-app
docker-compose logs -f caddy
```

### Backup

Important files to backup:
- `AI_Agent/knowledge_base.faiss` - Vector index
- `AI_Agent/knowledge_base.meta.pkl` - Metadata
- `AI_Agent/.env` - Configuration (contains secrets!)

### Update Application

```bash
# Pull latest code
git pull

# Rebuild container
docker-compose build rag-app

# Restart with new image
docker-compose up -d rag-app
```

## Troubleshooting

### Container won't start

**Check logs**:
```bash
docker-compose logs rag-app
```

**Common issues**:
1. Missing FAISS files → Run `build_index.py` first
2. Invalid API key → Check `.env` file
3. Port already in use → Change `STREAMLIT_PORT` in `.env`

### "Missing vector store files" error

**Solution**: Build the index first:
```bash
cd AI_Agent
python scripts/build_index.py
```

### Out of memory

**Solution**: Increase container memory:
```yaml
# In docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G  # Increase from 2G
```

### Caddy SSL certificate issues

**Common causes**:
1. Domain not pointing to server
2. Ports 80/443 blocked
3. Invalid email in Caddyfile

**Debug**:
```bash
docker-compose logs caddy
```

## Security Best Practices

1. **Never commit `.env` to git**
   ```bash
   # Already in .gitignore, but double-check
   cat .gitignore | grep .env
   ```

2. **Use Docker secrets in production**
   ```bash
   # Instead of .env file
   echo "sk-xxx" | docker secret create openai_api_key -
   ```

3. **Keep dependencies updated**
   ```bash
   pip install -r requirements.txt --upgrade
   docker-compose build --no-cache
   ```

4. **Enable Caddy rate limiting**
   - Uncomment rate_limit section in Caddyfile
   - Protects against abuse

5. **Regular backups**
   - Backup FAISS index and metadata
   - Backup `.env` configuration
   - Store in secure location

## Resource Planning

### Minimum Requirements
- 1 CPU core
- 1 GB RAM
- 5 GB disk space

### Recommended for Production
- 2-4 CPU cores
- 2-4 GB RAM
- 20 GB disk space
- SSD storage for faster retrieval

### Scaling Considerations
- **More documents**: Increase RAM (FAISS index size grows)
- **More users**: Increase CPU cores
- **Faster queries**: Use SSD storage
- **High availability**: Run multiple replicas behind load balancer

## Production Checklist

- [ ] FAISS index built and tested locally
- [ ] `.env` file configured with valid API key
- [ ] Domain DNS pointing to server (if using Caddy)
- [ ] Firewall rules allow ports 80, 443 (if using Caddy)
- [ ] Docker and Docker Compose installed
- [ ] Sufficient disk space available
- [ ] Backup strategy in place
- [ ] Monitoring/alerting configured
- [ ] SSL certificate obtained (automatic with Caddy)
- [ ] Rate limiting enabled (optional)
- [ ] Logs being collected/rotated

## Getting Help

- **Documentation**: See `IMPROVEMENTS.md` for detailed explanations
- **Issues**: Open a GitHub issue
- **Logs**: Always include relevant logs when asking for help

---

**Next Steps**:
- Read `IMPROVEMENTS.md` for technical details
- Review `AI_Agent/README.md` for CLI usage
- Check `tests/` for examples of testing
