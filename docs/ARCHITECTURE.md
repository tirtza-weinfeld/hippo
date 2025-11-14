# Architecture Overview - Inference API + Local Training

## Design Philosophy

**Separation of Concerns:**
- **Training**: Happens locally in Python scripts (slow, resource-intensive, learning-focused)
- **API**: Inference-only (fast, lightweight, production-ready)
- **Model Storage**: Hugging Face Hub (versioned, public, free, efficient)

## Project Structure

```
hippo/
├── api/                        # Inference-only FastAPI
│   ├── main.py                 # App entry, loads models from HF Hub
│   └── routes/
│       ├── inference.py        # POST /predict, POST /activations
│       └── mnist.py            # GET /mnist/samples
│
├── training/                   # Local training workflows
│   ├── train_mnist.py          # Train feedforward networks locally
│   ├── upload_to_hf.py         # Upload trained models to HF Hub
│   ├── experiments/            # Training experiments & notebooks
│   └── README.md               # Training guide
│
├── hf_hub/                     # Hugging Face Hub integration
│   ├── model_manager.py        # Download & cache models from HF Hub
│   └── config.py               # HF Hub configuration (repo IDs, etc.)
│
├── neural_networks/            # Core ML implementations
│   ├── core.py                 # NeuralNetwork class (pure NumPy)
│   └── mnist_loader.py         # MNIST dataset utilities
│
├── schemas/                    # Pydantic validation models
│   ├── inference.py            # PredictionInput, PredictionOutput, etc.
│   └── mnist.py                # MNISTSample, etc.
│
└── docs/
    ├── ARCHITECTURE.md         # This file
    ├── TRAINING.md             # Local training workflow
    └── API.md                  # API documentation
```

## Component Responsibilities

### 1. API Layer (`api/`)

**Purpose**: Serve pre-trained models for inference only

**Endpoints**:
```
POST /predict
  - Input: 784 pixels [0-1]
  - Output: Predicted digit, confidence, probabilities
  - Uses model loaded from HF Hub

POST /activations
  - Input: 784 pixels
  - Output: All layer activations (for visualization)

GET /mnist/samples
  - Output: Random MNIST test samples
  - For testing/demo purposes

GET /models
  - Output: List of available models from HF Hub
  - Metadata: architecture, accuracy, training info
```

**Model Loading**:
- On startup, download specified model from HF Hub
- Cache locally for fast inference
- No dynamic model creation or training

**State Management**:
- Single global model instance (loaded at startup)
- No training state (no locks, progress tracking, etc.)
- Stateless inference (no sessions)

### 2. Training Layer (`training/`)

**Purpose**: Local training scripts for learning & experimentation

**Workflow**:
```python
# 1. Train locally
python training/train_mnist.py \
    --sizes 784 100 10 \
    --activation relu \
    --epochs 30 \
    --learning-rate 3.0

# 2. Upload to HF Hub
python training/upload_to_hf.py \
    --model-path models/mnist-784-100-10-relu.npz \
    --name "MNIST Feedforward 784-100-10 ReLU" \
    --accuracy 95.4
```

**Features**:
- Detailed logging (training curves, metrics)
- Jupyter notebook integration for analysis
- Experiment tracking
- Model checkpointing
- No API dependencies (pure Python)

### 3. HF Hub Integration (`hf_hub/`)

**Purpose**: Bridge between local training and API inference

**Model Manager**:
```python
from hf_hub import ModelManager

# Download model from HF Hub
manager = ModelManager()
network = manager.load_model("username/hippo-mnist-relu-95")

# Upload new model
manager.upload_model(
    network=trained_network,
    name="mnist-relu-95",
    metadata={"accuracy": 95.4, "epochs": 30}
)
```

**Storage Format**:
```
your-hf-username/hippo-neural-networks/
├── mnist-784-30-10-sigmoid-92.npz      # Model weights/biases
├── mnist-784-30-10-sigmoid-92.json     # Metadata (architecture, accuracy)
├── mnist-784-100-10-relu-95.npz
├── mnist-784-100-10-relu-95.json
└── README.md                            # Model card
```

### 4. Neural Networks (`neural_networks/`)

**No changes** - Pure ML implementations, no HTTP concerns

## Data Flow

### Training Flow (Local)
```
1. Run training script
   ↓
2. NeuralNetwork trains on MNIST locally
   ↓
3. Save model as .npz (NumPy compressed)
   ↓
4. Upload to HF Hub with metadata
   ↓
5. Model available for API to download
```

### Inference Flow (API)
```
1. API starts → Downloads model from HF Hub
   ↓
2. User sends POST /predict request
   ↓
3. API runs feedforward (NumPy)
   ↓
4. Returns prediction
```

## Benefits of This Architecture

### For Learning
- ✅ Train interactively in Jupyter notebooks
- ✅ Detailed logging & visualization
- ✅ No API complexity during learning
- ✅ Full control over training process

### For API
- ✅ Lightweight (no training code)
- ✅ Fast startup (download cached models)
- ✅ Stateless & scalable
- ✅ Production-ready

### For Model Management
- ✅ Version control (Git-backed)
- ✅ Public sharing & portfolio
- ✅ Efficient storage (binary format)
- ✅ Free unlimited storage

## Migration from Current Design

**Removed**:
- ❌ `POST /network/create` - No dynamic creation
- ❌ `POST /network/train` - Training is local
- ❌ `POST /network/save`, `GET /network/saved`, `POST /network/load` - HF Hub replaces DB
- ❌ `db.py`, `models.py`, `init_db.py` - No database needed
- ❌ Neon PostgreSQL integration (saved for future user features)

**Added**:
- ✨ `training/` directory - Local training scripts
- ✨ `hf_hub/` module - HF Hub integration
- ✨ `GET /models` - List available models from HF Hub

**Kept**:
- ✅ `POST /predict` - Core inference
- ✅ `POST /activations` - Visualization support
- ✅ `GET /mnist/samples` - Test data
- ✅ `neural_networks/core.py` - ML implementation

## Environment Variables

```bash
# .env
HUGGINGFACE_TOKEN=hf_...           # HF Hub write access (for uploads)
HF_MODEL_REPO=username/hippo-models # Default model repository
DEFAULT_MODEL=mnist-relu-95         # Model to load on startup
ALLOWED_ORIGINS=https://...         # CORS origins
```

## Future Additions

When adding user accounts or custom features:

**Bring back Neon DB for**:
- User authentication
- User-specific model preferences
- Training history tracking
- Private model metadata

**Keep HF Hub for**:
- Actual model weights (efficient binary storage)
- Public model sharing
- Version control
