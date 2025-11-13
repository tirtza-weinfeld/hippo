# Learning Mode: See What's Happening Inside

For learning purposes, you can log everything that happens during training and visualize it in Jupyter notebooks.

## Quick Start

### 1. Train with Logging

```python
from neural_networks.logged_network import LoggedNeuralNetwork
from neural_networks import MNISTLoader

# Load data
training_data, _, test_data = MNISTLoader.load_data()

# Use LoggedNeuralNetwork instead of NeuralNetwork
network = LoggedNeuralNetwork([784, 30, 10])

# Train - logs everything automatically
network.train(
    training_data=training_data,
    epochs=30,
    mini_batch_size=10,
    learning_rate=3.0,
    test_data=test_data
)

# Logs saved to: logs/training_YYYYMMDD_HHMMSS.jsonl
```

### 2. Analyze in Jupyter

```bash
# Install visualization libs (if not already)
pip install jupyter matplotlib seaborn

# Start Jupyter
jupyter notebook notebooks/analyze_training.ipynb
```

### 3. Run Example

```bash
python example_with_logging.py
```

## What Gets Logged

### Every Epoch:
- **Epoch start/end** - Timing and progress
- **Weight snapshots** - Mean, std, min, max for each layer
- **Test accuracy** - How well the network performs
- **Duration** - How long each epoch took

### Every 100 Mini-Batches:
- **Gradient magnitudes** - How much weights are changing
- **Bias/weight gradients** - Mean and max values

### End of Training:
- **Summary statistics** - Overall performance
- **Total duration** - Complete training time
- **Session ID** - Unique identifier for this run

## What You Can Learn

### 1. Accuracy Over Time
See how the network improves:
- Does it plateau?
- Is it still learning?
- Is the learning rate too high/low?

### 2. Weight Evolution
Watch weights change:
- Are they exploding or vanishing?
- Do they stabilize?
- Which layers change most?

### 3. Gradient Behavior
Understand the learning process:
- Large gradients = big changes (early training)
- Small gradients = fine-tuning (later training)
- Zero gradients = stuck (problem!)

### 4. Training Time
Optimize your workflow:
- Which epochs are slow?
- Is performance consistent?
- How long for X epochs?

## File Structure

```
logs/
  training_20250113_143022.jsonl    # Raw logs (JSON lines)

notebooks/
  analyze_training.ipynb             # Jupyter analysis notebook

neural_networks/
  logged_network.py                  # Wrapper with logging
  training_logger.py                 # Logger implementation
```

## Log Format (JSONL)

Each line is a JSON object:

```json
{"type": "epoch_start", "epoch": 1, "total_epochs": 30, "timestamp": "2025-01-13T14:30:22"}
{"type": "mini_batch", "epoch": 1, "batch_idx": 0, "gradient_stats": {...}}
{"type": "weight_snapshot", "epoch": 1, "layers": [{...}, {...}]}
{"type": "epoch_end", "epoch": 1, "test_accuracy": 8234, "accuracy_percent": 82.34}
```

## Visualizations in Notebook

1. **Accuracy Curve** - Line plot of accuracy vs epoch
2. **Weight Evolution** - How weights change per layer
3. **Gradient Magnitudes** - Learning intensity over time
4. **Training Time** - Bar chart and histogram
5. **Summary Table** - Key statistics

## Comparison: Regular vs Logged

### Regular (Production)
```python
from neural_networks import NeuralNetwork

network = NeuralNetwork([784, 30, 10])
network.train(...)  # Fast, no logging
```

### Logged (Learning)
```python
from neural_networks.logged_network import LoggedNeuralNetwork

network = LoggedNeuralNetwork([784, 30, 10])
network.train(...)  # Slower, full logs
```

**Key difference:** `LoggedNeuralNetwork` is a wrapper. The core code stays clean!

## Tips

### For Fast Experiments
```python
# Use subset of data
network.train(training_data[:1000], epochs=5, ...)
```

### For Deep Analysis
```python
# Full dataset, more epochs
network.train(training_data, epochs=50, ...)
```

### Multiple Experiments
```python
# Each run creates a new log file with timestamp
# Compare different:
# - Learning rates
# - Network architectures
# - Activation functions
```

## Advanced: Custom Logging

Access the logger directly:

```python
network = LoggedNeuralNetwork([784, 30, 10])

# Access logger
logger = network.logger

# After training, get summary
summary = logger.get_summary()
print(summary)

# Log custom events
logger.log_activation_pattern(
    sample_idx=0,
    activations=network.get_all_activations(sample_input),
    label=7,
    prediction=7
)
```

## Next Steps

1. **Run `example_with_logging.py`** - See it in action
2. **Open the Jupyter notebook** - Visualize the results
3. **Experiment** - Try different hyperparameters
4. **Compare** - Train multiple networks and compare logs

## Questions to Explore

- What learning rate works best?
- How many hidden layer neurons are optimal?
- Does sigmoid or ReLU learn faster?
- When does the network stop improving?
- Which layers change most during training?

All these questions can be answered by analyzing the logs! 📊
