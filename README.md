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

**For production deployment:** See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for Railway setup.

### Local Training

```bash
# Train a new model
python training/train_mnist.py \
    --sizes 784 100 10 \
    --activation relu \
    --epochs 30 \
    --learning-rate 3.0

# Upload to Hugging Face Hub
python training/upload_to_hf.py \
    --model-path models/mnist-784-100-10-relu.npz \
    --name "MNIST ReLU 95% accuracy" \
    --accuracy 95.4
```

See [`training/README.md`](training/README.md) for detailed training workflow.

## Project Structure

```
hippo/
├── api/                        # Inference-only FastAPI
│   ├── main.py                 # App entry point
│   └── routes/
│       ├── inference.py        # Prediction & activations
│       └── mnist.py            # MNIST samples
│
├── training/                   # Local training scripts
│   ├── train_mnist.py          # Train feedforward networks
│   ├── upload_to_hf.py         # Upload models to HF Hub
│   └── README.md               # Training guide
│
├── hf_hub/                     # HF Hub integration
│   ├── model_manager.py        # Download & cache models
│   └── config.py               # Configuration
│
├── neural_networks/            # Core ML implementations
│   ├── core.py                 # NeuralNetwork class
│   └── mnist_loader.py         # MNIST utilities
│
├── schemas/                    # Pydantic models
│   ├── inference.py            # API contracts
│   └── mnist.py                # MNIST schemas
│
└── docs/
    ├── ARCHITECTURE.md         # Architecture overview
    ├── DEPLOYMENT.md           # Railway + HF Hub deployment
    ├── TRAINING.md             # Training workflow
    └── API.md                  # API documentation
```

## API Endpoints

### Models

#### List Available Models
```http
GET /models
```
Returns list of available models from Hugging Face Hub.

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

#### Get Activations (for Visualization)
```http
POST /activations
Content-Type: application/json

{
  "pixels": [0.0, 0.1, ..., 0.0]
}
```

Returns activations for all layers to visualize what each layer "sees".

### MNIST Samples

```http
GET /mnist/samples?count=10&dataset=test
```

Get random MNIST samples for testing. Datasets: `train`, `validation`, `test`.

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

## Example Frontend Integration

```javascript
// 1. Get test samples
const samples = await fetch('http://localhost:8000/mnist/samples?count=5')
  .then(r => r.json());

// 2. Make a prediction
const prediction = await fetch('http://localhost:8000/predict', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({pixels: samples.samples[0].pixels})
}).then(r => r.json());

console.log(`Predicted: ${prediction.predicted_digit}`);
console.log(`Actual: ${samples.samples[0].label}`);
console.log(`Confidence: ${prediction.confidence}`);
```

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

## Next Steps

### For Learning
1. Run local training scripts
2. Experiment with different architectures
3. Upload your best models to HF Hub
4. Share your progress publicly

### For Frontend Development
1. **Model Selection**: UI to choose from available models
2. **Digit Drawing Canvas**: Let users draw digits for prediction
3. **Activation Visualization**: Show what each layer activates on
4. **Sample Gallery**: Display MNIST samples with predictions

## Future Extensions

The modular structure makes it easy to add new neural network types:

```
neural_networks/
  ├── core.py              # Basic feedforward network ✓
  ├── cnn.py               # Convolutional networks (future)
  ├── rnn.py               # Recurrent networks (future)
  └── gan.py               # Generative adversarial networks (future)
```

Each new network type gets its own route module:
```
api/routes/
  ├── inference.py         # Basic feedforward ✓
  ├── cnn.py               # CNN routes (future)
  └── rnn.py               # RNN routes (future)
```
