# 🚀 pipeline-generator

[![PyPI](https://img.shields.io/pypi/v/cicd-pipeline-generator.svg)](https://pypi.org/project/cicd-pipeline-generator/)
[![Python](https://img.shields.io/pypi/pyversions/cicd-pipeline-generator)](https://pypi.org/project/cicd-pipeline-generator/)
[![CI](https://github.com/SanjaySundarMurthy/pipeline-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/SanjaySundarMurthy/pipeline-generator/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/cicd-pipeline-generator.svg)](https://pypi.org/project/cicd-pipeline-generator/)

**Generate production-ready CI/CD pipeline configs from a simple YAML spec.**

One spec file → pipeline configs for **GitHub Actions**, **Azure DevOps**, and **GitLab CI**. Stop writing boilerplate YAML manually.

```
pipe-gen generate --demo
```

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🐙 **GitHub Actions** | Generates `.github/workflows/ci.yml` with matrix testing, caching, Docker builds |
| 🔷 **Azure DevOps** | Generates `azure-pipelines.yml` with stages, test publishing, deployment jobs |
| 🦊 **GitLab CI** | Generates `.gitlab-ci.yml` with parallel matrix, DinD builds, environments |
| 🔍 **Auto-Detect** | Scans your project to detect language, framework, and existing CI configs |
| 📝 **Simple Spec** | Define your pipeline in a human-readable YAML spec file |
| 🎨 **Rich Output** | Beautiful terminal output with previews, syntax highlighting, and summaries |
| 🏗️ **5 Languages** | Python, Node.js, Go, .NET, Terraform — with smart defaults for each |
| 🔒 **Security** | Built-in security scanning stages (Bandit, Safety, npm audit, gosec, tfsec) |
| 🐳 **Docker** | Docker build & push with metadata extraction and multi-platform support |
| 🚀 **Deploy** | Environment-based deployments with manual approval gates |

## 📦 Installation

```bash
pip install cicd-pipeline-generator
```

Or install from source:

```bash
git clone https://github.com/SanjaySundarMurthy/pipeline-generator.git
cd pipeline-generator
pip install cicd-pipeline-generator
```

## 🚀 Quick Start

### 1. Create a spec file

```bash
# From a preset
pipe-gen init --preset python --name my-api

# Or auto-detect your project
pipe-gen detect
```

### 2. Edit the spec (optional)

```yaml
# pipeline.yaml
project:
  name: my-api
  language: python
  version: "3.11"
  framework: fastapi

stages:
  - lint
  - test
  - security
  - build
  - deploy

lint:
  tools:
    - ruff

test:
  framework: pytest
  coverage: true
  min_coverage: 80

security:
  tools:
    - bandit
    - safety

build:
  type: docker
  dockerfile: Dockerfile
  registry: ghcr.io

deploy:
  target: kubernetes
  environments:
    - name: staging
      auto_deploy: true
    - name: production
      auto_deploy: false
```

### 3. Generate pipeline configs

```bash
# Generate for all platforms
pipe-gen generate --platform all

# Generate for a specific platform
pipe-gen generate --platform github

# Preview without writing files
pipe-gen generate --dry-run

# Try the demo (no files needed)
pipe-gen generate --demo
```

## 📋 CLI Reference

| Command | Description |
|---------|-------------|
| `pipe-gen init` | Create a pipeline.yaml spec file |
| `pipe-gen detect` | Auto-detect project type |
| `pipe-gen generate` | Generate CI/CD pipeline configs |
| `pipe-gen --version` | Show version |

### `pipe-gen init`

```
Options:
  -p, --preset   Language preset (python, node, go, dotnet, terraform)
  -n, --name     Project name
  -o, --output   Output file path (default: pipeline.yaml)
```

### `pipe-gen generate`

```
Options:
  -p, --platform   Target platform: all, github, azure, gitlab (default: all)
  -s, --spec       Path to spec file (default: pipeline.yaml)
  --preset         Use a built-in preset instead of spec file
  -o, --output-dir Output directory (default: current dir)
  --dry-run        Preview without writing files
  --demo           Demo mode with sample output
```

## 🗣️ Supported Languages

| Language | Lint Tools | Test Framework | Security Tools | Setup Action |
|----------|-----------|----------------|----------------|--------------|
| **Python** | ruff, mypy, flake8, black | pytest, unittest | bandit, safety | setup-python@v5 |
| **Node.js** | eslint, prettier | jest, vitest, mocha | npm audit | setup-node@v4 |
| **Go** | golangci-lint, go vet | go test | gosec, govulncheck | setup-go@v5 |
| **.NET** | dotnet format | dotnet test | dotnet audit | setup-dotnet@v4 |
| **Terraform** | terraform fmt, tflint | terraform validate | tfsec, checkov | setup-terraform@v3 |

## 🏗️ Generated Pipeline Structure

Each generated pipeline includes (based on your spec):

```
lint  →  test (matrix)  →  security  →  build (Docker)  →  deploy
                                                          ├── staging (auto)
                                                          └── production (manual)
```

### What's included:

- **Lint**: Code style checking, formatting validation
- **Test**: Matrix testing across language versions, coverage reports
- **Security**: SAST scanning, dependency vulnerability checks
- **Build**: Docker build & push with image metadata and tagging
- **Deploy**: Environment-based deployments with approval gates

## 🔧 Advanced Usage

### Use a preset without a spec file

```bash
pipe-gen generate --preset python --platform github --dry-run
```

### Generate in a different directory

```bash
pipe-gen generate --output-dir ./ci-configs
```

### Auto-detect and generate

```bash
pipe-gen detect           # See what's detected
pipe-gen init             # Create spec from detection
pipe-gen generate         # Generate configs
```

## 🧪 Running Tests

```bash
# Install dev dependencies
pip install cicd-pipeline-generator

# Run tests
pytest -v

# Run with coverage
pytest --cov=pipeline_generator -v
```

## 📁 Project Structure

```
pipeline-generator/
├── pipeline_generator/
│   ├── __init__.py          # Package version
│   ├── cli.py               # Click CLI commands
│   ├── models.py            # PipelineSpec data models
│   ├── presets.py            # Language configs & presets
│   ├── detector.py           # Project auto-detection
│   ├── generator.py          # Generation engine
│   ├── platforms/
│   │   ├── base.py          # Abstract base class
│   │   ├── github.py        # GitHub Actions generator
│   │   ├── azure.py         # Azure DevOps generator
│   │   └── gitlab.py        # GitLab CI generator
│   └── output/
│       └── console.py       # Rich terminal output
├── tests/
│   ├── conftest.py          # Test fixtures
│   └── test_generator.py    # 35+ tests
├── examples/                # Example spec files
├── pyproject.toml
├── README.md
└── CONTRIBUTING.md
```

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Adding a new language

1. Add tool config to `presets.py` → `LANGUAGE_TOOLS`
2. Add preset to `PRESETS`
3. Add detection in `detector.py`
4. Add tests and an example spec

### Adding a new platform

1. Create generator in `platforms/`
2. Inherit from `BasePlatform`
3. Register in `generator.py` → `PLATFORMS`

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

## 👤 Author

**Sanjay S** — Senior DevOps Engineer

- GitHub: [@SanjaySundarMurthy](https://github.com/SanjaySundarMurthy)
- LinkedIn: [sanjaysundarmurthy](https://linkedin.com/in/sanjaysundarmurthy)
- Portfolio: [sanjaysundarmurthy-portfolio.vercel.app](https://sanjaysundarmurthy-portfolio.vercel.app)


## 🐳 Docker

Run without installing Python:

```bash
# Build the image
docker build -t pipeline-generator .

# Run
docker run --rm pipeline-generator --help

# Example with volume mount
docker run --rm -v ${PWD}:/workspace pipeline-generator [command] /workspace
```

Or pull from the container registry:

```bash
docker pull ghcr.io/SanjaySundarMurthy/pipeline-generator:latest
docker run --rm ghcr.io/SanjaySundarMurthy/pipeline-generator:latest --help
```

## 🔗 Links

- **PyPI**: [https://pypi.org/project/cicd-pipeline-generator/](https://pypi.org/project/cicd-pipeline-generator/)
- **GitHub**: [https://github.com/SanjaySundarMurthy/pipeline-generator](https://github.com/SanjaySundarMurthy/pipeline-generator)
- **Issues**: [https://github.com/SanjaySundarMurthy/pipeline-generator/issues](https://github.com/SanjaySundarMurthy/pipeline-generator/issues)