# Neural Network Training: How It Works

This document explains how training works in the Hippo neural network implementation, from high-level concepts to implementation details.

## Table of Contents

- [High-Level Overview](#high-level-overview)
- [The Core Training Loop](#the-core-training-loop)
- [Backpropagation: The Heart of Learning](#backpropagation-the-heart-of-learning)
- [Gradient Descent: Updating Weights](#gradient-descent-updating-weights)
- [API Integration: Streaming Progress](#api-integration-streaming-progress)
- [Two-Tier Logging System](#two-tier-logging-system)
- [Mathematical Foundation](#mathematical-foundation)
- [Example Training Session](#example-training-session)
- [Code References](#code-references)

## High-Level Overview

The neural network uses **Stochastic Gradient Descent (SGD)** with mini-batches. The training process:

1. **Shuffle data**  prevents learning order patterns
2. **Split into mini-batches**  balances speed vs accuracy
3. **For each mini-batch:**
   - Run backpropagation on each sample
   - Average the gradients
   - Update weights and biases
4. **Evaluate accuracy** after each epoch
5. **Repeat** for specified number of epochs

## The Core Training Loop

Located in `neural_networks/core.py:86-130`, the `train()` method orchestrates everything:

```python
def train(
    self,
    training_data: list[tuple[NDArrayFloat, NDArrayFloat]],
    epochs: int,
    mini_batch_size: int,
    learning_rate: float,
    test_data: list[tuple[NDArrayFloat, NDArrayFloat]] | None = None,
) -> list[dict[str, int | float]]:
```

### Training Algorithm

**For each epoch:**
- Shuffle training data randomly
- Split data into mini-batches of specified size
- Process each mini-batch sequentially
- Optionally evaluate accuracy on test data
- Record metrics in history

**Mini-batch processing:**
- Each mini-batch updates the network weights once
- Uses averaged gradients from all samples in the batch

### Pseudocode

```python
for epoch in range(epochs):
    # Shuffle to avoid learning order
    random.shuffle(training_data)

    # Split into mini-batches
    mini_batches = [training_data[k:k+mini_batch_size]
                   for k in range(0, len(training_data), mini_batch_size)]

    # Update weights for each mini-batch
    for mini_batch in mini_batches:
        self._update_mini_batch(mini_batch, learning_rate)

    # Evaluate progress
    if test_data:
        accuracy = self.evaluate(test_data)
```

## Backpropagation: The Heart of Learning

The `_backprop()` method (`neural_networks/core.py:177-218`) implements the learning algorithm using the chain rule from calculus.

### 1. Forward Pass (Compute Outputs)

```python
activation = x  # Input
activations = [x]  # Store all activations
zs = []  # Store pre-activation values

for bias, weight in zip(self.biases, self.weights):
    z = weight @ activation + bias  # Linear combination
    zs.append(z)
    activation = sigmoid(z)  # Apply activation function
    activations.append(activation)
```

**What's happening:**
- Compute the weighted sum plus bias for each neuron
- Apply activation function (sigmoid or ReLU)
- Store both `z` (pre-activation) and `activation` for backward pass

### 2. Backward Pass (Compute Gradients)

**Output layer error:**
```python
# How wrong was the output? (cost derivative)
# How fast is the activation changing? (sigmoid derivative)
delta = (output - target) * sigmoid_derivative(z_last)
```

**Propagate error backward through hidden layers:**
```python
for layer in range(num_layers-2, 0, -1):
    # Flow error backward through weights (transpose)
    # Multiply by activation derivative (chain rule)
    delta = (weights[layer].T @ delta) * sigmoid_derivative(z[layer])

    # Gradients are:
    nabla_bias = delta
    nabla_weight = delta @ previous_activation.T
```

**Key insight:** Each layer's error depends on the next layer's error, propagated backward through the network using the transpose of weights and the chain rule.

### Complete Implementation

From `neural_networks/core.py:177-218`:

```python
def _backprop(
    self, x: NDArrayFloat, y: NDArrayFloat
) -> tuple[list[NDArrayFloat], list[NDArrayFloat]]:
    """Return tuple (nabla_b, nabla_w) representing gradient for cost function C_x.

    nabla_b and nabla_w are layer-by-layer lists of numpy arrays, similar
    to self.biases and self.weights.
    """
    nabla_b: list[NDArrayFloat] = [np.zeros(b.shape) for b in self.biases]
    nabla_w: list[NDArrayFloat] = [np.zeros(w.shape) for w in self.weights]

    # Forward pass
    activation = x
    activations: list[NDArrayFloat] = [x]
    zs: list[NDArrayFloat] = []

    for b, w in zip(self.biases, self.weights):
        z = w @ activation + b
        zs.append(z)
        activation = self._activation(z)
        activations.append(activation)

    # Backward pass
    delta = self._cost_derivative(activations[-1], y) * self._activation_derivative(zs[-1])
    nabla_b[-1] = delta
    nabla_w[-1] = delta @ activations[-2].T

    for layer in range(2, self.num_layers):
        z = zs[-layer]
        sp = self._activation_derivative(z)
        delta = (self.weights[-layer + 1].T @ delta) * sp
        nabla_b[-layer] = delta
        nabla_w[-layer] = delta @ activations[-layer - 1].T

    return nabla_b, nabla_w
```

## Gradient Descent: Updating Weights

The `_update_mini_batch()` method (`neural_networks/core.py:147-175`) applies the gradients:

### Algorithm

1. **Initialize gradient accumulators:**
   ```python
   nabla_b = [np.zeros(b.shape) for b in self.biases]
   nabla_w = [np.zeros(w.shape) for w in self.weights]
   ```

2. **Accumulate gradients from all samples in mini-batch:**
   ```python
   for x, y in mini_batch:
       delta_nabla_b, delta_nabla_w = self._backprop(x, y)
       nabla_b = [nb + dnb for nb, dnb in zip(nabla_b, delta_nabla_b)]
       nabla_w = [nw + dnw for nw, dnw in zip(nabla_w, delta_nabla_w)]
   ```

3. **Apply averaged gradients (gradient descent):**
   ```python
   learning_rate_adjusted = learning_rate / len(mini_batch)
   self.weights = [w - learning_rate_adjusted * nw
                   for w, nw in zip(self.weights, nabla_w)]
   self.biases = [b - learning_rate_adjusted * nb
                  for b, nb in zip(self.biases, nabla_b)]
   ```

**Key insight:** Averaging gradients from a mini-batch is more stable than updating after every single sample (online learning) and faster than computing gradients for the entire dataset (batch learning).

## API Integration: Streaming Progress

The API (`api/routes/network.py:75-151`) exposes training via Server-Sent Events (SSE) for real-time progress updates:

### Endpoint

```
POST /network/train
```

### Request Body

```json
{
  "epochs": 30,
  "mini_batch_size": 10,
  "learning_rate": 3.0,
  "use_test_data": true
}
```

### Implementation

```python
@router.post("/train")
async def train_network(config: TrainingConfig):
    async def train_with_progress() -> AsyncGenerator[str, None]:
        state.is_training = True
        try:
            for epoch in range(config.epochs):
                # Shuffle and create mini-batches
                np.random.shuffle(state.training_data)
                mini_batches = [...]

                # Train on mini-batches
                for mini_batch in mini_batches:
                    state.network._update_mini_batch(mini_batch, config.learning_rate)
                    await asyncio.sleep(0)  # Yield control to event loop

                # Evaluate and send progress
                progress = TrainingProgress(...)
                yield f"data: {progress.model_dump_json()}\n\n"
        finally:
            state.is_training = False

    return StreamingResponse(train_with_progress(), media_type="text/event-stream")
```

### Progress Updates

After each epoch, the API streams a JSON object:

```json
{
  "epoch": 1,
  "total_epochs": 30,
  "accuracy": 8234,
  "accuracy_percent": 82.34,
  "total_test_samples": 10000
}
```

This allows the frontend to show live training progress without blocking.

## Two-Tier Logging System

The codebase implements a sophisticated two-tier approach:

### Production Mode: `NeuralNetwork`

Located in `neural_networks/core.py`:
- Fast, minimal overhead
- Returns only epoch-level accuracy
- Used by the API for production training
- No file logging, just in-memory metrics

### Learning Mode: `LoggedNeuralNetwork`

Located in `neural_networks/logged_network.py`:
- Wraps `NeuralNetwork` without modifying it
- Writes comprehensive logs to `logs/training_YYYYMMDD_HHMMSS.jsonl`
- Perfect for Jupyter notebook analysis

### What Gets Logged

**Every epoch:**
- Epoch start/end timestamps
- Weight snapshots (mean, std, min, max per layer)
- Test accuracy and duration
- Example:
  ```json
  {"type": "epoch_end", "epoch": 1, "test_accuracy": 8234, "accuracy_percent": 82.34}
  ```

**Every 100 mini-batches:**
- Gradient statistics (mean, max for weights and biases)
- Batch index and size
- Example:
  ```json
  {"type": "mini_batch", "epoch": 1, "batch_idx": 0, "gradient_stats": {...}}
  ```

**Training completion:**
- Total duration
- Session ID for tracking
- Summary statistics (final/best accuracy, improvement)

### Log File Format

- JSONL (JSON Lines) format
- Each line is a complete JSON object
- Stored at: `logs/training_YYYYMMDD_HHMMSS.jsonl`
- Can be parsed line-by-line for analysis

### Usage

```python
from neural_networks.logged_network import LoggedNeuralNetwork
from neural_networks import MNISTLoader

training_data, _, test_data = MNISTLoader.load_data()
network = LoggedNeuralNetwork([784, 30, 10])

network.train(
    training_data=training_data,
    epochs=30,
    mini_batch_size=10,
    learning_rate=3.0,
    test_data=test_data
)
# Logs saved to: logs/training_YYYYMMDD_HHMMSS.jsonl
```

## Mathematical Foundation

### The Core Update Rule

```
weight_new = weight_old - (learning_rate / batch_size) * gradient
```

Where:
- **gradient** = Cost/weight (partial derivative of cost with respect to weight)
- **learning_rate** controls step size (too high  unstable, too low  slow)
- **batch_size** averaging reduces noise

### Cost Function (Quadratic)

```python
Cost = (1/2) * ||output - target||
Derivative = output - target
```

Implementation in `neural_networks/core.py:251-265`:

```python
def _cost_derivative(self, output_activations: NDArrayFloat, y: NDArrayFloat) -> NDArrayFloat:
    """Return vector of partial derivatives C_x/a for output activations."""
    return output_activations - y
```

### Activation Functions

#### Sigmoid

```python
(z) = 1 / (1 + e^(-z))
'(z) = (z) * (1 - (z))
```

Implementation (`neural_networks/core.py:220-234`):

```python
def _sigmoid(z: NDArrayFloat) -> NDArrayFloat:
    """Sigmoid activation function."""
    return 1.0 / (1.0 + np.exp(-z))

def _sigmoid_derivative(z: NDArrayFloat) -> NDArrayFloat:
    """Derivative of sigmoid function."""
    return _sigmoid(z) * (1 - _sigmoid(z))
```

#### ReLU

```python
ReLU(z) = max(0, z)
ReLU'(z) = 1 if z > 0 else 0
```

Implementation (`neural_networks/core.py:236-249`):

```python
def _relu(z: NDArrayFloat) -> NDArrayFloat:
    """ReLU activation function."""
    return np.maximum(0, z)

def _relu_derivative(z: NDArrayFloat) -> NDArrayFloat:
    """Derivative of ReLU function."""
    return (z > 0).astype(float)
```

## Example Training Session

### Basic Usage

```python
from neural_networks import NeuralNetwork, MNISTLoader

# Load MNIST dataset
training_data, validation_data, test_data = MNISTLoader.load_data()

# Create network: 784 inputs (2828 MNIST), 30 hidden, 10 outputs (digits 0-9)
network = NeuralNetwork([784, 30, 10])

# Train for 30 epochs
history = network.train(
    training_data=training_data,  # 50,000 MNIST images
    epochs=30,                     # Full passes through data
    mini_batch_size=10,            # 10 images per gradient update
    learning_rate=3.0,             # Step size
    test_data=test_data            # 10,000 images for evaluation
)

# Check final accuracy
final_accuracy = history[-1]["test_accuracy"]
print(f"Final accuracy: {final_accuracy}/10000 = {final_accuracy/100:.2f}%")
```

### What Happens

- **50,000 training samples**  **10 per batch** = **5,000 weight updates per epoch**
- **5,000 updates**  **30 epochs** = **150,000 total gradient descent steps**
- After each epoch, tests on **10,000 held-out images** to measure progress
- Typically achieves **~95% accuracy** on MNIST

### Via API

```bash
# Create network
curl -X POST http://localhost:8000/network/create \
  -H "Content-Type: application/json" \
  -d '{"sizes": [784, 30, 10]}'

# Load MNIST data
curl -X POST http://localhost:8000/mnist/load

# Train with streaming progress
curl -X POST http://localhost:8000/network/train \
  -H "Content-Type: application/json" \
  -d '{
    "epochs": 30,
    "mini_batch_size": 10,
    "learning_rate": 3.0,
    "use_test_data": true
  }'
```

## Code References

### Core Training Components

| Component | Location | Description |
|-----------|----------|-------------|
| Main training loop | `neural_networks/core.py:86-130` | `train()` method |
| Mini-batch updates | `neural_networks/core.py:147-175` | `_update_mini_batch()` method |
| Backpropagation | `neural_networks/core.py:177-218` | `_backprop()` method |
| Sigmoid activation | `neural_networks/core.py:220-234` | `_sigmoid()` and derivative |
| ReLU activation | `neural_networks/core.py:236-249` | `_relu()` and derivative |
| Cost derivative | `neural_networks/core.py:251-265` | `_cost_derivative()` method |
| Evaluation | `neural_networks/core.py:132-145` | `evaluate()` method |

### API Components

| Component | Location | Description |
|-----------|----------|-------------|
| Training endpoint | `api/routes/network.py:75-151` | `POST /network/train` |
| Training config | `schemas/network.py` | `TrainingConfig` model |
| Progress updates | `schemas/network.py` | `TrainingProgress` model |

### Logging Components

| Component | Location | Description |
|-----------|----------|-------------|
| Logged network | `neural_networks/logged_network.py` | `LoggedNeuralNetwork` wrapper |
| Training logger | `neural_networks/training_logger.py` | JSONL logging utilities |

## Architecture Diagram

```
User Request (POST /network/train)
    
API Layer (FastAPI)
      Validates state
      Manages async execution
      Streams progress via SSE
    
NeuralNetwork.train() [or LoggedNeuralNetwork.train()]
    
For each epoch:
      Shuffle training data
      Create mini-batches
      For each mini-batch:
          _update_mini_batch()
             Accumulate gradients via _backprop()
                Forward pass (compute activations)
                Backward pass (compute gradients)
             Apply averaged gradients to weights/biases
          Optional: Log gradient statistics
    
Evaluate on test data
    
Return/stream metrics
```

## Key Insights

1. **Mini-batch SGD balances speed and stability** - Pure SGD (batch size 1) is noisy, full batch gradient descent is slow. Mini-batches give the best of both.

2. **Backpropagation is just the chain rule** - The "magic" of neural networks is systematic application of calculus to compute gradients efficiently.

3. **Shuffling matters** - Without shuffling, the network might learn patterns in the data ordering rather than the actual patterns in the data.

4. **Learning rate is critical** - Too high and training diverges, too low and it takes forever. Typical values: 0.01 to 10.0.

5. **The architecture follows the math** - This implementation prioritizes clarity over performance, making it perfect for learning how neural networks actually work.

---

This implementation follows the [3Blue1Brown neural network tutorial series](https://www.3blue1brown.com/topics/neural-networks) and provides both production-ready performance and learning-friendly introspection capabilities.
