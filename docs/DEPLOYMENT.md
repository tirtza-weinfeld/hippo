# Deployment Guide

This guide covers deploying Hippo to Railway with models stored on HuggingFace Hub.

## Architecture Overview

```
Local Machine          HuggingFace Hub         Railway (Production)
─────────────          ───────────────         ─────────────────────

make train  ──────►   make upload  ──────►    API downloads
(models/)             (HF Hub)                 (.hf_cache/)
                                               │
                                               ▼
                                               In-memory network
                                               (state.network)
```

**Key concept:** Training happens locally, models are stored on HuggingFace Hub, and Railway downloads models on startup.

## Prerequisites

1. **Railway account** - Sign up at https://railway.app
2. **HuggingFace account** - Sign up at https://huggingface.co
3. **At least one trained model** - Run `make train` locally

## Step 1: Create HuggingFace Repository

```bash
# Visit https://huggingface.co/new
# Create a new repository (public or private)
# Example: your-username/hippo-models
```

## Step 2: Configure Environment

Create `.env` file in project root:

```bash
# Required
HF_MODEL_REPO=your-username/hippo-models
DEFAULT_MODEL=mnist-relu-100

# Optional (only for private repos)
HUGGINGFACE_TOKEN=hf_your_token_here

# Optional
HF_CACHE_DIR=.hf_cache
ALLOWED_ORIGINS=https://your-frontend.com
```

## Step 3: Train and Upload First Model

```bash
# Train a model
make train

# Upload to HuggingFace Hub
make upload MODEL=models/mnist-relu-100-TIMESTAMP.npz ACC=95.4
```

**Note:** After upload, local files are automatically deleted. HuggingFace Hub becomes the source of truth.

## Step 4: Deploy to Railway

### Install Railway CLI

```bash
npm install -g @railway/cli
```

### Deploy

```bash
# Login to Railway
railway login

# Link to your Railway project (or create new one)
railway link

# Deploy
railway up
```

### Configure Environment Variables in Railway

Go to Railway dashboard and set:

```bash
# Required
HF_MODEL_REPO=your-username/hippo-models
DEFAULT_MODEL=mnist-relu-100

# Optional (for private HF repos)
HUGGINGFACE_TOKEN=hf_...

# Optional
HF_CACHE_DIR=.hf_cache
ALLOWED_ORIGINS=https://your-frontend.com
```

**Note:** `DATABASE_URL` is auto-provided by Railway if you add a PostgreSQL service.

## Step 5: Verify Deployment

### Check Health Endpoint

```bash
curl https://your-app.railway.app/healthz
```

Expected response:
```json
{
  "status": "healthy",
  "network_loaded": true
}
```

### Test Prediction Endpoint

```bash
curl -X POST https://your-app.railway.app/predict \
  -H "Content-Type: application/json" \
  -d '{"pixels": [0.0, 0.1, ..., 0.9]}'  # 784 values
```

## Updating Models

### Process

```bash
# 1. Train new model locally
make train ARGS='--sizes 784 200 10 --epochs 50'

# 2. Upload to HuggingFace Hub
make upload MODEL=models/mnist-relu-200-TIMESTAMP.npz ACC=97.2

# 3. Update DEFAULT_MODEL in Railway dashboard
# Set to: mnist-relu-200-TIMESTAMP

# 4. Redeploy
railway up
```

### What Happens on Update

1. API restarts
2. Checks `.hf_cache/` for new model name
3. Model not cached → downloads from HF Hub
4. Caches model in `.hf_cache/`
5. Loads into memory (`state.network`)
6. Ready to serve requests

**Caching behavior:**
- First time: Downloads model (2-6 seconds)
- Subsequent deploys: Uses cached model (<1 second)
- Old models remain in cache (manual cleanup if needed)

## Railway Persistent Storage

Railway automatically provides persistent storage:

- **`.hf_cache/`** directory persists between deployments
- Models downloaded once are reused indefinitely
- Only re-downloads when `DEFAULT_MODEL` changes

### Startup Flow

```python
# api/main.py lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    manager = ModelManager()
    state.network = manager.load_model(model_name)  # Downloads if not cached
    yield
```

**Process:**
1. Check if model exists in `.hf_cache/`
2. If missing → download from HuggingFace Hub
3. Load model from cache into RAM
4. All API requests use in-memory network

## Performance Metrics

### Cold Start (First Deployment)
- Download model: 1-5 seconds (depends on size)
- Load into memory: <1 second
- **Total:** ~2-6 seconds

### Warm Start (Subsequent Deployments)
- Load from cache: <1 second
- No network calls to HuggingFace Hub

### Request Handling
- In-memory inference: ~milliseconds
- No disk I/O per request

## Production Checklist

Before going live:

- [ ] At least one model uploaded to HuggingFace Hub
- [ ] Railway environment variables configured
- [ ] `HF_MODEL_REPO` and `DEFAULT_MODEL` set correctly
- [ ] `HUGGINGFACE_TOKEN` set (if using private repo)
- [ ] CORS `ALLOWED_ORIGINS` configured for frontend
- [ ] Health endpoint returns `network_loaded: true`
- [ ] Test `/predict` endpoint with sample data
- [ ] Test `/activations` endpoint with sample data

## Troubleshooting

### "Failed to load model from HF Hub"

**Causes:**
- Incorrect `HF_MODEL_REPO` value
- `DEFAULT_MODEL` doesn't match uploaded model name
- Private repo without `HUGGINGFACE_TOKEN`

**Solutions:**
```bash
# Verify model exists on HF Hub
https://huggingface.co/YOUR_USERNAME/hippo-models

# Check Railway logs
railway logs

# Verify environment variables
railway variables
```

### "Model not found on HF Hub"

**Causes:**
- Model wasn't uploaded successfully
- Filename mismatch
- Missing `.npz` or `.json` file

**Solutions:**
```bash
# Check HuggingFace Hub repo
# Both files should exist:
# - mnist-relu-100.npz
# - mnist-relu-100.json

# Re-upload if needed
make upload MODEL=models/mnist-relu-100.npz ACC=95.4
```

### Slow Startup Times

**Expected:**
- First deployment: 2-6 seconds (downloads model)
- Subsequent deploys: <1 second (uses cache)

**If consistently slow:**
- Check model size (large models take longer)
- Check Railway region/network latency
- Verify persistent storage is enabled

### Cache Not Persisting

**Check:**
```bash
# Verify Railway volume is mounted
# In Railway dashboard → Service → Settings → Volumes

# Ensure .hf_cache/ is in project root, not /tmp
# Check api/main.py HF_CACHE_DIR configuration
```

### API Returns 503 (Service Unavailable)

**Cause:** Model failed to load on startup

**Solutions:**
```bash
# Check Railway logs for specific error
railway logs

# Common issues:
# - Incorrect DEFAULT_MODEL name
# - Network timeout downloading from HF Hub
# - Missing HUGGINGFACE_TOKEN for private repo
```

## Local Development

### Setup

```bash
# Create .env file
cp .env.example .env

# Edit .env with your settings
HF_MODEL_REPO=your-username/hippo-models
DEFAULT_MODEL=mnist-relu-100
HUGGINGFACE_TOKEN=hf_...  # Optional
```

### Run Locally

```bash
# Install dependencies
make install

# Start API server
make start

# First run downloads model from HF Hub to .hf_cache/
# Subsequent runs use cached model
```

**Note:** `.hf_cache/` is gitignored. Each developer downloads models independently.

## Advanced: Rolling Back Models

To rollback to a previous model:

```bash
# 1. Find old model name on HuggingFace Hub
# Visit: https://huggingface.co/your-username/hippo-models

# 2. Update DEFAULT_MODEL in Railway dashboard
DEFAULT_MODEL=mnist-relu-100-OLD_TIMESTAMP

# 3. Redeploy
railway up

# If old model was cached, it loads instantly
# If not cached, downloads from HF Hub
```

## Deployment URL

**Production:** https://hippo.up.railway.app

**Endpoints:**
- `GET /healthz` - Health check
- `POST /predict` - Digit prediction
- `POST /activations` - Layer activations
- `GET /docs` - Interactive API documentation

## Related Documentation

- **Architecture overview:** `docs/introduction.md`
- **Training guide:** `docs/TRAINING.md`
- **Training concepts:** `docs/TRAINING_CONCEPTS.md`

## Support

- **Railway docs:** https://docs.railway.app
- **HuggingFace Hub docs:** https://huggingface.co/docs/hub
- **Project issues:** Check Railway logs with `railway logs`
