"""Data models for pipeline specifications."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProjectConfig:
    """Project metadata."""

    name: str
    language: str  # python, node, go, dotnet, terraform
    version: str
    framework: str = ""

    def __post_init__(self) -> None:
        self.language = self.language.lower()
        aliases = {
            "nodejs": "node",
            "javascript": "node",
            "typescript": "node",
            "js": "node",
            "ts": "node",
            "csharp": "dotnet",
            "c#": "dotnet",
            "fsharp": "dotnet",
            "f#": "dotnet",
            "golang": "go",
            "py": "python",
            "python3": "python",
        }
        self.language = aliases.get(self.language, self.language)


@dataclass
class LintConfig:
    """Linting configuration."""

    tools: list[str] = field(default_factory=list)


@dataclass
class TestConfig:
    """Test configuration."""

    framework: str = ""
    coverage: bool = True
    min_coverage: int = 80


@dataclass
class SecurityConfig:
    """Security scanning configuration."""

    tools: list[str] = field(default_factory=list)


@dataclass
class BuildConfig:
    """Build configuration."""

    type: str = "docker"  # docker | package | binary
    dockerfile: str = "Dockerfile"
    registry: str = "ghcr.io"
    context: str = "."


@dataclass
class Environment:
    """Deployment environment."""

    name: str
    auto_deploy: bool = True


@dataclass
class DeployConfig:
    """Deployment configuration."""

    target: str = "kubernetes"  # kubernetes | azure-webapp | aws-ecs | static
    environments: list[Environment] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.environments:
            self.environments = [
                Environment(name="staging", auto_deploy=True),
                Environment(name="production", auto_deploy=False),
            ]
        elif self.environments and isinstance(self.environments[0], dict):
            self.environments = [Environment(**e) for e in self.environments]


@dataclass
class PipelineSpec:
    """Complete pipeline specification."""

    project: ProjectConfig
    stages: list[str] = field(default_factory=lambda: ["lint", "test", "build"])
    lint: LintConfig | None = None
    test: TestConfig | None = None
    security: SecurityConfig | None = None
    build: BuildConfig | None = None
    deploy: DeployConfig | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PipelineSpec:
        """Create a PipelineSpec from a dictionary (YAML-loaded data)."""
        project_data = data.get("project", {})
        for key in ("name", "language", "version"):
            if not project_data.get(key):
                raise ValueError(f"project.{key} is required in the spec file")

        project = ProjectConfig(**project_data)
        stages = data.get("stages", ["lint", "test", "build"])

        lint = LintConfig(**data["lint"]) if "lint" in data else None
        test = TestConfig(**data["test"]) if "test" in data else None
        security = SecurityConfig(**data["security"]) if "security" in data else None
        build = BuildConfig(**data["build"]) if "build" in data else None
        deploy = DeployConfig(**data["deploy"]) if "deploy" in data else None

        return cls(
            project=project,
            stages=stages,
            lint=lint,
            test=test,
            security=security,
            build=build,
            deploy=deploy,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result: dict[str, Any] = {
            "project": {
                "name": self.project.name,
                "language": self.project.language,
                "version": self.project.version,
            },
        }
        if self.project.framework:
            result["project"]["framework"] = self.project.framework

        result["stages"] = list(self.stages)

        if self.lint:
            result["lint"] = {"tools": list(self.lint.tools)}
        if self.test:
            result["test"] = {
                "framework": self.test.framework,
                "coverage": self.test.coverage,
                "min_coverage": self.test.min_coverage,
            }
        if self.security:
            result["security"] = {"tools": list(self.security.tools)}
        if self.build:
            result["build"] = {
                "type": self.build.type,
                "dockerfile": self.build.dockerfile,
                "registry": self.build.registry,
            }
        if self.deploy:
            result["deploy"] = {
                "target": self.deploy.target,
                "environments": [
                    {"name": e.name, "auto_deploy": e.auto_deploy} for e in self.deploy.environments
                ],
            }

        return result
