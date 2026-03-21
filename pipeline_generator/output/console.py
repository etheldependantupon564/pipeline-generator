"""Rich terminal output for pipeline-generator."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

if TYPE_CHECKING:
    from ..detector import DetectionResult
    from ..models import PipelineSpec

# Create console with force_terminal=False to handle test environments gracefully
console = Console()


def print_header(spec: "PipelineSpec") -> None:
    """Print the generation header banner."""
    framework = f" / {spec.project.framework}" if spec.project.framework else ""
    subtitle = (
        f"Generating CI/CD pipelines for: [bold]{spec.project.name}[/bold] "
        f"({spec.project.language.title()} {spec.project.version}{framework})"
    )
    console.print()
    console.print(
        Panel(
            f"[bold cyan]\U0001f680  PIPELINE GENERATOR v1.0.0[/bold cyan]\n\n{subtitle}",
            border_style="cyan",
            padding=(1, 2),
        )
    )


def print_stages(stages: list[str]) -> None:
    """Print the pipeline stages flow."""
    flow = " \u2192 ".join(f"[bold]{s}[/bold]" for s in stages)
    console.print(f"\n\U0001f4cb Stages: {flow}\n")


def print_platform_result(
    icon: str,
    name: str,
    filename: str,
    content: str,
    dry_run: bool = False,
) -> None:
    """Print the result for a single platform generation."""
    console.print(
        "\u2500" * 78,
        style="dim",
    )
    console.print(f"\n{icon}  [bold]{name}[/bold]  \u2192  [cyan]{filename}[/cyan]\n")

    # Preview: first 12 lines
    preview_lines = content.split("\n")[:12]
    remaining = len(content.split("\n")) - 12
    preview = "\n".join(preview_lines)
    if remaining > 0:
        preview += f"\n# ... ({remaining} more lines)"

    console.print(
        Panel(
            Syntax(preview, "yaml", theme="monokai", line_numbers=False),
            title="[dim]Preview[/dim]",
            border_style="dim",
            padding=(0, 1),
        )
    )

    total_lines = len(content.split("\n"))
    if dry_run:
        console.print(f"  \U0001f4dd Would write to [cyan]{filename}[/cyan] ({total_lines} lines)")
    else:
        console.print(f"  \u2705 Written to [cyan]{filename}[/cyan] ({total_lines} lines)")


def print_summary(results: dict[str, str], dry_run: bool = False) -> None:
    """Print the generation summary."""
    total_files = len(results)
    total_lines = sum(len(c.split("\n")) for c in results.values())

    console.print("\n" + "\u2500" * 78, style="dim")

    action = "previewed" if dry_run else "generated"
    summary = (
        f"[bold green]\u2705 {total_files} pipeline configs {action}[/bold green]\n"
        f"\U0001f4c4 {total_lines} total lines of CI/CD configuration\n"
    )

    filenames = "\n".join(f"  \u2022 [cyan]{f}[/cyan]" for f in results.keys())
    summary += f"\n{filenames}"

    console.print(
        Panel(
            summary,
            title="[bold]SUMMARY[/bold]",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print()


def print_detection(result: "DetectionResult") -> None:
    """Print auto-detection results."""
    if not result.language:
        console.print(
            Panel(
                "[yellow]Could not detect project type.[/yellow]\n\n"
                "Try running in a project directory, or use:\n"
                "  [cyan]pipe-gen init --preset python[/cyan]",
                title="\U0001f50d Detection",
                border_style="yellow",
            )
        )
        return

    lines: list[str] = []
    lines.append(f"[bold]Language:[/bold]     {result.language.title()} {result.version}")
    if result.framework:
        lines.append(f"[bold]Framework:[/bold]    {result.framework}")
    lines.append(f"[bold]Pkg Manager:[/bold]  {result.package_manager}")
    docker_status = (
        "[green]\u2705 Found[/green]" if result.has_dockerfile else "[dim]\u2796 Not found[/dim]"
    )
    lines.append(f"[bold]Dockerfile:[/bold]   {docker_status}")
    test_status = (
        "[green]\u2705 Found[/green]" if result.has_tests else "[dim]\u2796 Not found[/dim]"
    )
    lines.append(f"[bold]Tests:[/bold]        {test_status}")

    if result.existing_ci:
        lines.append("")
        lines.append("[bold]Existing CI:[/bold]")
        for ci in result.existing_ci:
            lines.append(f"  \u2022 {ci}")

    lines.append("")
    lines.append("[dim]Suggested command:[/dim]")
    lines.append(f"  [cyan]pipe-gen init --preset {result.language} --name my-project[/cyan]")

    console.print(
        Panel(
            "\n".join(lines),
            title="\U0001f50d  Project Detection",
            border_style="blue",
            padding=(1, 2),
        )
    )


def print_init_success(output_path: str, preset: str) -> None:
    """Print success message after creating a spec file."""
    console.print(
        Panel(
            f"[green]\u2705 Created [bold]{output_path}[/bold][/green]\n\n"
            f"Preset: [cyan]{preset}[/cyan]\n\n"
            "Next steps:\n"
            f"  1. Edit [cyan]{output_path}[/cyan] to match your project\n"
            "  2. Run [cyan]pipe-gen generate --platform all[/cyan]\n"
            "  3. Commit the generated pipeline files",
            title="\U0001f389  Spec File Created",
            border_style="green",
            padding=(1, 2),
        )
    )


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"\n[bold red]\u274c Error:[/bold red] {message}\n")


def print_presets_list(presets: dict) -> None:
    """Print a list of available presets with details."""
    from rich.table import Table

    console.print()
    console.print(
        Panel(
            "[bold cyan]\U0001f4cb  AVAILABLE PRESETS[/bold cyan]\n\n"
            "Use with: [cyan]pipe-gen init --preset <name>[/cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
    )
    console.print()

    table = Table(show_header=True, header_style="bold", expand=True)
    table.add_column("Preset", style="cyan", no_wrap=True)
    table.add_column("Language", style="green")
    table.add_column("Stages")
    table.add_column("Lint Tools", style="dim")
    table.add_column("Security", style="dim")

    for name, spec in presets.items():
        stages = " \u2192 ".join(spec.stages)
        lint_tools = ", ".join(spec.lint.tools) if spec.lint else "-"
        security_tools = ", ".join(spec.security.tools) if spec.security else "-"
        table.add_row(
            name,
            f"{spec.project.language.title()} {spec.project.version}",
            stages,
            lint_tools,
            security_tools,
        )

    console.print(table)
    console.print()


def print_validation_result(
    spec_path: str,
    spec: "PipelineSpec | None",
    valid: bool,
    error: str = "",
) -> None:
    """Print the result of spec file validation."""
    if valid and spec:
        stages = " \u2192 ".join(spec.stages)
        framework = f" ({spec.project.framework})" if spec.project.framework else ""
        content = (
            f"[green]\u2705 Valid spec file![/green]\n\n"
            f"[bold]Project:[/bold]  {spec.project.name}\n"
            f"[bold]Language:[/bold] {spec.project.language.title()} {spec.project.version}{framework}\n"
            f"[bold]Stages:[/bold]   {stages}\n\n"
            "[dim]Ready to generate pipelines:[/dim]\n"
            f"  [cyan]pipe-gen generate --spec {spec_path}[/cyan]"
        )
        console.print(
            Panel(
                content,
                title="\U0001f9ea  Validation Result",
                border_style="green",
                padding=(1, 2),
            )
        )
    else:
        console.print(
            Panel(
                f"[red]\u274c Invalid spec file![/red]\n\n"
                f"[bold]Error:[/bold] {error}\n\n"
                "[dim]Check the file format and try again.[/dim]",
                title="\U0001f9ea  Validation Result",
                border_style="red",
                padding=(1, 2),
            )
        )
