# Hippo - Neural Network Learning API

Backend inference API for neural networks trained locally.
Modern Python 3.14+ implementation with NumPy. Models are trained locally and served via FastAPI for frontend applications.

## Architecture

**Training**: Local Python scripts with detailed logging
**Storage**: Hugging Face Hub (versioned, public, efficient)
**API**: Inference-only (fast, lightweight, production-ready)

```
Local Training → Upload to HF Hub → API Downloads → Inference
```

## Features

- **Inference API**: Load pre-trained models from Hugging Face Hub
- **Real-time Predictions**: Get predictions with confidence scores
- **Visualization Support**: Access all layer activations for frontend visualization
- **MNIST Samples**: Fetch random samples for testing
- **Local Training**: Train models locally with full control

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### API Server (Inference Only)

```bash
# Set up environment
echo "HF_MODEL_REPO=your-username/hippo-models" >> .env
echo "DEFAULT_MODEL=mnist-relu-95" >> .env
echo "ALLOWED_ORIGINS=http://localhost:3000" >> .env

# Run the server
uvicorn api.main:app --reload
```

The API will be available at `http://localhost:8000`

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

### Local Training

```bash
# Train a new model
python training/cli_train.py \
    --sizes 784 100 10 \
    --activation relu \
    --epochs 30 \
    --learning-rate 0.01

# Upload to Hugging Face Hub
python training/cli_upload.py \
    --model-path models/mnist-relu-100.npz \
    --accuracy 95.4
```

See [`training/README.md`](training/README.md) for detailed training workflow.

## Project Structure

```
hippo/
├── api/                        # FastAPI application
│   ├── main.py                 # App entry point
│   └── routes/
│       ├── inference.py        # Neural network predictions & activations
│       └── vocabulary.py       # Word/definition management
│
├── training/                   # Local training scripts
│   ├── cli_train.py            # Train feedforward networks
│   └── cli_upload.py           # Upload models to HF Hub
│
├── hf_hub/                     # HuggingFace Hub integration
│   ├── model_manager.py        # Download & cache models
│   └── config.py               # Configuration
│
├── neural_networks/            # Core ML implementations
│   ├── core.py                 # NeuralNetwork class
│   └── mnist_loader.py         # MNIST dataset utilities
│
├── schemas/                    # Pydantic models (API contracts)
│   ├── inference.py            # Inference endpoints
│   └── vocabulary.py           # Vocabulary endpoints
│
├── db/                         # Database models
│   └── models/
│       └── vocabulary.py       # SQLAlchemy models
│
└── docs/                       # Documentation
    └── voc.md                  # Vocabulary database schema
```

## API Endpoints

**Full interactive documentation:** Visit `http://localhost:8000/docs` when server is running.

### Inference

#### Predict
```http
POST /predict
Content-Type: application/json

{
  "pixels": [0.0, 0.1, ..., 0.0]  // 784 values [0, 1]
}
```

Returns:
```json
{
  "predicted_digit": 7,
  "confidence": 0.95,
  "probabilities": [0.01, 0.02, ..., 0.95]
}
```

#### Get Activations
```http
POST /activations
Content-Type: application/json

{
  "pixels": [0.0, 0.1, ..., 0.0]
}
```

Returns activations for all layers (useful for visualization).

### Vocabulary Management

Full CRUD operations for words, definitions, examples, tags, and relationships.

**Main endpoints:**
- `GET /vocabulary/words` - List all words
- `POST /vocabulary/words` - Create new word
- `GET /vocabulary/words/{id}` - Get word details
- `PATCH /vocabulary/words/{id}` - Update word
- `DELETE /vocabulary/words/{id}` - Delete word

**Related endpoints:** `/vocabulary/definitions`, `/vocabulary/examples`, `/vocabulary/tags`, `/vocabulary/word-relations`

See `/docs` for complete API reference.

## Neural Network Implementation

1. **Feedforward**: `a = σ(w·a_prev + b)`
2. **Backpropagation**: Compute gradients using chain rule
3. **Training**: Stochastic gradient descent with mini-batches

## Training Locally

```python
from neural_networks import NeuralNetwork
from neural_networks.mnist_loader import load_data_wrapper

# Load MNIST
training_data, validation_data, test_data = load_data_wrapper()

# Create network (784 inputs, 100 hidden, 10 outputs)
network = NeuralNetwork(sizes=[784, 100, 10], activation="relu")

# Train
network.train(
    training_data=training_data,
    epochs=30,
    mini_batch_size=10,
    learning_rate=3.0,
    test_data=test_data
)

# Save
import numpy as np
np.savez_compressed(
    'model.npz',
    weights=[w.tolist() for w in network.weights],
    biases=[b.tolist() for b in network.biases],
    sizes=network.sizes,
    activation=network.activation_name
)
```

See [`docs/TRAINING.md`](docs/TRAINING.md) for complete training guide.

## Code Quality Standards

This project follows strict Python 3.14+ rules (see `.cursor/rules/python.mdc`):
- Full type hints on all functions
- Modern syntax (`|` not `Union`, `list[]` not `List`)
- Docstrings on all public functions
- No wildcard imports
- `ruff` for linting/formatting
- `mypy --strict` for type checking

## Environment Variables

```bash
# .env
HF_MODEL_REPO=your-username/hippo-models  # Your HF Hub repository
DEFAULT_MODEL=mnist-relu-95                # Model to load on startup
HUGGINGFACE_TOKEN=hf_...                   # For uploading models (optional for API)
ALLOWED_ORIGINS=http://localhost:3000      # CORS origins
```

## Learning Resources

- [3Blue1Brown Neural Networks Series](https://www.3blue1brown.com/topics/neural-networks)
- [Original Reference Code](https://github.com/3b1b/videos/tree/master/_2017/nn)
- [MNIST Dataset](http://yann.lecun.com/exdb/mnist/)

## Development

### Database Migrations

```bash
# Create a new migration
make migrate MSG='describe your changes'

# Apply migrations
make upgrade

# Rollback last migration
make downgrade
```
