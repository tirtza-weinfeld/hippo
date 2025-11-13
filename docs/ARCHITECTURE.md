# Architecture Overview

## Clean, Modular Structure

The project is organized for scalability and adding more neural network tutorials:

```
hippo/
├── api/                     # API layer
│   ├── main.py              # FastAPI app entry point
│   ├── state.py             # Global app state
│   └── routes/              # Route modules by domain
│       ├── network.py       # Neural network operations
│       └── mnist.py         # MNIST data operations
│
├── neural_networks/         # ML implementations
│   ├── core.py              # Basic feedforward network
│   └── mnist_loader.py      # MNIST dataset handler
│
├── schemas/                 # Pydantic models
│   ├── common.py            # Shared schemas
│   ├── network.py           # Network-related schemas
│   └── mnist.py             # MNIST schemas
│
└── data/                    # Auto-downloaded datasets
```

## Key Design Decisions

### 1. Async Training with Streaming
Instead of blocking for minutes, training uses **Server-Sent Events (SSE)** to stream progress:
- Frontend stays responsive
- Real-time progress updates
- Clean cancellation handling

### 2. Modular Routes
Each domain gets its own route module:
- `network.py` - Network lifecycle (create, train, predict, activations, state)
- `mnist.py` - Dataset operations (samples)
- Easy to add: `cnn.py`, `rnn.py`, etc.

### 3. Separated Concerns
- `neural_networks/` - Pure ML code, no HTTP
- `api/` - HTTP layer, delegates to neural_networks
- `schemas/` - Data validation contracts

### 4. State Management
Global state in `api/state.py`:
- Single network instance
- MNIST datasets loaded once
- Training lock to prevent concurrent training

## Adding New Neural Network Types

Want to add CNNs? Follow this pattern:

```python
# 1. Implement in neural_networks/cnn.py
class ConvolutionalNetwork:
    def __init__(self, ...): ...
    def forward(self, ...): ...

# 2. Create schemas in schemas/cnn.py
class CNNCreate(BaseModel): ...
class CNNOutput(BaseModel): ...

# 3. Create routes in api/routes/cnn.py
router = APIRouter(prefix="/cnn")

@router.post("/create")
def create_cnn(...): ...

# 4. Include in api/main.py
from api.routes import cnn
app.include_router(cnn.router)
```

## API Design Principles

### Essential Endpoints Only
- ✅ Create network
- ✅ Train (streaming)
- ✅ Predict
- ✅ Get activations (for visualization)
- ✅ Get state (for save/load)
- ✅ Get samples (for testing)
- ❌ Internal-only operations

### Streaming for Long Operations
Training takes minutes, so:
```
POST /network/train → SSE stream
data: {epoch: 1, accuracy_percent: 82.34}
data: {epoch: 2, accuracy_percent: 85.67}
...
data: {status: "completed"}
```

Frontend uses `EventSource`:
```javascript
const es = new EventSource('/network/train');
es.onmessage = (e) => updateProgressBar(JSON.parse(e.data));
```

### Type Safety Everywhere
- Pydantic validates all inputs
- Type hints on all functions
- `mypy --strict` compliance

## Code Quality

Following `.cursor/rules/python.mdc`:
- Modern Python 3.14+ syntax
- No `Union`, `Optional` - use `|` instead
- No wildcard imports
- Full docstrings
- `ruff` formatting
- `mypy --strict` type checking

## Next Steps

1. **Test the API**: Run `uvicorn api.main:app --reload`
2. **Connect Frontend**: Use provided example code in README
3. **Add More Networks**: Follow the pattern above
4. **Persist Models**: Add save/load endpoints using network state
