# Frontend Requirements for Neural Network Learning App

## Backend API

FastAPI backend at `http://localhost:8000` implementing neural network learning (3Blue1Brown tutorial).

**Dataset:** MNIST handwritten digits 0-9 (60,000 training, 10,000 test images)

---

## API Endpoints

### Health Check
```
GET /healthz
```
**Response:**
```json
{
  "status": "healthy",
  "network_loaded": boolean,
  "mnist_loaded": boolean
}
```

---

### Create Neural Network
```
POST /network/create
```
**Request Body:**
```json
{
  "sizes": [784, 30, 10],           // Array of layer sizes
  "activation": "sigmoid" | "relu"  // Activation function
}
```
**Response:**
```json
{
  "sizes": [784, 30, 10],
  "activation": "sigmoid",
  "weights": [[[...]]], // Nested arrays of all weights
  "biases": [[[]]]      // Nested arrays of all biases
}
```
**Behavior:** Creates new network with random weights. Calling this resets any existing trained network.

---

### Train Network
```
POST /network/train
```
**Request Body:**
```json
{
  "epochs": 30,              // How many times to see all 60K images
  "mini_batch_size": 10,     // Update weights after N images
  "learning_rate": 3.0,      // Weight adjustment magnitude
  "use_test_data": true      // Evaluate accuracy each epoch
}
```

**Response:** Server-Sent Events stream

**Stream format:**
```
data: {"epoch": 1, "total_epochs": 30, "test_accuracy": 8234, "test_total": 10000, "accuracy_percent": 82.34}

data: {"epoch": 2, "total_epochs": 30, "test_accuracy": 8567, "test_total": 10000, "accuracy_percent": 85.67}

data: {"status": "completed"}
```

**Critical Behavior:**
- Training **continues** from current weights (does NOT reset)
- To start fresh training: Call `POST /network/create` first
- Each epoch takes ~5-10 seconds
- Stream stays open until training completes

---

### Get Network State
```
GET /network/state
```
**Response:** Same as create response (all weights/biases)

**Note:** Large response. Only use for save/load functionality.

---

### Make Prediction
```
POST /network/predict
```
**Request Body:**
```json
{
  "pixels": [0.0, 0.1, ..., 0.0]  // 784 floats [0.0-1.0]
}
```
**Response:**
```json
{
  "predicted_digit": 7,              // 0-9
  "confidence": 0.95,                // 0.0-1.0
  "probabilities": [0.01, ..., 0.95] // 10 floats, one per digit
}
```

---

### Get Layer Activations
```
POST /network/activations
```
**Request Body:**
```json
{
  "pixels": [0.0, 0.1, ..., 0.0]  // 784 floats
}
```
**Response:**
```json
{
  "activations": [
    [0.1, 0.2, ...],  // Input layer (784 values)
    [0.5, 0.3, ...],  // Hidden layer (30 values)
    [0.1, 0.9, ...]   // Output layer (10 values)
  ],
  "layer_sizes": [784, 30, 10]
}
```
**Purpose:** Visualize which neurons activate for given input.

---

### Get MNIST Samples
```
GET /mnist/samples?count=10&dataset=test
```
**Query Parameters:**
- `count`: 1-100 (default: 10)
- `dataset`: "train" | "validation" | "test" (default: "test")

**Response:**
```json
{
  "samples": [
    {"pixels": [784 floats], "label": 7},
    {"pixels": [784 floats], "label": 3}
  ],
  "count": 10
}
```

---

## Error Responses

All errors return standard HTTP status codes:

- `400` - Bad request (validation failed)
- `404` - Network not created yet
- `409` - Training already in progress
- `503` - MNIST data not loaded

---

## Image Format

**MNIST images:**
- 28×28 grayscale pixels
- Flattened to 784 values
- Each value: 0.0 (black) to 1.0 (white)

**To display:** Render 28×28 grid, map [0, 1] to grayscale

**To capture user drawing:** Scale to 28×28, normalize to [0, 1]

---

## Features to Build

### 1. Network Configuration
- Input: Layer sizes (comma-separated, e.g., "784, 30, 10")
- Dropdown: Activation function (sigmoid/relu)
- Button: Create Network
- Display: Current network status

### 2. Training Interface
**Inputs:**
- Epochs: 1-100 (default 30)
- Mini-batch size: 1-1000 (default 10)
- Learning rate: 0.1-10.0 (default 3.0)
- Checkbox: Use test data

**Display:**
- Real-time progress: "Epoch X/Y"
- Live accuracy percentage
- Progress bar or indicator
- Disable training button while training

**Implementation:** Use EventSource or fetch with streaming

### 3. Sample Gallery
- Display 10-20 MNIST images as 28×28 grids
- Show label below each image
- Button: Load more samples
- Tabs/buttons: Switch between train/validation/test datasets
- Click sample → predict on it

### 4. Prediction Interface

**Option A: Drawing Canvas**
- 280×280px canvas (28×28 scaled up 10x)
- Mouse/touch drawing
- Clear button
- Predict button → send to `/network/predict`

**Option B: Click Sample**
- Click image from gallery
- Send to `/network/predict`

**Display Results:**
- Large predicted digit
- Confidence percentage
- Bar chart: All 10 probabilities (0-9)

### 5. Network Visualization (Optional)
- Visual representation of network layers
- Circles for neurons
- Lines connecting layers
- Highlight active neurons using `/network/activations`
- Color intensity = activation strength

### 6. Training History (Optional)
- Line chart: Accuracy vs epoch
- Store history during training stream
- Reset when creating new network

---

## CORS

Backend allows all origins by default. Configure specific origins in backend `.env`:
```
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## Expected User Flow

1. Create network (784, 30, 10)
2. Load sample images to see examples
3. Start training (30 epochs)
4. Watch live progress updates
5. After training, click sample → see prediction
6. Draw own digit → get prediction
7. Optionally train more (continues from current weights)
8. Or create new network (resets to start over)

---

## Key Concepts

**Epochs:** Number of complete passes through all 60,000 training images
- More epochs = more learning (but risk overfitting)

**Mini-batches:** Process N images, then update weights
- Balance between speed and stability

**Learning rate:** How aggressively to update weights
- Too high = unstable
- Too low = slow
- 3.0 works well for MNIST

**Training behavior:** Cumulative, not reset
- First train: Random weights → 90% accuracy
- Second train: 90% → 92% accuracy (continues learning)
- Create network: Resets to random weights

---

## Success Criteria

✅ Create and configure neural networks
✅ Train with live progress updates
✅ Display MNIST sample images
✅ Get predictions on samples and drawings
✅ Show prediction confidence
✅ Clean, intuitive UI
✅ Proper error handling

---

## Tech Stack

**Backend:** Python 3.14, FastAPI, NumPy
**Algorithm:** Feedforward network with backpropagation
**Following:** 3Blue1Brown neural networks tutorial


see https://github.com/tirtza-weinfeld/site/blob/main/app/n/ai/llm.tsx https://github.com/tirtza-weinfeld/site/blob/main/app/n/ai/tokenization.tsx  https://github.com/tirtza-weinfeld/site/blob/main/app/n/ai/self-attention.tsx  for animation ideas but do better and more modern 