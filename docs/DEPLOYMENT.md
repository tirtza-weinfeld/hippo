# Deployment Guide - Hippo Project

This guide documents how to deploy Hippo using our production stack: **Railway** (hosting) + **Neon** (PostgreSQL) + **HuggingFace Hub** (model storage).

## Our Production Stack

```
Local Development      Cloud Services              Railway Production
─────────────────      ──────────────              ──────────────────

make train   ──────►   HuggingFace Hub   ──────►   API downloads
(models/)              (model storage)              (.hf_cache/)
                                                    │
                                                    ▼
                                                    In-memory network

make migrate ──────►   Git (migrations)   ──────►  Neon PostgreSQL
(alembic/)                                          (vocabulary data)
```

**How it works:**
- Train models locally → Upload to HuggingFace Hub
- Railway downloads models on startup (cached in `.hf_cache/`)
- Neon PostgreSQL stores vocabulary data
- Database migrations tracked in git, applied via Railway

## Prerequisites

1. **Railway account** - https://railway.app
2. **Neon account** - https://neon.tech
3. **HuggingFace account** - https://huggingface.co
4. **At least one trained model** - Run `make train` locally

## Step 1: Create HuggingFace Repository

```bash
# Visit https://huggingface.co/new
# Create a new repository (public or private)
# Example: your-username/hippo-models
```

## Step 2: Set Up Neon PostgreSQL

1. Go to https://neon.tech and create account
2. Create new project (name it `hippo-db` or similar)
3. **Neon automatically creates two branches:**
   - `production` (default) - For Railway deployment
   - `development` - For local development
4. Copy connection strings from dashboard:
   - Click on `production` branch → copy connection string
   - Click on `development` branch → copy connection string
5. **Important:** Change `postgresql://` to `postgresql+psycopg://`

Example:
```
# Neon gives you:
postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require

# Change to:
postgresql+psycopg://user:pass@ep-xxx.neon.tech/neondb?sslmode=require
```

**Why use branches?**
- ✅ Isolates local development from production data
- ✅ Safe to test migrations and data changes locally
- ✅ Easy to reset development branch if needed
- ✅ Same database engine in both environments

## Step 3: Configure Local Environment

Create `.env` file in project root (or use `.env.example` as template):

```bash
# Database (Required) - Use DEVELOPMENT branch for local work
DATABASE_URL=postgresql+psycopg://user:pass@ep-dev-endpoint.neon.tech/neondb?sslmode=require

# HuggingFace Hub (Required)
HF_MODEL_REPO=your-username/hippo-models
DEFAULT_MODEL=mnist-relu-100

# Optional (only for private HF repos)
HUGGINGFACE_TOKEN=hf_your_token_here

# CORS Origins (Production URLs)
ALLOWED_ORIGINS=https://your-frontend.com,http://localhost:3000

# Optional
HF_CACHE_DIR=.hf_cache
```

**See `.env.example` for all available variables.**

## Step 4: Run Database Migrations (Local)

```bash
# Apply migrations to create vocabulary tables
make upgrade

# Verify database tables were created
# Check your Neon dashboard or connect with psql
```

## Step 5: Train and Upload First Model

```bash
# Train a model
make train

# Upload to HuggingFace Hub
make upload MODEL=models/mnist-relu-100-TIMESTAMP.npz ACC=95.4
```

**Note:** After upload, local files are automatically deleted. HuggingFace Hub becomes the source of truth.

## Step 6: Deploy to Railway

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

Go to Railway dashboard → Variables tab and set all variables:

```bash
# Database (Neon PRODUCTION branch connection string)
DATABASE_URL=postgresql+psycopg://user:pass@ep-prod-endpoint.neon.tech/neondb?sslmode=require

# HuggingFace Hub
HF_MODEL_REPO=your-username/hippo-models
DEFAULT_MODEL=your-model-name

# Optional (for private HF repos)
HUGGINGFACE_TOKEN=hf_...

# Production CORS (your frontend URLs)
ALLOWED_ORIGINS=https://your-frontend.vercel.app

# Optional
HF_CACHE_DIR=.hf_cache
```

**Note:** Copy the exact `DATABASE_URL` from your Neon dashboard. Railway will use this to connect to your Neon database.

### Run Database Migrations on Railway

After first deployment, run migrations:

```bash
# Option 1: Railway CLI
railway run alembic upgrade head

# Option 2: Railway dashboard
# Go to Deployments → Settings → Add "Deploy Command"
# Command: alembic upgrade head
```

## Step 7: Verify Deployment

### Check Health Endpoint

```bash
curl https://your-app.railway.app/healthz
```

Expected response:
```json
{
  "status": "healthy",
  "network_loaded": true,
  "database_connected": true
}
```

**What the health check verifies:**
- `status: "healthy"` - API is running
- `network_loaded: true` - ML model loaded from HuggingFace Hub
- `database_connected: true` - PostgreSQL database is accessible

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

**Database:**
- [ ] PostgreSQL database created (Neon or Railway)
- [ ] `DATABASE_URL` environment variable set
- [ ] Database migrations run (`alembic upgrade head`)
- [ ] Health endpoint returns `database_connected: true`

**ML Models:**
- [ ] At least one model uploaded to HuggingFace Hub
- [ ] `HF_MODEL_REPO` and `DEFAULT_MODEL` set correctly
- [ ] `HUGGINGFACE_TOKEN` set (if using private repo)
- [ ] Health endpoint returns `network_loaded: true`
- [ ] Test `/predict` endpoint with sample data
- [ ] Test `/activations` endpoint with sample data

**API Configuration:**
- [ ] Railway environment variables configured
- [ ] CORS `ALLOWED_ORIGINS` configured for frontend URLs
- [ ] Test `/healthz` endpoint - all checks pass
- [ ] Visit `/docs` - Swagger UI loads correctly
- [ ] Test vocabulary endpoints (if using database features)

## Troubleshooting

### "Database connection failed" (`database_connected: false`)

**Common causes with Neon:**

1. **Wrong connection string format**
   ```bash
   # ❌ Wrong (missing +psycopg)
   postgresql://user:pass@ep-xxx.neon.tech/neondb

   # ✅ Correct
   postgresql+psycopg://user:pass@ep-xxx.neon.tech/neondb?sslmode=require
   ```

2. **Neon database auto-suspended** (free tier)
   - Visit Neon dashboard to wake it up
   - First request after suspension may be slow

3. **Missing sslmode parameter**
   - Neon requires `?sslmode=require`

**Fix it:**
```bash
# Check Railway logs
railway logs

# Test connection locally
python -c "from db import engine; engine.connect()"

# Verify DATABASE_URL in Railway Variables tab
# Should match your Neon connection string exactly
```

### "Tables don't exist" errors

**Causes:**
- Database migrations not run
- Migrations run on wrong database

**Solutions:**
```bash
# Run migrations on Railway
railway run alembic upgrade head

# Verify migrations were applied
railway run python -c "from sqlalchemy import inspect, text; from db import engine; inspector = inspect(engine); print(inspector.get_table_names())"

# Check migration history
railway run alembic current
```

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
# IMPORTANT: Use Neon DEVELOPMENT branch for DATABASE_URL
DATABASE_URL=postgresql+psycopg://...@ep-dev-endpoint.neon.tech/neondb...
HF_MODEL_REPO=your-username/hippo-models
DEFAULT_MODEL=mnist-relu-100
HUGGINGFACE_TOKEN=hf_...  # Optional
```

**Database Isolation:**
- ✅ Local `.env` uses Neon `development` branch
- ✅ Railway uses Neon `production` branch (set in Railway dashboard)
- ✅ No manual switching needed - automatic based on environment
- ✅ `.env` is gitignored and never deployed to Railway

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

**Production:** https://your-app.up.railway.app

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
