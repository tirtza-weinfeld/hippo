# Training Guide

This guide explains how to train neural networks locally and deploy them via HuggingFace Hub.

## Quick Start

### 1. Train a Model

```bash
make train
```

This will:
- Load MNIST dataset
- Train a network with default settings (784→100→10, ReLU, 30 epochs)
- Save the model to `models/`
- **Prompt you to upload to HuggingFace Hub**
- **Prompt you to update .env**
- **Prompt you to start API locally**

**Example output:**
```
Loading MNIST dataset...

Creating network: [784, 100, 10]
Activation: relu

Training for 30 epochs...
Learning rate: 0.01
Mini-batch size: 10
--------------------------------------------------
Epoch 1: 9132 / 10000
Epoch 2: 9287 / 10000
...
Epoch 30: 9618 / 10000
--------------------------------------------------

✓ Training complete!
Final accuracy: 96.18%
✓ Model saved to: models/mnist-relu-100-20251114_171943.npz
  Size: 598.2 KB

==================================================
Upload model to HuggingFace Hub? (y/n): y
Model description (optional, press Enter to skip):

Uploading mnist-relu-100-20251114_171943 to tessaw/hippo-models...
✓ Uploaded mnist-relu-100-20251114_171943.npz
✓ Uploaded mnist-relu-100-20251114_171943.json
✓ Uploaded README.md

✓ Upload complete!
View your model: https://huggingface.co/tessaw/hippo-models

==================================================
Update DEFAULT_MODEL in .env to mnist-relu-100-20251114_171943? (y/n): y
✓ Updated .env: DEFAULT_MODEL=mnist-relu-100-20251114_171943

==================================================
Start API locally to test? (y/n): y

✓ Starting API server...
API will be available at: http://localhost:8000
Interactive docs: http://localhost:8000/docs
```

### 2. Custom Training

Train with custom architecture:

```bash
make train ARGS='--sizes 784 200 10 --epochs 50 --learning-rate 0.5'
```

**Options:**
- `--sizes` - Layer architecture (e.g., `784 128 64 10`)
- `--activation` - `sigmoid` or `relu`
- `--epochs` - Number of training epochs
- `--learning-rate` - Learning rate (0.1-3.0)
- `--mini-batch-size` - Mini-batch size (default: 10)
- `--seed` - Random seed for reproducibility

## Training Workflow

```
┌─────────────────┐
│  make train     │ ← Run training command
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Train network   │ ← Automatic MNIST loading + training
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Save locally    │ ← models/mnist-*.npz + .json
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Upload to HF?   │ ← Interactive prompt (y/n)
└────────┬────────┘
         │ y
         ▼
┌─────────────────┐
│ Upload to Hub   │ ← Automatic upload + cleanup
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update .env?    │ ← Set DEFAULT_MODEL (y/n)
└────────┬────────┘
         │ y
         ▼
┌─────────────────┐
│ Start API?      │ ← Test locally (y/n)
└────────┬────────┘
         │ y
         ▼
┌─────────────────┐
│ API running     │ ← http://localhost:8000
└─────────────────┘
```

## HuggingFace Hub Setup

### First Time Only

```bash
# Install HuggingFace CLI
pip install huggingface-hub

# Login and get token
huggingface-cli login

# Add to .env
echo "HUGGINGFACE_TOKEN=hf_..." >> .env
echo "HF_MODEL_REPO=your-username/hippo-models" >> .env
```

### Creating HF Repository

1. Visit https://huggingface.co/new
2. Create repository: `your-username/hippo-models`
3. Can be public or private
4. Add repo to `.env`: `HF_MODEL_REPO=your-username/hippo-models`

## Model Files

Each trained model creates two files:

```
models/
├── mnist-relu-100-TIMESTAMP.npz    # Model weights/biases
└── mnist-relu-100-TIMESTAMP.json   # Training metadata
```

**.npz format (NumPy compressed):**
```python
{
    "sizes": [784, 100, 10],
    "activation": "relu",
    "num_layers": 3,
    "weight_0": array(...),  # Input → Hidden
    "weight_1": array(...),  # Hidden → Output
    "bias_0": array(...),
    "bias_1": array(...)
}
```

**.json format (metadata):**
```json
{
  "training_config": {
    "sizes": [784, 100, 10],
    "activation": "relu",
    "epochs": 30,
    "learning_rate": 0.01,
    "mini_batch_size": 10
  },
  "final_accuracy": 96.18
}
```

**After upload to HuggingFace Hub, local files are deleted** (Hub becomes source of truth).

## Manual Upload (if needed)

If you skip the automatic upload prompt:

```bash
make upload MODEL=models/mnist-relu-100-TIMESTAMP.npz ACC=96.18
```

This will:
- Upload `.npz` and `.json` to HuggingFace Hub
- Create model card (README.md)
- Delete local files on success

## Testing API Locally

### Start API Server

```bash
make start
```

### Test Endpoints

**Health check:**
```bash
curl http://localhost:8000/healthz
```

**Prediction:**
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"pixels": [0.0, 0.0, ..., 0.0]}'  # 784 values
```

**Interactive docs:**
Visit http://localhost:8000/docs

## Deployment to Railway

Once your model is tested locally:

```bash
# Deploy to Railway
railway up

# Update DEFAULT_MODEL in Railway dashboard
# Redeploy automatically downloads model from HF Hub
```

Railway startup:
1. Checks `.hf_cache/` for model
2. If not cached → downloads from HuggingFace Hub
3. Loads model into memory
4. Ready to serve predictions

## Training Tips

### Quick Test Model
```bash
make train-small  # 784→30→10, sigmoid, 10 epochs (~2 min)
```

### High Accuracy Model
```bash
make train ARGS='--sizes 784 200 10 --activation relu --epochs 50'
```

### Reproducible Results
```bash
make train ARGS='--seed 42'
```

### Common Architectures

| Architecture | Accuracy | Training Time | Use Case |
|--------------|----------|---------------|----------|
| 784→30→10 (sigmoid) | ~92% | 2-3 min | Quick testing |
| 784→100→10 (relu) | ~96% | 5-7 min | Good baseline |
| 784→200→10 (relu) | ~97% | 10-15 min | High accuracy |
| 784→128→64→10 (relu) | ~97-98% | 15-20 min | Deep network |

## Troubleshooting

### "HF_MODEL_REPO environment variable not set"
Add to `.env`:
```bash
HF_MODEL_REPO=your-username/hippo-models
```

### "HUGGINGFACE_TOKEN environment variable not set"
```bash
huggingface-cli login
# Or manually add to .env
```

### Upload fails
Files are kept in `models/` directory. Try manual upload:
```bash
make upload MODEL=models/your-model.npz ACC=95.4
```

### API won't start - model not found
```bash
# Check .env has correct model name
cat .env | grep DEFAULT_MODEL

# Verify model exists on HF Hub
# Visit: https://huggingface.co/your-username/hippo-models
```

## Next Steps

- **Architecture overview:** `docs/introduction.md`
- **Deployment guide:** `docs/DEPLOYMENT.md`
- **Training concepts:** `docs/TRAINING_CONCEPTS.md`

## Quick Reference

```bash
# Train default model (interactive prompts)
make train

# Train custom architecture
make train ARGS='--sizes 784 200 10 --epochs 50'

# Train small/fast model
make train-small

# Upload manually
make upload MODEL=models/my-model.npz ACC=95.4

# Start API locally
make start

# Deploy to Railway
railway up
```

The training script handles everything - just run `make train` and follow the prompts!
