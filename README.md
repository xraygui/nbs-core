# NSLS-II Beamline Core Library

A core library providing common functionality shared across NSLS-II beamline software packages.

## Overview

nbs-core serves as the foundation for other NSLS-II beamline packages, providing:

- Common utilities and helper functions
- Shared data structures and models
- Base classes for device control
- Configuration management tools
- Core interfaces and protocols

## Usage

This package is typically used as a dependency in other nbs packages:
- `nbs-bl`: Beamline support library
- `nbs-gui`: Beamline GUI framework

## Installation

```bash
# Clone the repository
git clone https://github.com/xraygui/nbs-core.git
cd nbs-core

# Install in development mode
pip install -e .
```

## Dependencies

- Python 3.8+
- Bluesky
- Ophyd
- NumPy

## License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details. 