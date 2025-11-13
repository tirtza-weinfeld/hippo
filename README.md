# Neural Network Learning API

Backend API for learning neural networks following the [3Blue1Brown tutorial](https://www.3blue1brown.com/lessons/neural-networks).

Modern Python 3.14+ implementation with NumPy, designed as a clean backend for frontend applications.

## Features

- **Create Neural Networks**: Define custom architectures (layer sizes, activation functions)
- **Train on MNIST**: Learn handwritten digit recognition (0-9) with real-time progress
- **Real-time Predictions**: Get predictions with confidence scores
- **Visualization Support**: Access all layer activations for frontend visualization
- **MNIST Samples**: Fetch random samples for testing
- **Streaming Training**: Server-sent events for live training progress updates

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn api.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

## Project Structure

```
hippo/
├── api/
│   ├── main.py              # FastAPI application entry point
│   ├── state.py             # Global application state
│   └── routes/
│       ├── network.py       # Neural network endpoints
│       └── mnist.py         # MNIST dataset endpoints
├── neural_networks/
│   ├── core.py              # Neural network implementation
│   └── mnist_loader.py      # MNIST data handling
├── schemas/
│   ├── common.py            # Common schemas (health check)
│   ├── network.py           # Network-related schemas
│   └── mnist.py             # MNIST schemas
├── data/                    # MNIST dataset (auto-downloaded)
├── requirements.txt
└── README.md
```

## API Endpoints

### Health Check
```http
GET /healthz
```
Check if API is running and data is loaded.

### Network Management

#### Create Network
```http
POST /network/create
Content-Type: application/json

{
  "sizes": [784, 30, 10],
  "activation": "sigmoid"
}
```
Creates a neural network:
- Input: 784 neurons (28x28 MNIST images)
- Hidden: 30 neurons
- Output: 10 neurons (digits 0-9)

#### Get Network State
```http
GET /network/state
```
Returns current weights, biases, and configuration (large response).

### Training (with Real-time Progress)

```http
POST /network/train
Content-Type: application/json

{
  "epochs": 30,
  "mini_batch_size": 10,
  "learning_rate": 3.0,
  "use_test_data": true
}
```

Returns **Server-Sent Events (SSE)** stream:
```
data: {"epoch": 1, "total_epochs": 30, "test_accuracy": 8234, "test_total": 10000, "accuracy_percent": 82.34}

data: {"epoch": 2, "total_epochs": 30, "test_accuracy": 8567, "test_total": 10000, "accuracy_percent": 85.67}

...

data: {"status": "completed"}
```

**Frontend Example (EventSource):**
```javascript
const eventSource = new EventSource('http://localhost:8000/network/train');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.status === 'completed') {
    console.log('Training completed!');
    eventSource.close();
  } else {
    console.log(`Epoch ${data.epoch}/${data.total_epochs}: ${data.accuracy_percent}% accuracy`);
  }
};
```

### Predictions

```http
POST /network/predict
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

### Visualization

```http
POST /network/activations
Content-Type: application/json

{
  "pixels": [0.0, 0.1, ..., 0.0]
}
```
Returns activations for all layers (visualize what each layer "sees").

### MNIST Samples

```http
GET /mnist/samples?count=10&dataset=test
```
Get random MNIST samples. Datasets: `train`, `validation`, `test`.

## Neural Network Details

Following the 3Blue1Brown tutorial:

1. **Feedforward**: `a = σ(w·a_prev + b)`
2. **Backpropagation**: Compute gradients using chain rule
3. **Training**: Stochastic gradient descent with mini-batches

## Code Quality Standards

This project follows strict Python 3.14+ rules (see `.cursor/rules/python.mdc`):
- Full type hints on all functions
- Modern syntax (`|` not `Union`, `list[]` not `List`)
- Docstrings on all public functions
- No wildcard imports
- `ruff` for linting/formatting
- `mypy --strict` for type checking

## Extending for More Tutorials

The modular structure makes it easy to add new neural network tutorials:

```
neural_networks/
  ├── core.py              # Basic feedforward network
  ├── cnn.py               # Add CNNs here
  ├── rnn.py               # Add RNNs here
  └── gan.py               # Add GANs here

api/routes/
  ├── network.py           # Basic network routes
  ├── cnn_routes.py        # Add CNN routes here
  └── ...
```

## Learning Resources

- [3Blue1Brown Neural Networks Series](https://www.3blue1brown.com/topics/neural-networks)
- [Original Reference Code](https://github.com/3b1b/videos/tree/master/_2017/nn)
- [MNIST Dataset](http://yann.lecun.com/exdb/mnist/)

## Example Usage

```python
import requests

# 1. Create a network
requests.post("http://localhost:8000/network/create", json={
    "sizes": [784, 30, 10],
    "activation": "sigmoid"
})

# 2. Get test samples
samples = requests.get("http://localhost:8000/mnist/samples?count=5").json()

# 3. Make a prediction (before training - will be random)
response = requests.post("http://localhost:8000/network/predict", json={
    "pixels": samples["samples"][0]["pixels"]
})
print(f"Predicted: {response.json()['predicted_digit']}")
print(f"Actual: {samples['samples'][0]['label']}")

# 4. Train with streaming progress (use EventSource in browser)
# See frontend example above
```

## Next Steps for Your Frontend

1. **Create Network UI**: Form to specify layer sizes
2. **Training Progress**: Real-time progress bar using SSE
3. **Digit Drawing Canvas**: Let users draw digits for prediction
4. **Activation Visualization**: Show what each layer activates on
5. **Sample Gallery**: Display MNIST samples with predictions
