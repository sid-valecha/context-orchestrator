"""CLI interface - the primary user interface for COL."""

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from . import __version__
from .config import load_config
from .core import build_prompt, merge_updates, run_completion
from .core.orchestrator import InvalidResponseError
from .providers import AnthropicProvider, OpenAIProvider
from .schema import Context, ModelResponse, SuggestedContextUpdates
from .storage import init_context, load_context, save_context

app = typer.Typer(
    name="col",
    help="Context Orchestration Layer - Model-agnostic context management for LLMs",
    no_args_is_help=True,
)
console = Console()


def get_provider(provider_name: str, model: Optional[str] = None):
    """Get the appropriate provider instance."""
    if provider_name == "openai":
        return OpenAIProvider(model=model) if model else OpenAIProvider()
    elif provider_name in ("anthropic", "claude"):
        return AnthropicProvider(model=model) if model else AnthropicProvider()
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


@app.command()
def init(
    filename: str = typer.Argument(
        "context.json",
        help="Name of the context file to create",
    ),
):
    """Create a new context file with the default template."""
    path = Path(filename)
    
    try:
        context = init_context(path)
        console.print(f"[green]Created context file:[/green] {path}")
        console.print("\nEdit this file to set your goal, constraints, and initial facts.")
    except FileExistsError:
        console.print(f"[red]Error:[/red] File already exists: {path}", err=True)
        raise typer.Exit(1)


@app.command()
def run(
    context_file: Path = typer.Option(
        ...,
        "--context", "-c",
        help="Path to the context JSON file",
    ),
    provider: str = typer.Option(
        None,
        "--provider", "-p",
        help="LLM provider (openai, anthropic)",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model", "-m",
        help="Model identifier (e.g., gpt-4o, claude-sonnet-4-20250514)",
    ),
    output: Path = typer.Option(
        None,
        "--output", "-o",
        help="Path to save the response",
    ),
    prompt: str = typer.Option(
        ...,
        "--prompt", "-q",
        help="The user prompt/question",
    ),
):
    """Run a completion using the context. Stateless - does not modify context."""
    config = load_config()
    
    # Apply defaults
    if provider is None:
        provider = config.default_provider
    if output is None:
        output = Path(config.default_output_file)
    
    # Load context
    try:
        context = load_context(context_file)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Context file not found: {context_file}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error loading context:[/red] {e}", err=True)
        raise typer.Exit(1)
    
    # Get provider
    try:
        llm = get_provider(provider, model)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error initializing provider:[/red] {e}", err=True)
        raise typer.Exit(1)
    
    # Run completion
    console.print(f"[dim]Running with {provider}...[/dim]")
    
    try:
        response, metadata = run_completion(context, llm, prompt, output)
        
        # Display the answer
        console.print("\n[bold]Answer:[/bold]")
        console.print(Panel(response.answer))
        
        # Display suggested updates if any
        updates = response.suggested_context_updates
        has_updates = any([
            updates.facts,
            updates.decisions,
            updates.constraints,
            updates.tool_outputs,
            updates.open_questions,
        ])
        
        if has_updates:
            console.print("\n[bold]Suggested Context Updates:[/bold]")
            if updates.facts:
                console.print("[cyan]Facts:[/cyan]", updates.facts)
            if updates.decisions:
                console.print("[cyan]Decisions:[/cyan]", updates.decisions)
            if updates.constraints:
                console.print("[cyan]Constraints:[/cyan]", updates.constraints)
            if updates.tool_outputs:
                console.print("[cyan]Tool Outputs:[/cyan]", updates.tool_outputs)
            if updates.open_questions:
                console.print("[cyan]Open Questions:[/cyan]", updates.open_questions)
            
            console.print(f"\n[dim]To apply these updates, run:[/dim]")
            console.print(f"  col apply --context {context_file} --response {output}")
        
        console.print(f"\n[green]Response saved to:[/green] {output}")
        
    except InvalidResponseError as e:
        console.print(f"\n[red]Error:[/red] {e}", err=True)
        console.print(f"\n[yellow]Raw output saved to:[/yellow] {e.output_path}")
        console.print("[dim]Manual intervention required. Edit the file and retry.[/dim]")
        raise typer.Exit(1)


@app.command()
def apply(
    context_file: Path = typer.Option(
        ...,
        "--context", "-c",
        help="Path to the context JSON file",
    ),
    response_file: Path = typer.Option(
        ...,
        "--response", "-r",
        help="Path to the response JSON file from 'col run'",
    ),
    yes: bool = typer.Option(
        False,
        "--yes", "-y",
        help="Skip confirmation prompt",
    ),
):
    """Apply suggested context updates from a response file."""
    # Load context
    try:
        context = load_context(context_file)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Context file not found: {context_file}", err=True)
        raise typer.Exit(1)
    
    # Load response
    try:
        with open(response_file, "r", encoding="utf-8") as f:
            response_data = json.load(f)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Response file not found: {response_file}", err=True)
        raise typer.Exit(1)
    
    # Check if response was valid
    if not response_data.get("valid", False):
        console.print("[red]Error:[/red] Response file contains invalid data.", err=True)
        console.print("[dim]Fix the response file manually or re-run the completion.[/dim]")
        raise typer.Exit(1)
    
    # Extract suggested updates
    parsed = response_data.get("parsed", {})
    updates_data = parsed.get("suggested_context_updates", {})
    updates = SuggestedContextUpdates.model_validate(updates_data)
    
    # Preview changes
    new_context, changes = merge_updates(context, updates)
    
    if not changes:
        console.print("[yellow]No new updates to apply.[/yellow]")
        console.print("[dim]All suggested items already exist in context.[/dim]")
        raise typer.Exit(0)
    
    # Show diff
    console.print("\n[bold]Changes to be applied:[/bold]")
    for field, items in changes.items():
        console.print(f"\n[cyan]{field}:[/cyan]")
        for item in items:
            console.print(f"  [green]+ {item}[/green]")
    
    # Confirm
    if not yes:
        confirm = typer.confirm("\nApply these changes?")
        if not confirm:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)
    
    # Apply
    save_context(context_file, new_context)
    console.print(f"\n[green]Context updated:[/green] {context_file}")


@app.command()
def metrics(
    context_file: Path = typer.Option(
        ...,
        "--context", "-c",
        help="Path to the context JSON file",
    ),
):
    """Show metrics for a context file."""
    # Load context
    try:
        context = load_context(context_file)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Context file not found: {context_file}", err=True)
        raise typer.Exit(1)
    
    # File stats
    file_size = context_file.stat().st_size
    
    # Count items
    table = Table(title="Context Metrics")
    table.add_column("Field", style="cyan")
    table.add_column("Count", justify="right")
    
    table.add_row("Goal", "1" if context.goal else "0")
    table.add_row("Constraints", str(len(context.constraints)))
    table.add_row("Facts", str(len(context.facts)))
    table.add_row("Decisions", str(len(context.decisions)))
    table.add_row("Tool Outputs", str(len(context.tool_outputs)))
    table.add_row("Open Questions", str(len(context.open_questions)))
    
    console.print(table)
    
    # File size
    console.print(f"\n[dim]File size:[/dim] {file_size:,} bytes")
    
    # Build prompt to estimate tokens (rough)
    prompt = build_prompt(context)
    char_count = len(prompt)
    estimated_tokens = char_count // 4  # Rough approximation
    
    console.print(f"[dim]System prompt chars:[/dim] {char_count:,}")
    console.print(f"[dim]Estimated tokens:[/dim] ~{estimated_tokens:,}")


@app.command()
def version():
    """Show the COL version."""
    console.print(f"col {__version__}")


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
