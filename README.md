# Aegis Core

Core integrator for the Aegis AI autonomy trilogy - providing shared contracts, plumbing, and observability layer that the other three repositories plug into.

## Overview

Aegis Core serves as the central nervous system for the Aegis trilogy:

- **Scaffolding** - Central identity and memory persistence
- **Decision Engine** - Thought-to-action conversion
- **Personality Matrix** - Survivable personality layer

## Architecture

### Core Components

- **State Management**: Persistent storage with JSONL rotation
- **Event System**: Async pub/sub for component communication
- **Tracing**: Comprehensive decision trace logging
- **Policy Layer**: Self-governance and safety controls
- **Contracts**: Protocol definitions for component integration

### Key Features

- **StateStore Interface**: `get()`, `set()`, `append_jsonl()`, `rotate()`
- **EventBus**: Topic-based async messaging
- **DecisionTrace**: Complete audit trail of AI decisions
- **SelfGovernancePolicy**: Maturity gates, mental health monitoring, PMX boundaries

## Installation

```bash
pip install aegis-core
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/
isort src/ tests/
```

## Usage

See `examples/golden_path.py` for a complete integration example.

## License

MIT License - see LICENSE file for details.