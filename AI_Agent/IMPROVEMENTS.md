# RAG System Improvements Documentation

This document describes the improvements made to the AI Knowledge Base RAG (Retrieval Augmented Generation) system.

## 1. Core RAG Logic Improvements

### Chunking Strategy
**File**: `AI_Agent/scripts/build_index.py`

**Improvements**:
- **Token-based chunking** with 500 token chunks and 80 token overlap
- **Semantic continuity**: The overlap (16% of chunk size) helps prevent semantic breaks at chunk boundaries
- **Empty chunk filtering**: Only non-empty chunks are indexed
- **Rationale**: 
  - 500 tokens provides enough context for semantic understanding (~375 words)
  - 80 token overlap prevents loss of context at boundaries
  - This balances retrieval granularity with semantic coherence

**Configuration**:
```bash
python scripts/build_index.py --max-tokens 500 --overlap 80
```

### Similarity Threshold
**File**: `AI_Agent/scripts/ask.py`

**Improvements**:
- Added configurable `similarity_threshold` parameter to retrieval function
- Filters out low-quality matches based on cosine similarity score
- Default: 0.0 (returns all k results for backward compatibility)
- Recommended: 0.3-0.5 for production use

**Usage**:
```python
hits = retrieve(client, question, k=8, similarity_threshold=0.4)
```

### Hallucination Prevention
**File**: `AI_Agent/scripts/ask.py`

**Improvements**:
- Enhanced system prompt with explicit instructions:
  1. Answer ONLY from retrieved snippets
  2. Mandatory citation for every claim
  3. Explicit "I don't know" responses when insufficient information
  4. Never make up information
  5. State uncertainty explicitly
- **Result**: Model is less likely to hallucinate or fabricate answers

**System Prompt**:
```python
SYSTEM_PROMPT = (
    "You are the documentation expert for the IAA AI Knowledge Base. "
    "CRITICAL INSTRUCTIONS:\n"
    "1. Answer ONLY using information from the retrieved snippets provided below.\n"
    "2. Every claim must cite evidence using the snippet number and file path...\n"
    "..."
)
```

## 2. Performance & Scalability

### API Retry Logic
**File**: `AI_Agent/scripts/utils.py`

**Improvements**:
- Exponential backoff retry decorator for API calls
- Handles `APITimeoutError`, `RateLimitError`, and `APIError`
- Default: 3 retries with exponential backoff (1s, 2s, 4s...)
- Configurable max delay (60s default)

**Implementation**:
```python
@retry_with_exponential_backoff(max_retries=3, initial_delay=1.0)
def embed_batches(client: OpenAI, chunks: List[str]):
    resp = client.embeddings.create(model=EMBED_MODEL, input=chunks)
    return [item.embedding for item in resp.data]
```

**Benefits**:
- Handles transient API failures gracefully
- Prevents cascading failures
- Reduces manual intervention needed

### Batch Optimization
**File**: `AI_Agent/scripts/build_index.py`

**Current Status**: ✅ Already implemented
- Embeddings are created in batches (default 64 chunks)
- Reduces API calls and improves throughput
- Configurable via `--batch-size` parameter

### Error Handling
**Files**: `AI_Agent/scripts/build_index.py`, `AI_Agent/scripts/ask.py`

**Improvements**:
- Comprehensive error handling for file operations
- Graceful handling of encoding errors (UTF-8 → Latin-1 fallback)
- Validation of file content before processing
- Informative error messages for debugging

## 3. Deployment & Environment

### Docker Support
**Files**: 
- `AI_Agent/Dockerfile` - Multi-stage build for minimal image
- `AI_Agent/docker-compose.yml` - Complete deployment stack
- `AI_Agent/Caddyfile` - Reverse proxy configuration
- `AI_Agent/.dockerignore` - Optimized build context

**Features**:
- **Multi-stage build**: Separates build and runtime dependencies
- **Minimal image**: Python 3.11-slim base (smaller attack surface)
- **Non-root user**: Runs as `appuser` (UID 1000) for security
- **Resource limits**: Configurable CPU/memory limits
- **Health checks**: Automatic container health monitoring
- **Secure secrets**: Environment variables via `.env` file
- **Read-only mounts**: Vector store files mounted as read-only

**Image Size Optimization**:
- Build dependencies only in builder stage
- No embedding model weights in image (too large)
- Pre-built FAISS index mounted as volume
- Cleaned apt cache to reduce size

**Usage**:
```bash
# Build the image
docker build -t ai-knowledge-base -f AI_Agent/Dockerfile .

# Run with docker-compose
cd AI_Agent
docker-compose up -d

# View logs
docker-compose logs -f rag-app
```

### Environment Variables Security
**File**: `AI_Agent/.env.example`

**Best Practices**:
- API keys never hardcoded in code or Dockerfile
- `.env` file for local development (gitignored)
- Docker secrets or environment variables for production
- Separate `.env.example` for documentation

**Production Setup**:
```bash
# Option 1: Use .env file
cp .env.example .env
# Edit .env with your keys
docker-compose up -d

# Option 2: Pass via command line
OPENAI_API_KEY=sk-xxx docker-compose up -d

# Option 3: Docker secrets (recommended for production)
echo "sk-xxx" | docker secret create openai_api_key -
```

### Resource Limits
**File**: `AI_Agent/docker-compose.yml`

**Configuration**:
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'      # Maximum CPU cores
      memory: 2G       # Maximum RAM
    reservations:
      cpus: '1.0'      # Minimum CPU cores
      memory: 1G       # Minimum RAM
```

**Rationale**:
- Prevents resource exhaustion on shared hosts
- 2GB RAM sufficient for FAISS index + embeddings
- 2 CPU cores handles concurrent requests
- Adjust based on index size and query load

### Reverse Proxy with Caddy
**File**: `AI_Agent/Caddyfile`

**Features**:
- Automatic HTTPS with Let's Encrypt
- WebSocket support for Streamlit
- Security headers (HSTS, CSP, etc.)
- Rate limiting (optional)
- Structured logging
- HTTP to HTTPS redirect

**Setup**:
```bash
# Edit Caddyfile with your domain
vim AI_Agent/Caddyfile

# Start with Caddy
docker-compose up -d caddy

# Caddy automatically obtains SSL certificates
```

## 4. Testing & Data Consistency

### Comprehensive Test Suite
**File**: `AI_Agent/tests/test_rag_pipeline.py`

**Test Coverage**:

1. **File Validation Tests** (`TestFileValidation`)
   - Valid files pass validation
   - Empty files are rejected
   - Whitespace-only files are rejected
   - Too-short files are rejected
   - Corrupted/binary files are rejected

2. **Chunking Tests** (`TestChunking`)
   - Normal text creates multiple chunks
   - Empty text returns no chunks
   - Short text creates single chunk
   - Chunks are non-empty after processing

3. **Index Building Tests** (`TestBuildIndex`)
   - Valid files successfully build index
   - Empty files are skipped with warnings
   - Error messages are informative

4. **Retrieval Tests** (`TestRetrieval`)
   - Retrieval returns relevant documents
   - Similarity threshold filters results
   - High threshold returns fewer results

5. **No Match Handling** (`TestNoMatchResponse`)
   - Empty results are handled gracefully
   - System returns appropriate "I don't know" response

### File Upload Validation
**File**: `AI_Agent/scripts/utils.py`

**Function**: `validate_file_content(file_path, content)`

**Checks**:
1. Content is not empty
2. Content is not only whitespace
3. Minimum 10 characters of actual content
4. At least 80% printable characters (detects binary/corrupted files)

**Usage**:
```python
is_valid, error_msg = validate_file_content("doc.md", content)
if not is_valid:
    print(f"Validation failed: {error_msg}")
```

### "I Don't Know" Response
**File**: `AI_Agent/scripts/ask.py`

**Implementation**:
```python
hits = retrieve(client, question)
if not hits:
    print("I don't have enough information to answer this question.")
    sys.exit(0)
```

**Benefits**:
- Prevents hallucination when no relevant documents found
- User gets honest response instead of made-up answer
- Maintains trust in the system

### Running Tests
```bash
cd AI_Agent
pytest tests/test_rag_pipeline.py -v
pytest tests/test_smoke.py -v  # Original smoke tests

# With coverage
pytest tests/ --cov=scripts --cov-report=html
```

## 5. Migration Guide

### For Existing Installations

1. **Update Dependencies**:
   ```bash
   cd AI_Agent
   pip install -r requirements.txt
   ```

2. **Rebuild Index** (optional but recommended):
   ```bash
   python scripts/build_index.py --source ../Knowledge_Base_MarkDown
   ```

3. **Update Environment Variables** (optional):
   - No breaking changes, existing `.env` files work as-is
   - Can add new features by updating `.env`:
     ```
     SIMILARITY_THRESHOLD=0.4  # Optional: filter low-quality matches
     ```

4. **Run Tests**:
   ```bash
   pytest tests/
   ```

### For New Deployments

1. **Using Docker** (Recommended):
   ```bash
   # Copy environment template
   cp AI_Agent/.env.example AI_Agent/.env
   # Edit with your API key
   vim AI_Agent/.env
   
   # Build index locally first
   cd AI_Agent
   python scripts/build_index.py
   
   # Start services
   docker-compose up -d
   ```

2. **Local Installation**:
   ```bash
   cd AI_Agent
   make setup
   make index
   make ask q="your question"
   ```

## 6. Configuration Reference

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | - | Yes |
| `MODEL` | Chat model | `gpt-4o` | No |
| `EMBEDDING_MODEL` | Embedding model | `text-embedding-3-large` | No |
| `SOURCE_DIR` | Markdown source directory | `../Knowledge_Base_MarkDown` | No |
| `INDEX_PATH` | FAISS index file path | `knowledge_base.faiss` | No |
| `META_PATH` | Metadata pickle file path | `knowledge_base.meta.pkl` | No |

### Build Index Parameters

```bash
python scripts/build_index.py \
  --source ../Knowledge_Base_MarkDown \
  --max-tokens 500 \      # Chunk size
  --overlap 80 \          # Overlap size
  --batch-size 64         # Embedding batch size
```

### Retrieval Parameters

```python
retrieve(
    client,
    question,
    k=8,                      # Number of results
    similarity_threshold=0.4  # Minimum similarity (0.0-1.0)
)
```

## 7. Performance Benchmarks

### Typical Performance (Based on Current Corpus)

- **Index Build Time**: ~2-5 minutes for 50+ documents
- **Query Latency**: ~1-2 seconds (embedding + retrieval + generation)
- **Memory Usage**: ~500MB-1GB (depends on index size)
- **Throughput**: ~30-60 queries/minute (limited by OpenAI API)

### Optimization Tips

1. **For Faster Indexing**:
   - Increase `--batch-size` (64-128)
   - Use faster embedding model (e.g., `text-embedding-ada-002`)

2. **For Lower Latency**:
   - Use similarity threshold to reduce candidates
   - Reduce `k` parameter (fewer chunks to send to LLM)

3. **For Lower Costs**:
   - Use smaller embedding model
   - Use GPT-3.5-turbo instead of GPT-4

## 8. Security Considerations

### Implemented Protections

1. **API Key Security**:
   - Never commit `.env` to git
   - Use environment variables in containers
   - Consider Docker secrets for production

2. **Container Security**:
   - Non-root user (UID 1000)
   - Read-only file system for data
   - Resource limits prevent DoS
   - Minimal base image reduces attack surface

3. **Network Security**:
   - Caddy provides automatic HTTPS
   - Security headers (HSTS, CSP, etc.)
   - Optional rate limiting

4. **Input Validation**:
   - File content validation prevents processing corrupted data
   - Query sanitization via LLM prompt engineering

### Future Enhancements

- [ ] Add authentication/authorization
- [ ] Implement request rate limiting
- [ ] Add audit logging
- [ ] Encrypt vector store at rest
- [ ] Add CORS configuration

## 9. Troubleshooting

### Common Issues

1. **"Missing vector store files"**
   - **Solution**: Run `python scripts/build_index.py` first

2. **Docker container unhealthy**
   - **Check logs**: `docker-compose logs rag-app`
   - **Verify mounts**: Ensure FAISS files exist and are mounted

3. **API timeout errors**
   - **Solution**: Retry logic handles this automatically
   - **Check**: Network connectivity to OpenAI API

4. **Out of memory errors**
   - **Solution**: Increase container memory limit
   - **Or**: Reduce batch size during indexing

5. **Test failures with tiktoken**
   - **Cause**: tiktoken tries to download data during import
   - **Solution**: Tests now mock tiktoken encoder

### Debug Mode

```bash
# Enable verbose logging
export PYTHONUNBUFFERED=1

# Run with debug output
python -v scripts/ask.py "your question"

# Check Docker logs
docker-compose logs -f --tail=100 rag-app
```

## 10. Future Roadmap

### Planned Improvements

- [ ] Async API support for concurrent requests
- [ ] Streaming responses for better UX
- [ ] Vector database integration (Pinecone/Milvus/Weaviate)
- [ ] Semantic chunking (preserving paragraph/section boundaries)
- [ ] Reranking for better retrieval quality
- [ ] Multi-modal support (images, tables)
- [ ] Fine-tuned embeddings for domain-specific content
- [ ] A/B testing framework for prompt engineering
- [ ] Observability (Prometheus metrics, tracing)
- [ ] CI/CD pipeline for automated testing

## 11. Contributing

### Development Workflow

1. Create feature branch
2. Make changes
3. Add tests
4. Run test suite: `pytest tests/`
5. Update documentation
6. Submit pull request

### Code Quality

- Follow PEP 8 style guide
- Add type hints
- Write docstrings
- Maintain >80% test coverage
- Use meaningful variable names
- Keep functions focused and small

---

For questions or issues, please open a GitHub issue or contact the maintainers.
