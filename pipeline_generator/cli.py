"""CLI entry point for pipeline-generator."""

from __future__ import annotations

import click

from . import __version__
from .generator import PLATFORMS, create_spec_file, generate_pipelines, load_spec
from .output.console import (
    print_detection,
    print_error,
    print_header,
    print_init_success,
    print_platform_result,
    print_stages,
    print_summary,
)
from .presets import PRESETS

PRESET_CHOICES = list(PRESETS.keys())
PLATFORM_CHOICES = ["all", "github", "azure", "gitlab"]


@click.group()
@click.version_option(version=__version__, prog_name="pipeline-generator")
def cli() -> None:
    """Generate production-ready CI/CD pipeline configs from a simple YAML spec.

    \b
    Supported platforms:
      • GitHub Actions  (.github/workflows/ci.yml)
      • Azure DevOps    (azure-pipelines.yml)
      • GitLab CI       (.gitlab-ci.yml)

    \b
    Quick start:
      pipe-gen init --preset python
      pipe-gen generate --platform all
    """


@cli.command()
@click.option(
    "--preset",
    "-p",
    type=click.Choice(PRESET_CHOICES),
    default="python",
    help="Language preset to use.",
)
@click.option("--name", "-n", default="", help="Project name (overrides preset default).")
@click.option(
    "--output",
    "-o",
    default="pipeline.yaml",
    help="Output file path for the spec.",
)
def init(preset: str, name: str, output: str) -> None:
    """Create a pipeline.yaml spec file from a preset.

    \b
    Examples:
      pipe-gen init --preset python --name my-api
      pipe-gen init --preset node
      pipe-gen init --preset go --output ci-spec.yaml
    """
    try:
        create_spec_file(preset=preset, output_path=output, project_name=name)
        print_init_success(output, preset)
    except Exception as e:
        print_error(str(e))
        raise SystemExit(1) from None


@cli.command()
@click.option("--path", default=".", help="Project directory to scan.")
def detect(path: str) -> None:
    """Auto-detect project type and configuration.

    Scans the given directory for project files (package.json, pyproject.toml,
    go.mod, etc.) and shows what was found.
    """
    from .detector import detect_project

    result = detect_project(path)
    print_detection(result)


@cli.command("list-presets")
def list_presets() -> None:
    """List all available presets with details.

    \b
    Shows preset name, language, stages, and tools.
    """
    from .output.console import print_presets_list

    print_presets_list(PRESETS)


@cli.command()
@click.option(
    "--spec",
    "-s",
    default="pipeline.yaml",
    help="Path to the spec YAML file.",
)
def validate(spec: str) -> None:
    """Validate a pipeline spec file.

    \b
    Checks the spec file for syntax errors and missing required fields.

    \b
    Examples:
      pipe-gen validate                         # Validate pipeline.yaml
      pipe-gen validate --spec my-pipeline.yaml
    """
    from .output.console import print_validation_result

    try:
        pipeline_spec = load_spec(spec)
        print_validation_result(spec, pipeline_spec, valid=True)
    except FileNotFoundError:
        print_error(f"Spec file '{spec}' not found.")
        raise SystemExit(1) from None
    except Exception as e:
        print_validation_result(spec, None, valid=False, error=str(e))
        raise SystemExit(1) from None


@cli.command()
@click.option(
    "--platform",
    "-p",
    type=click.Choice(PLATFORM_CHOICES),
    default="all",
    help="Target platform(s).",
)
@click.option(
    "--spec",
    "-s",
    default="pipeline.yaml",
    help="Path to the spec YAML file.",
)
@click.option(
    "--preset",
    type=click.Choice(PRESET_CHOICES),
    default=None,
    help="Use a built-in preset instead of a spec file.",
)
@click.option(
    "--output-dir",
    "-o",
    default=".",
    help="Output directory for generated files.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview generated configs without writing files.",
)
@click.option(
    "--demo",
    is_flag=True,
    help="Generate a demo using the python-full preset (implies --dry-run).",
)
def generate(
    platform: str,
    spec: str,
    preset: str | None,
    output_dir: str,
    dry_run: bool,
    demo: bool,
) -> None:
    """Generate CI/CD pipeline configs for one or all platforms.

    \b
    Examples:
      pipe-gen generate                         # From pipeline.yaml, all platforms
      pipe-gen generate -p github               # GitHub Actions only
      pipe-gen generate --preset python -p all   # From preset, all platforms
      pipe-gen generate --demo                   # Demo with python-full preset
    """
    try:
        if demo:
            preset = "python-full"
            dry_run = True

        if preset:
            import copy

            pipeline_spec = copy.deepcopy(PRESETS[preset])
        else:
            try:
                pipeline_spec = load_spec(spec)
            except FileNotFoundError:
                print_error(
                    f"Spec file '{spec}' not found.\n\n"
                    "  Create one with:  [cyan]pipe-gen init --preset python[/cyan]\n"
                    "  Or use a preset:  [cyan]pipe-gen generate --preset python[/cyan]"
                )
                raise SystemExit(1) from None

        # Print header
        print_header(pipeline_spec)
        print_stages(pipeline_spec.stages)

        # Generate
        results = generate_pipelines(
            spec=pipeline_spec,
            platform=platform,
            output_dir=output_dir,
            dry_run=dry_run,
        )

        # Print each platform result
        platform_list = list(PLATFORMS.values()) if platform == "all" else [PLATFORMS[platform]]

        for gen in platform_list:
            if gen.filename in results:
                print_platform_result(
                    icon=gen.icon,
                    name=gen.name,
                    filename=gen.filename,
                    content=results[gen.filename],
                    dry_run=dry_run,
                )

        print_summary(results, dry_run=dry_run)

    except SystemExit:
        raise
    except Exception as e:
        print_error(str(e))
        raise SystemExit(1) from None


if __name__ == "__main__":
    cli()
