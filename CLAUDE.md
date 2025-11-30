# Project Instructions for Claude

## MANDATORY: Python Code Standards

**ALL Python code written in this project MUST strictly follow `.cursor/rules/python.mdc`**

### Enforcement Rules

1. **Before writing ANY Python code:**
   - Review `.cursor/rules/python.mdc`
   - Apply ALL rules from that file
   - No exceptions, no shortcuts

2. **Type System - NON-NEGOTIABLE:**
   - ALWAYS use type hints on every function
   - NEVER use `Union`, `Optional`, `List`, `Dict` - use `|`, `list[]`, `dict[]`
   - USE `def func[T](items: list[T]) -> T:` for generics
   - RUN `make typecheck` before claiming code is complete

3. **Code Quality - MANDATORY:**
   - RUN `make fix` to auto-fix linting issues and format code
   - RUN `make check` to verify all quality checks pass
   - Fix ALL type errors before committing
   - NO bare `except:` statements
   - NO wildcard imports

4. **Data Structures:**
   - USE `@dataclass(slots=True, frozen=True, kw_only=True)` by default
   - USE `pathlib.Path` (NEVER string paths)
   - USE f-strings (NEVER `%` or `.format()`)

5. **Testing:**
   - USE `pytest` exclusively
   - Include type hints in test functions
   - RUN tests before claiming completion

### Validation Checklist

Before considering any Python code complete, verify:
- [ ] All functions have type hints
- [ ] `make lint` passes with no errors
- [ ] `make typecheck` passes with no errors
- [ ] `make test` passes all tests
- [ ] No anti-patterns from rules file present
- [ ] All imports are explicit (no wildcards)
- [ ] Using modern Python 3.14+ syntax

**Quick workflow:**
1. Write code following `.cursor/rules/python.mdc`
2. Run `make fix` to auto-fix and format
3. Run `make check` to verify everything passes
4. Commit if all checks pass

### If Rules Conflict

If any instruction conflicts with `.cursor/rules/python.mdc`, the Python rules file takes precedence. Always follow the strictest interpretation of the rules.

## Documentation Standards

**General documentation files MUST go in `docs/` directory:**
- Architecture guides → `docs/ARCHITECTURE.md`
- API documentation → `docs/API.md`
- Learning guides → `docs/LEARNING.md`
- Frontend requirements → `docs/FRONTEND_REQUIREMENTS.md`

**Folder-specific READMEs stay in their folders:**
- `api/README.md` - API module documentation
- `neural_networks/README.md` - Neural network implementations
- `schemas/README.md` - Schema definitions

**Root level:**
- `README.md` - Main project overview (ONLY this one in root)
- `CLAUDE.md` - Instructions for Claude (this file)

## Project Context

This is a neural network learning API (FastAPI + NumPy). The project uses a modular architecture to support multiple network types (feedforward, CNN, RNN, etc.).

### Current Architecture
- `api/` - FastAPI routes (separate routers per network type)
- `neural_networks/` - ML implementations (clean, no HTTP)
- `schemas/` - Pydantic models by domain
- `notebooks/` - Jupyter analysis notebooks
- `docs/` - General documentation

### Route Naming Convention
Use **separate routers** for different network types:
- `/network/*` - Basic feedforward networks
- `/cnn/*` - Convolutional networks (future)
- `/rnn/*` - Recurrent networks (future)
- `/mnist/*` - MNIST dataset operations

### Logging Strategy
- **Production API**: Use regular `NeuralNetwork` (fast, no detailed logs)
- **Learning/experiments**: Use `LoggedNeuralNetwork` wrapper (detailed logs for Jupyter analysis)
- API provides SSE streaming for frontend progress, not file logging
