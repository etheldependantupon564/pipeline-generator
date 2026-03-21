"""Fixtures and helpers for pipeline-generator tests."""

from __future__ import annotations

import pytest

from pipeline_generator.models import (
    BuildConfig,
    DeployConfig,
    Environment,
    LintConfig,
    PipelineSpec,
    ProjectConfig,
    SecurityConfig,
    TestConfig,
)


@pytest.fixture
def python_spec() -> PipelineSpec:
    """A full-featured Python pipeline spec."""
    return PipelineSpec(
        project=ProjectConfig(
            name="my-python-api", language="python", version="3.11", framework="fastapi"
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
    )


@pytest.fixture
def node_spec() -> PipelineSpec:
    """A Node.js pipeline spec."""
    return PipelineSpec(
        project=ProjectConfig(name="my-node-app", language="node", version="20"),
        stages=["lint", "test", "security", "build"],
        lint=LintConfig(tools=["eslint", "prettier"]),
        test=TestConfig(framework="jest", coverage=True, min_coverage=80),
        security=SecurityConfig(tools=["npm-audit"]),
        build=BuildConfig(type="docker", registry="ghcr.io"),
    )


@pytest.fixture
def go_spec() -> PipelineSpec:
    """A Go pipeline spec."""
    return PipelineSpec(
        project=ProjectConfig(name="my-go-service", language="go", version="1.22"),
        stages=["lint", "test", "security", "build"],
        lint=LintConfig(tools=["golangci-lint"]),
        test=TestConfig(framework="go-test", coverage=True),
        security=SecurityConfig(tools=["gosec", "govulncheck"]),
        build=BuildConfig(type="docker", registry="ghcr.io"),
    )


@pytest.fixture
def minimal_spec() -> PipelineSpec:
    """A minimal spec with just lint and test."""
    return PipelineSpec(
        project=ProjectConfig(name="simple-app", language="python", version="3.12"),
        stages=["lint", "test"],
    )


@pytest.fixture
def python_spec_dict() -> dict:
    """Raw dict representing a pipeline.yaml for Python."""
    return {
        "project": {
            "name": "dict-loaded-app",
            "language": "python",
            "version": "3.11",
        },
        "stages": ["lint", "test", "build"],
        "lint": {"tools": ["ruff"]},
        "test": {"framework": "pytest", "coverage": True, "min_coverage": 80},
        "build": {"type": "docker", "dockerfile": "Dockerfile", "registry": "ghcr.io"},
    }
