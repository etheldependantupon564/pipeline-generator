"""Auto-detect project type from directory contents."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field


@dataclass
class DetectionResult:
    """Result of project auto-detection."""

    language: str = ""
    version: str = ""
    framework: str = ""
    package_manager: str = ""
    has_dockerfile: bool = False
    has_tests: bool = False
    existing_ci: list[str] = field(default_factory=list)
    confidence: float = 0.0
    details: list[str] = field(default_factory=list)


def detect_project(path: str = ".") -> DetectionResult:
    """Scan a directory to detect the project type and configuration.

    Looks at filenames, config files, and directory structure to determine
    the language, framework, package manager, and existing CI setup.
    """
    result = DetectionResult()

    if not os.path.isdir(path):
        result.details.append(f"Path '{path}' is not a directory")
        return result

    # Collect top-level entries (lowercased for matching)
    entries: set[str] = set()
    for entry in os.listdir(path):
        entries.add(entry.lower())

    # Also check immediate subdirectories
    for entry in os.listdir(path):
        full = os.path.join(path, entry)
        if os.path.isdir(full) and not entry.startswith("."):
            try:
                for sub in os.listdir(full):
                    entries.add(f"{entry.lower()}/{sub.lower()}")
            except PermissionError:
                pass

    # ---- Detect existing CI/CD ----
    if any("workflows" in e for e in entries):
        result.existing_ci.append("GitHub Actions")
    if "azure-pipelines.yml" in entries:
        result.existing_ci.append("Azure DevOps")
    if ".gitlab-ci.yml" in entries:
        result.existing_ci.append("GitLab CI")
    if "jenkinsfile" in entries:
        result.existing_ci.append("Jenkins")

    # ---- Detect Dockerfile ----
    if "dockerfile" in entries:
        result.has_dockerfile = True
        result.details.append("Dockerfile found")

    # ---- Detect language ----

    # Python
    if any(f in entries for f in ("pyproject.toml", "setup.py", "requirements.txt", "pipfile")):
        result.language = "python"
        result.confidence = 0.9
        result.package_manager = "pip"

        if "pyproject.toml" in entries:
            _detect_python_details(os.path.join(path, "pyproject.toml"), result)
        elif "requirements.txt" in entries:
            result.details.append("Python project (requirements.txt)")

        if not result.version:
            result.version = "3.11"
        result.details.append(f"Detected: Python {result.version}")

    # Node.js
    elif "package.json" in entries:
        result.language = "node"
        result.confidence = 0.9
        result.package_manager = "npm"

        _detect_node_details(os.path.join(path, "package.json"), result, entries)

        if not result.version:
            result.version = "20"
        result.details.append(f"Detected: Node.js {result.version}")

    # Go
    elif "go.mod" in entries:
        result.language = "go"
        result.confidence = 0.9
        result.package_manager = "go"

        _detect_go_details(os.path.join(path, "go.mod"), result)

        if not result.version:
            result.version = "1.22"
        result.details.append(f"Detected: Go {result.version}")

    # .NET
    elif any(f.endswith(".csproj") or f.endswith(".sln") for f in entries):
        result.language = "dotnet"
        result.confidence = 0.9
        result.package_manager = "dotnet"
        result.version = "8.0.x"
        result.details.append("Detected: .NET 8.0")

    # Terraform
    elif any(f.endswith(".tf") for f in entries):
        result.language = "terraform"
        result.confidence = 0.85
        result.package_manager = "terraform"
        result.version = "1.7"
        result.details.append("Detected: Terraform")

    # ---- Detect test directory ----
    test_dirs = {"tests", "test", "spec", "__tests__", "tests/"}
    if test_dirs & entries:
        result.has_tests = True
        result.details.append("Test directory found")

    return result


def _detect_python_details(pyproject_path: str, result: DetectionResult) -> None:
    """Extract Python project details from pyproject.toml."""
    try:
        content = open(pyproject_path, encoding="utf-8").read()
        lower = content.lower()
        if "fastapi" in lower:
            result.framework = "fastapi"
        elif "django" in lower:
            result.framework = "django"
        elif "flask" in lower:
            result.framework = "flask"

        for line in content.split("\n"):
            if "python_requires" in line and ">=" in line:
                ver = line.split(">=")[1].strip().strip('"').strip("'").strip(",")
                result.version = ver[:4]
                break
    except (OSError, IndexError):
        pass


def _detect_node_details(package_path: str, result: DetectionResult, entries: set[str]) -> None:
    """Extract Node.js project details from package.json."""
    try:
        pkg = json.load(open(package_path, encoding="utf-8"))
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

        for fw, name in [
            ("next", "next"),
            ("express", "express"),
            ("react", "react"),
            ("vue", "vue"),
            ("angular", "@angular/core"),
        ]:
            if name in deps:
                result.framework = fw
                break

        if "yarn.lock" in entries:
            result.package_manager = "yarn"
        elif "pnpm-lock.yaml" in entries:
            result.package_manager = "pnpm"

        engines = pkg.get("engines", {})
        if "node" in engines:
            result.version = engines["node"].strip(">=^~").split(".")[0]
    except (OSError, json.JSONDecodeError, IndexError):
        pass


def _detect_go_details(gomod_path: str, result: DetectionResult) -> None:
    """Extract Go project details from go.mod."""
    try:
        content = open(gomod_path, encoding="utf-8").read()
        for line in content.split("\n"):
            if line.startswith("go "):
                result.version = line.split()[1]
                break
    except (OSError, IndexError):
        pass
