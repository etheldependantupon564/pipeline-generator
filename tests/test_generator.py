"""Comprehensive tests for pipeline-generator."""

from __future__ import annotations

import os
import tempfile

import pytest
import yaml

from pipeline_generator.detector import detect_project
from pipeline_generator.generator import (
    fill_defaults,
    generate_pipelines,
    render_spec_yaml,
)
from pipeline_generator.models import (
    DeployConfig,
    PipelineSpec,
    ProjectConfig,
)
from pipeline_generator.platforms.azure import AzureDevOpsGenerator
from pipeline_generator.platforms.github import GitHubActionsGenerator
from pipeline_generator.platforms.gitlab import GitLabCIGenerator
from pipeline_generator.presets import LANGUAGE_TOOLS, PRESETS


# =============================================================================
# Model Tests
# =============================================================================
class TestModels:
    def test_spec_from_dict(self, python_spec_dict):
        spec = PipelineSpec.from_dict(python_spec_dict)
        assert spec.project.name == "dict-loaded-app"
        assert spec.project.language == "python"
        assert spec.lint is not None
        assert spec.lint.tools == ["ruff"]
        assert spec.test is not None
        assert spec.test.framework == "pytest"

    def test_spec_from_dict_missing_name_raises(self):
        with pytest.raises(ValueError, match="project.name"):
            PipelineSpec.from_dict({"project": {"language": "python", "version": "3.11"}})

    def test_spec_from_dict_missing_language_raises(self):
        with pytest.raises(ValueError, match="project.language"):
            PipelineSpec.from_dict({"project": {"name": "app", "version": "3.11"}})

    def test_language_alias_normalization(self):
        p = ProjectConfig(name="x", language="nodejs", version="20")
        assert p.language == "node"
        p2 = ProjectConfig(name="x", language="golang", version="1.22")
        assert p2.language == "go"
        p3 = ProjectConfig(name="x", language="csharp", version="8.0")
        assert p3.language == "dotnet"

    def test_spec_to_dict_roundtrip(self, python_spec):
        d = python_spec.to_dict()
        assert d["project"]["name"] == "my-python-api"
        assert d["stages"] == ["lint", "test", "security", "build", "deploy"]
        assert d["lint"]["tools"] == ["ruff"]
        assert d["deploy"]["target"] == "kubernetes"
        assert len(d["deploy"]["environments"]) == 2

    def test_deploy_config_default_environments(self):
        dc = DeployConfig()
        assert len(dc.environments) == 2
        assert dc.environments[0].name == "staging"
        assert dc.environments[1].name == "production"

    def test_deploy_config_from_dict_list(self):
        dc = DeployConfig(
            environments=[
                {"name": "dev", "auto_deploy": True},
                {"name": "prod", "auto_deploy": False},
            ]
        )
        assert dc.environments[0].name == "dev"
        assert dc.environments[1].auto_deploy is False


# =============================================================================
# GitHub Actions Generator Tests
# =============================================================================
class TestGitHubActions:
    def test_python_full_pipeline(self, python_spec):
        gen = GitHubActionsGenerator()
        output = gen.generate(python_spec)

        # Verify valid structure
        assert "name: my-python-api CI/CD" in output
        assert "on:" in output
        assert "jobs:" in output
        assert "lint:" in output
        assert "test:" in output
        assert "security:" in output
        assert "build:" in output
        assert "deploy-staging:" in output
        assert "deploy-production:" in output

    def test_python_uses_correct_actions(self, python_spec):
        gen = GitHubActionsGenerator()
        output = gen.generate(python_spec)

        assert "actions/checkout@v4" in output
        assert "actions/setup-python@v5" in output
        assert "docker/login-action@v3" in output
        assert "docker/build-push-action@v5" in output

    def test_python_lint_includes_ruff(self, python_spec):
        gen = GitHubActionsGenerator()
        output = gen.generate(python_spec)

        assert "pip install ruff" in output
        assert "ruff check ." in output

    def test_python_test_has_matrix(self, python_spec):
        gen = GitHubActionsGenerator()
        output = gen.generate(python_spec)

        assert "matrix:" in output
        assert '"3.10"' in output
        assert '"3.11"' in output
        assert '"3.12"' in output

    def test_python_security_tools(self, python_spec):
        gen = GitHubActionsGenerator()
        output = gen.generate(python_spec)

        assert "bandit" in output
        assert "safety" in output
        assert "continue-on-error: true" in output

    def test_node_pipeline(self, node_spec):
        gen = GitHubActionsGenerator()
        output = gen.generate(node_spec)

        assert "actions/setup-node@v4" in output
        assert "npm ci" in output
        assert "eslint" in output
        assert "NODE_VERSION" in output

    def test_go_pipeline(self, go_spec):
        gen = GitHubActionsGenerator()
        output = gen.generate(go_spec)

        assert "actions/setup-go@v5" in output
        assert "go mod download" in output
        assert "golangci-lint" in output
        assert "GO_VERSION" in output

    def test_minimal_spec_fills_defaults(self, minimal_spec):
        gen = GitHubActionsGenerator()
        filled = fill_defaults(minimal_spec)
        output = gen.generate(filled)

        assert "lint:" in output
        assert "test:" in output
        # No build or deploy
        assert "build:" not in output or "needs:" not in output.split("build:")[1].split("\n")[0]

    def test_build_job_has_docker_steps(self, python_spec):
        gen = GitHubActionsGenerator()
        output = gen.generate(python_spec)

        assert "docker/login-action@v3" in output
        assert "docker/metadata-action@v5" in output
        assert "docker/build-push-action@v5" in output
        assert "permissions:" in output


# =============================================================================
# Azure DevOps Generator Tests
# =============================================================================
class TestAzureDevOps:
    def test_python_full_pipeline(self, python_spec):
        gen = AzureDevOpsGenerator()
        output = gen.generate(python_spec)

        assert "trigger:" in output
        assert "stages:" in output
        assert "- stage: Lint" in output
        assert "- stage: Test" in output
        assert "- stage: Security" in output
        assert "- stage: Build" in output

    def test_azure_uses_correct_tasks(self, python_spec):
        gen = AzureDevOpsGenerator()
        output = gen.generate(python_spec)

        assert "UsePythonVersion@0" in output
        assert "PublishTestResults@2" in output

    def test_azure_deploy_stages(self, python_spec):
        gen = AzureDevOpsGenerator()
        output = gen.generate(python_spec)

        assert "DeployStaging" in output
        assert "DeployProduction" in output
        assert "deployment:" in output
        assert "runOnce:" in output

    def test_node_azure_pipeline(self, node_spec):
        gen = AzureDevOpsGenerator()
        output = gen.generate(node_spec)

        assert "NodeTool@0" in output
        assert "npm ci" in output


# =============================================================================
# GitLab CI Generator Tests
# =============================================================================
class TestGitLabCI:
    def test_python_full_pipeline(self, python_spec):
        gen = GitLabCIGenerator()
        output = gen.generate(python_spec)

        assert "stages:" in output
        assert "- lint" in output
        assert "- test" in output
        assert "- security" in output
        assert "- build" in output
        assert "- deploy" in output

    def test_gitlab_python_image(self, python_spec):
        gen = GitLabCIGenerator()
        output = gen.generate(python_spec)

        assert "python:" in output
        assert "PIP_CACHE_DIR" in output

    def test_gitlab_docker_build(self, python_spec):
        gen = GitLabCIGenerator()
        output = gen.generate(python_spec)

        assert "docker:latest" in output
        assert "docker:dind" in output
        assert "CI_REGISTRY" in output

    def test_gitlab_deploy_jobs(self, python_spec):
        gen = GitLabCIGenerator()
        output = gen.generate(python_spec)

        assert "deploy-staging:" in output
        assert "deploy-production:" in output
        assert "when: manual" in output

    def test_gitlab_go_pipeline(self, go_spec):
        gen = GitLabCIGenerator()
        output = gen.generate(go_spec)

        assert "golang:" in output
        assert "go mod download" in output


# =============================================================================
# Generator Engine Tests
# =============================================================================
class TestGeneratorEngine:
    def test_generate_all_platforms(self, python_spec):
        results = generate_pipelines(python_spec, platform="all", dry_run=True)
        assert len(results) == 3
        assert ".github/workflows/ci.yml" in results
        assert "azure-pipelines.yml" in results
        assert ".gitlab-ci.yml" in results

    def test_generate_single_platform(self, python_spec):
        results = generate_pipelines(python_spec, platform="github", dry_run=True)
        assert len(results) == 1
        assert ".github/workflows/ci.yml" in results

    def test_invalid_platform_raises(self, python_spec):
        with pytest.raises(ValueError, match="Unknown platform"):
            generate_pipelines(python_spec, platform="jenkins", dry_run=True)

    def test_fill_defaults_adds_missing_configs(self, minimal_spec):
        filled = fill_defaults(minimal_spec)
        assert filled.lint is not None
        assert filled.test is not None
        # Security not in stages, so shouldn't be filled
        assert filled.security is None

    def test_render_spec_yaml_valid(self, python_spec):
        content = render_spec_yaml(python_spec)
        # Should be valid YAML
        parsed = yaml.safe_load(content)
        assert parsed["project"]["name"] == "my-python-api"
        assert "stages" in parsed

    def test_write_files_to_disk(self, python_spec):
        with tempfile.TemporaryDirectory() as tmpdir:
            generate_pipelines(python_spec, platform="github", output_dir=tmpdir, dry_run=False)
            filepath = os.path.join(tmpdir, ".github", "workflows", "ci.yml")
            assert os.path.exists(filepath)
            content = open(filepath, encoding="utf-8").read()
            assert "name: my-python-api CI/CD" in content


# =============================================================================
# Preset Tests
# =============================================================================
class TestPresets:
    def test_all_presets_generate_valid_output(self):
        gen = GitHubActionsGenerator()
        for name, spec in PRESETS.items():
            import copy

            s = copy.deepcopy(spec)
            output = gen.generate(fill_defaults(s))
            assert "name:" in output, f"Preset '{name}' produced empty output"
            assert "jobs:" in output, f"Preset '{name}' missing jobs"

    def test_language_tools_all_present(self):
        expected = {"python", "node", "go", "dotnet", "terraform"}
        assert expected == set(LANGUAGE_TOOLS.keys())

    def test_preset_names_match_languages(self):
        # Each major language should have a preset
        for lang in ("python", "node", "go", "dotnet", "terraform"):
            assert lang in PRESETS, f"Missing preset for {lang}"

    def test_framework_presets_exist(self):
        """Test that framework-specific presets are available."""
        framework_presets = ["python-django", "python-flask", "python-full", "node-ts"]
        for preset in framework_presets:
            assert preset in PRESETS, f"Missing preset: {preset}"

    def test_preset_count(self):
        """Verify we have the expected number of presets."""
        # 9 presets: python, python-full, python-django, python-flask, node, node-ts, go, dotnet, terraform
        assert len(PRESETS) == 9


# =============================================================================
# CLI Tests
# =============================================================================
class TestCLI:
    def test_cli_version(self):
        from click.testing import CliRunner
        from pipeline_generator.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output

    def test_cli_help(self):
        from click.testing import CliRunner
        from pipeline_generator.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "generate" in result.output
        assert "init" in result.output
        assert "detect" in result.output
        assert "validate" in result.output
        assert "list-presets" in result.output

    def test_cli_list_presets(self):
        from click.testing import CliRunner
        from pipeline_generator.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["list-presets"])
        assert result.exit_code == 0
        assert "python" in result.output.lower()

    def test_cli_validate_nonexistent(self):
        from click.testing import CliRunner
        from pipeline_generator.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["validate", "--spec", "nonexistent.yaml"])
        assert result.exit_code == 1

    def test_cli_generate_demo(self):
        from click.testing import CliRunner
        from pipeline_generator.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["generate", "--demo"])
        assert result.exit_code == 0


# =============================================================================
# Detector Tests
# =============================================================================
class TestDetector:
    def test_detect_python_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "pyproject.toml"), "w").write(
                '[project]\nname = "test"\nrequires-python = ">=3.11"'
            )
            open(os.path.join(tmpdir, "Dockerfile"), "w").write("FROM python:3.11")
            os.makedirs(os.path.join(tmpdir, "tests"))

            result = detect_project(tmpdir)
            assert result.language == "python"
            assert result.has_dockerfile is True
            assert result.has_tests is True
            assert result.confidence > 0.5

    def test_detect_node_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "package.json"), "w").write(
                '{"name": "test", "dependencies": {"express": "^4.0"}}'
            )
            result = detect_project(tmpdir)
            assert result.language == "node"
            assert result.framework == "express"

    def test_detect_go_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "go.mod"), "w").write("module test\n\ngo 1.22\n")
            result = detect_project(tmpdir)
            assert result.language == "go"
            assert result.version == "1.22"

    def test_detect_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = detect_project(tmpdir)
            assert result.language == ""
            assert result.confidence == 0.0
