# Hippo Neural Network Project - Makefile

.PHONY: help install train upload start test clean

# Default target
help:
	@echo "Hippo Neural Network Commands:"
	@echo ""
	@echo "  make install       Install dependencies"
	@echo "  make train         Train a model (customize with ARGS)"
	@echo "  make upload        Upload model to HF Hub (requires MODEL and ACC)"
	@echo "  make start         Start API server"
	@echo "  make test          Run tests"
	@echo "  make clean         Clean cache and temporary files"
	@echo ""
	@echo "Examples:"
	@echo "  make train"
	@echo "  make train ARGS='--sizes 784 30 10 --activation sigmoid --epochs 10'"
	@echo "  make upload MODEL=models/mnist-relu-100.npz ACC=95.4"

# Install dependencies
install:
	pip install -r requirements.txt

# Train a model (default: 784-100-10 with ReLU)
train:
	python training/cli_train.py \
		--sizes 784 100 10 \
		--activation relu \
		--epochs 30 \
		--learning-rate 0.01 \
		$(ARGS)

# Train small/fast model (for testing)
train-small:
	python training/cli_train.py \
		--sizes 784 30 10 \
		--activation sigmoid \
		--epochs 10 \
		--learning-rate 3.0

# Upload model to Hugging Face Hub and clean up local files
upload:
	@if [ -z "$(MODEL)" ]; then \
		echo "Error: MODEL not set"; \
		echo "Usage: make upload MODEL=models/my-model.npz ACC=95.4"; \
		exit 1; \
	fi
	@if [ -z "$(ACC)" ]; then \
		echo "Error: ACC (accuracy) not set"; \
		echo "Usage: make upload MODEL=models/my-model.npz ACC=95.4"; \
		exit 1; \
	fi
	@python training/cli_upload.py \
		--model-path $(MODEL) \
		--accuracy $(ACC) \
		$(ARGS)
	@if [ $$? -eq 0 ]; then \
		rm -f $(MODEL) $(MODEL:.npz=.json); \
		echo "✓ Cleaned up local files"; \
	else \
		echo "✗ Upload failed - keeping local files"; \
		exit 1; \
	fi

# Start API server
start:
	uvicorn api.main:app --reload

# Start API on different port
start-port:
	uvicorn api.main:app --reload --port $(PORT)

# Run tests
test:
	pytest tests/ -v

# Clean cache and temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .hf_cache
	@echo "✓ Cleaned cache and temporary files"

# Initialize database (for future use)
init-db:
	python init_db.py

# Format code
format:
	ruff format .

# Lint code
lint:
	ruff check .

# Type check
typecheck:
	mypy --strict neural_networks/ api/ training/ hf_hub/
