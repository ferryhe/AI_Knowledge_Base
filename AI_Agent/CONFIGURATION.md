# Configuration Guide

This document explains all configuration options for the AI Knowledge Base RAG system.

## Environment Variables

All environment variables should be set in `AI_Agent/.env` (copy from `.env.example`).

### Required Settings

#### `OPENAI_API_KEY`
- **Description**: Your OpenAI API key
- **Required**: Yes
- **Example**: `sk-proj-...`
- **Security**: Never commit this to git. Keep it in `.env` which is gitignored.
- **Where to get**: https://platform.openai.com/api-keys

### Optional Settings

#### `MODEL`
- **Description**: Chat model for generating responses
- **Default**: `gpt-4o`
- **Options**: 
  - `gpt-4o` - Best quality, most expensive
  - `gpt-4o-mini` - Good quality, cheaper
  - `gpt-3.5-turbo` - Fast, cheapest
- **Cost Impact**: High - this is called for every query
- **Recommendation**: Use `gpt-4o` for production, `gpt-4o-mini` for development

#### `EMBEDDING_MODEL`
- **Description**: Model for creating text embeddings
- **Default**: `text-embedding-3-large`
- **Options**:
  - `text-embedding-3-large` - Best quality (3072 dimensions)
  - `text-embedding-3-small` - Good quality, faster (1536 dimensions)
  - `text-embedding-ada-002` - Legacy, still good
- **Cost Impact**: Medium - called during indexing and for each query
- **Recommendation**: Use `text-embedding-3-large` unless you need faster/cheaper

#### `SOURCE_DIR`
- **Description**: Path to markdown files to index
- **Default**: `../Knowledge_Base_MarkDown`
- **Format**: Relative to `AI_Agent/` directory
- **Example**: `../Knowledge_Base_MarkDown` or `/absolute/path/to/docs`

#### `INDEX_PATH`
- **Description**: Where to save/load the FAISS index
- **Default**: `knowledge_base.faiss`
- **Format**: Relative to `AI_Agent/` or absolute path
- **Size**: Grows with corpus size (~10-100MB typical)

#### `META_PATH`
- **Description**: Where to save/load document metadata
- **Default**: `knowledge_base.meta.pkl`
- **Format**: Relative to `AI_Agent/` or absolute path
- **Size**: Smaller than index (~1-10MB typical)

#### `STREAMLIT_PORT`
- **Description**: Port for Streamlit UI (only affects `streamlit run` command)
- **Default**: `8501` (Streamlit's default)
- **Example**: `8502` if port 8501 is in use

## Build Index Parameters

These are command-line arguments to `scripts/build_index.py`:

### `--source`
- **Description**: Directory containing markdown files
- **Default**: Value of `SOURCE_DIR` env var
- **Example**: `--source /path/to/docs`

### `--max-tokens`
- **Description**: Maximum tokens per chunk
- **Default**: `500`
- **Recommendation**: 300-800 depending on your content
- **Trade-offs**:
  - **Larger chunks** (800+): More context, fewer chunks, less precise retrieval
  - **Smaller chunks** (200-300): More precise, more chunks, less context
- **Sweet spot**: 500 tokens ≈ 375 words

### `--overlap`
- **Description**: Token overlap between consecutive chunks
- **Default**: `80`
- **Recommendation**: 15-20% of chunk size
- **Purpose**: Prevents semantic breaks at chunk boundaries
- **Trade-offs**:
  - **More overlap**: Better continuity, more storage, slower indexing
  - **Less overlap**: Less storage, faster, risk of semantic breaks

### `--batch-size`
- **Description**: Number of chunks to embed in one API call
- **Default**: `64`
- **Range**: 1-100 (OpenAI embedding limit varies by model)
- **Recommendation**: 64-100 for faster indexing
- **Trade-offs**:
  - **Larger batches**: Faster, fewer API calls, higher memory
  - **Smaller batches**: Slower, more API calls, lower memory

## Retrieval Parameters

These are function parameters in the code:

### `k` (Number of results)
- **Description**: How many chunks to retrieve
- **Default**: `8`
- **Range**: 1-20 typical
- **Trade-offs**:
  - **More results** (10+): Better recall, more context, slower, more expensive
  - **Fewer results** (3-5): Faster, cheaper, might miss relevant info
- **Recommendation**: 
  - 5-8 for general use
  - 10-15 for complex questions

### `similarity_threshold` (Quality filter)
- **Description**: Minimum cosine similarity score
- **Default**: `0.0` (returns all k results)
- **Range**: 0.0-1.0
- **Recommendation**:
  - `0.0` - No filtering (default, backward compatible)
  - `0.3-0.4` - Moderate filtering (recommended)
  - `0.5-0.7` - Strict filtering (may return fewer than k results)
  - `0.8+` - Very strict (might return no results)
- **When to use**:
  - Use higher threshold when you want only highly relevant results
  - Use lower threshold for exploratory queries
  - Use 0.0 for backward compatibility

## Docker Configuration

Settings in `docker-compose.yml`:

### Resource Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'       # Maximum CPU cores
      memory: 2G        # Maximum RAM
    reservations:
      cpus: '1.0'       # Minimum CPU cores  
      memory: 1G        # Minimum RAM
```

**Recommendations**:
- **Small corpus** (< 100 docs): 1 CPU, 1GB RAM
- **Medium corpus** (100-500 docs): 2 CPU, 2GB RAM
- **Large corpus** (500+ docs): 4 CPU, 4GB RAM
- **High traffic**: Add more CPU, not necessarily more RAM

### Ports

```yaml
ports:
  - "${STREAMLIT_PORT:-8501}:8501"
```

- **8501**: Streamlit default
- **80/443**: HTTP/HTTPS (if using Caddy)

Change in `.env`:
```bash
STREAMLIT_PORT=8502
```

### Volumes

```yaml
volumes:
  - ./knowledge_base.faiss:/app/data/knowledge_base.faiss:ro
  - ./knowledge_base.meta.pkl:/app/data/knowledge_base.meta.pkl:ro
```

- **:ro** = read-only (security best practice)
- Files must exist before starting container
- Build them first with `python scripts/build_index.py`

## Caddy Configuration

Settings in `Caddyfile`:

### Domain
```
yourdomain.com {
    ...
}
```

Replace `yourdomain.com` with your actual domain.

### Email (for Let's Encrypt)
```
{
    email admin@yourdomain.com
}
```

Required for SSL certificate notifications.

### Rate Limiting (Optional)
```
rate_limit {
    zone rag_zone {
        key {remote}
        events 100      # 100 requests
        window 1m       # per minute
    }
}
```

Uncomment in production to prevent abuse.

## Performance Tuning

### For Faster Indexing
1. Increase `--batch-size` to 100
2. Use `text-embedding-3-small` model
3. Use faster CPU/SSD

### For Lower Latency
1. Use `similarity_threshold` to reduce candidates
2. Reduce `k` to 5-6
3. Use `gpt-4o-mini` instead of `gpt-4o`
4. Keep index in memory (already done with FAISS)

### For Lower Costs
1. Use `gpt-3.5-turbo` for chat
2. Use `text-embedding-3-small` for embeddings
3. Reduce `k` to minimize context tokens
4. Use higher `similarity_threshold` to filter more

### For Better Quality
1. Use `gpt-4o` for chat
2. Use `text-embedding-3-large` for embeddings
3. Increase `k` to 10-12
4. Use lower `similarity_threshold` (0.2-0.3)
5. Increase chunk size to 600-800 tokens

## Example Configurations

### Development (Fast & Cheap)
```bash
MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```
```bash
python scripts/build_index.py --max-tokens 400 --overlap 60 --batch-size 100
```

### Production (Quality)
```bash
MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-large
```
```bash
python scripts/build_index.py --max-tokens 500 --overlap 80 --batch-size 64
```

### High-Traffic (Balanced)
```bash
MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-large
```
- Use Caddy rate limiting
- Deploy multiple replicas behind load balancer
- Consider caching common queries

### Budget-Conscious
```bash
MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=text-embedding-ada-002
```
- Use higher similarity threshold (0.5)
- Reduce k to 5
- Cache aggressively

## Monitoring & Observability

### Health Checks

Docker Compose includes health checks:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

Check status:
```bash
docker-compose ps
```

### Logs

View logs:
```bash
# All services
docker-compose logs -f

# Just the RAG app
docker-compose logs -f rag-app

# Last 100 lines
docker-compose logs --tail=100 rag-app
```

Logs are rotated (max 10MB, 3 files).

### Metrics to Monitor

1. **Query Latency**: Time from question to answer
   - Target: < 3 seconds
   - Alert if: > 10 seconds

2. **Error Rate**: Failed queries / total queries
   - Target: < 1%
   - Alert if: > 5%

3. **Memory Usage**: Container RAM usage
   - Target: < 80% of limit
   - Alert if: > 90%

4. **API Costs**: OpenAI API usage
   - Monitor via OpenAI dashboard
   - Set budget alerts

## Troubleshooting Configuration Issues

### "Missing vector store files"
**Cause**: Index not built
**Fix**: `python scripts/build_index.py`

### "Invalid API key"
**Cause**: Wrong key in `.env`
**Fix**: Check `.env` has correct `OPENAI_API_KEY`

### "Out of memory"
**Cause**: Index too large for container
**Fix**: Increase memory limit in `docker-compose.yml`

### "Connection refused"
**Cause**: Port already in use
**Fix**: Change `STREAMLIT_PORT` in `.env`

### "No such file or directory"
**Cause**: Relative paths incorrect
**Fix**: Use absolute paths or check working directory

---

## Configuration Validation

Before deploying, verify your configuration:

```bash
# Check environment variables
cd AI_Agent
cat .env

# Verify paths exist
ls -lh knowledge_base.faiss knowledge_base.meta.pkl

# Test the system
python scripts/ask.py "test question"

# Check Docker config
docker-compose config
```

---

For more details, see:
- `IMPROVEMENTS.md` - Technical implementation details
- `DEPLOYMENT.md` - Deployment instructions
- `SECURITY.md` - Security checklist
