"""Language presets and tool configurations for pipeline generation."""

from __future__ import annotations

from .models import (
    BuildConfig,
    DeployConfig,
    Environment,
    LintConfig,
    PipelineSpec,
    ProjectConfig,
    SecurityConfig,
    TestConfig,
)

# =============================================================================
# Language-specific tool configurations
# Used by platform generators to produce correct commands per language.
# =============================================================================
LANGUAGE_TOOLS: dict = {
    "python": {
        "setup_action": "actions/setup-python@v5",
        "setup_key": "python-version",
        "cache_key": "pip",
        "install_deps": 'pip install -e ".[dev]"',
        "alt_install": "pip install -r requirements.txt",
        "lint_tools": {
            "ruff": {
                "install": "pip install ruff",
                "run": ["ruff check .", "ruff format --check ."],
            },
            "mypy": {
                "install": "pip install mypy",
                "run": ["mypy ."],
            },
            "flake8": {
                "install": "pip install flake8",
                "run": ["flake8 ."],
            },
            "black": {
                "install": "pip install black",
                "run": ["black --check ."],
            },
        },
        "test_frameworks": {
            "pytest": "pytest --cov --cov-report=xml -v",
            "unittest": "python -m unittest discover -v",
        },
        "security_tools": {
            "bandit": {"install": "pip install bandit", "run": "bandit -r . -x ./tests"},
            "safety": {"install": "pip install safety", "run": "safety check"},
        },
        "default_versions": ["3.10", "3.11", "3.12"],
        "image_template": "python:{version}",
        "azure_setup_task": "UsePythonVersion@0",
        "azure_version_key": "versionSpec",
        "version_var": "PYTHON_VERSION",
        "version_var_azure": "pythonVersion",
    },
    "node": {
        "setup_action": "actions/setup-node@v4",
        "setup_key": "node-version",
        "cache_key": "npm",
        "install_deps": "npm ci",
        "alt_install": "npm install",
        "needs_deps_for_lint": True,
        "lint_tools": {
            "eslint": {"install": "", "run": ["npx eslint ."]},
            "prettier": {"install": "", "run": ["npx prettier --check ."]},
        },
        "test_frameworks": {
            "jest": "npx jest --coverage --ci",
            "vitest": "npx vitest run --coverage",
            "mocha": "npx mocha --recursive",
        },
        "security_tools": {
            "npm-audit": {"install": "", "run": "npm audit --audit-level=moderate"},
        },
        "default_versions": ["18", "20", "22"],
        "image_template": "node:{version}",
        "azure_setup_task": "NodeTool@0",
        "azure_version_key": "versionSpec",
        "version_var": "NODE_VERSION",
        "version_var_azure": "nodeVersion",
    },
    "go": {
        "setup_action": "actions/setup-go@v5",
        "setup_key": "go-version",
        "cache_key": "",
        "install_deps": "go mod download",
        "alt_install": "go mod download",
        "lint_tools": {
            "golangci-lint": {
                "install": "go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest",
                "run": ["golangci-lint run ./..."],
            },
            "go-vet": {"install": "", "run": ["go vet ./..."]},
        },
        "test_frameworks": {
            "go-test": "go test -race -coverprofile=coverage.out -v ./...",
        },
        "security_tools": {
            "gosec": {
                "install": "go install github.com/securego/gosec/v2/cmd/gosec@latest",
                "run": "gosec ./...",
            },
            "govulncheck": {
                "install": "go install golang.org/x/vuln/cmd/govulncheck@latest",
                "run": "govulncheck ./...",
            },
        },
        "default_versions": ["1.21", "1.22", "1.23"],
        "image_template": "golang:{version}",
        "azure_setup_task": "GoTool@0",
        "azure_version_key": "version",
        "version_var": "GO_VERSION",
        "version_var_azure": "goVersion",
    },
    "dotnet": {
        "setup_action": "actions/setup-dotnet@v4",
        "setup_key": "dotnet-version",
        "cache_key": "",
        "install_deps": "dotnet restore",
        "alt_install": "dotnet restore",
        "lint_tools": {
            "dotnet-format": {"install": "", "run": ["dotnet format --verify-no-changes"]},
        },
        "test_frameworks": {
            "dotnet-test": (
                'dotnet test --collect:"XPlat Code Coverage"'
                " --logger trx --results-directory TestResults"
            ),
        },
        "security_tools": {
            "dotnet-audit": {
                "install": "",
                "run": "dotnet list package --vulnerable",
            },
        },
        "default_versions": ["8.0.x"],
        "image_template": "mcr.microsoft.com/dotnet/sdk:{version}",
        "azure_setup_task": "UseDotNet@2",
        "azure_version_key": "version",
        "version_var": "DOTNET_VERSION",
        "version_var_azure": "dotnetVersion",
    },
    "terraform": {
        "setup_action": "hashicorp/setup-terraform@v3",
        "setup_key": "terraform_version",
        "cache_key": "",
        "install_deps": "terraform init -backend=false",
        "alt_install": "terraform init -backend=false",
        "lint_tools": {
            "terraform-fmt": {"install": "", "run": ["terraform fmt -check -recursive"]},
            "tflint": {
                "install": (
                    "curl -s https://raw.githubusercontent.com/terraform-linters/"
                    "tflint/master/install_linux.sh | bash"
                ),
                "run": ["tflint --recursive"],
            },
        },
        "test_frameworks": {
            "terraform-validate": "terraform validate",
        },
        "security_tools": {
            "tfsec": {
                "install": (
                    "curl -s https://raw.githubusercontent.com/aquasecurity/"
                    "tfsec/master/scripts/install_linux.sh | bash"
                ),
                "run": "tfsec .",
            },
            "checkov": {"install": "pip install checkov", "run": "checkov -d ."},
        },
        "default_versions": ["1.7"],
        "image_template": "hashicorp/terraform:{version}",
        "azure_setup_task": "",
        "azure_version_key": "",
        "version_var": "TF_VERSION",
        "version_var_azure": "tfVersion",
    },
}


# =============================================================================
# Quick-start presets — used by `pipe-gen init --preset <name>`
# =============================================================================
PRESETS: dict[str, PipelineSpec] = {
    "python": PipelineSpec(
        project=ProjectConfig(name="my-python-app", language="python", version="3.11"),
        stages=["lint", "test", "security", "build"],
        lint=LintConfig(tools=["ruff"]),
        test=TestConfig(framework="pytest", coverage=True, min_coverage=80),
        security=SecurityConfig(tools=["bandit", "safety"]),
        build=BuildConfig(type="docker", registry="ghcr.io"),
    ),
    "python-full": PipelineSpec(
        project=ProjectConfig(
            name="my-python-app", language="python", version="3.11", framework="fastapi"
        ),
        stages=["lint", "test", "security", "build", "deploy"],
        lint=LintConfig(tools=["ruff"]),
        test=TestConfig(framework="pytest", coverage=True, min_coverage=80),
        security=SecurityConfig(tools=["bandit", "safety"]),
        build=BuildConfig(type="docker", registry="ghcr.io"),
        deploy=DeployConfig(
            target="kubernetes",
            environments=[
                Environment(name="staging", auto_deploy=True),
                Environment(name="production", auto_deploy=False),
            ],
        ),
    ),
    "python-django": PipelineSpec(
        project=ProjectConfig(
            name="my-django-app", language="python", version="3.11", framework="django"
        ),
        stages=["lint", "test", "security", "build", "deploy"],
        lint=LintConfig(tools=["ruff", "mypy"]),
        test=TestConfig(framework="pytest", coverage=True, min_coverage=80),
        security=SecurityConfig(tools=["bandit", "safety"]),
        build=BuildConfig(type="docker", registry="ghcr.io"),
        deploy=DeployConfig(
            target="kubernetes",
            environments=[
                Environment(name="staging", auto_deploy=True),
                Environment(name="production", auto_deploy=False),
            ],
        ),
    ),
    "python-flask": PipelineSpec(
        project=ProjectConfig(
            name="my-flask-app", language="python", version="3.11", framework="flask"
        ),
        stages=["lint", "test", "security", "build"],
        lint=LintConfig(tools=["ruff"]),
        test=TestConfig(framework="pytest", coverage=True, min_coverage=80),
        security=SecurityConfig(tools=["bandit", "safety"]),
        build=BuildConfig(type="docker", registry="ghcr.io"),
    ),
    "node": PipelineSpec(
        project=ProjectConfig(name="my-node-app", language="node", version="20"),
        stages=["lint", "test", "security", "build"],
        lint=LintConfig(tools=["eslint", "prettier"]),
        test=TestConfig(framework="jest", coverage=True, min_coverage=80),
        security=SecurityConfig(tools=["npm-audit"]),
        build=BuildConfig(type="docker", registry="ghcr.io"),
    ),
    "node-ts": PipelineSpec(
        project=ProjectConfig(
            name="my-typescript-app", language="node", version="20", framework="typescript"
        ),
        stages=["lint", "test", "security", "build"],
        lint=LintConfig(tools=["eslint", "prettier"]),
        test=TestConfig(framework="jest", coverage=True, min_coverage=80),
        security=SecurityConfig(tools=["npm-audit"]),
        build=BuildConfig(type="docker", registry="ghcr.io"),
    ),
    "go": PipelineSpec(
        project=ProjectConfig(name="my-go-app", language="go", version="1.22"),
        stages=["lint", "test", "security", "build"],
        lint=LintConfig(tools=["golangci-lint"]),
        test=TestConfig(framework="go-test", coverage=True),
        security=SecurityConfig(tools=["gosec", "govulncheck"]),
        build=BuildConfig(type="docker", registry="ghcr.io"),
    ),
    "dotnet": PipelineSpec(
        project=ProjectConfig(name="my-dotnet-app", language="dotnet", version="8.0.x"),
        stages=["lint", "test", "security", "build"],
        lint=LintConfig(tools=["dotnet-format"]),
        test=TestConfig(framework="dotnet-test", coverage=True),
        security=SecurityConfig(tools=["dotnet-audit"]),
        build=BuildConfig(type="docker", registry="ghcr.io"),
    ),
    "terraform": PipelineSpec(
        project=ProjectConfig(name="my-infra", language="terraform", version="1.7"),
        stages=["lint", "test", "security"],
        lint=LintConfig(tools=["terraform-fmt", "tflint"]),
        test=TestConfig(framework="terraform-validate"),
        security=SecurityConfig(tools=["tfsec", "checkov"]),
    ),
}
