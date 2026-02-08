"""
Beautiful CLI interface for Alfred
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import print as rprint
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import sys
import re
import subprocess
import webbrowser
import subprocess
from .api_balance_tracker import APIBalanceTracker
from .github_integration import GitHubIntegration
from .github_auth import GitHubAuth
from .review_history import ReviewHistory
from .agent import CodeReviewAgent
from .config import Config

# Load environment variables
load_dotenv()

# Initialize
app = typer.Typer(
    name="alfred",
    help="🤖 AI-powered code reviewer using Claude",
    add_completion=False
)
console = Console()


def print_banner():
    """Print simple banner"""
    console.print("\n[bold cyan]🤖 Alfred[/bold cyan] [dim]v0.1.0[/dim]")
    console.print("[dim]AI-Powered Code Review[/dim]\n")

def interactive_setup() -> Optional[str]:
    """
    Interactive setup when no API key is found
    Returns the API key if user provides one, None if they skip
    """
    console.print("\n[yellow]❌ No API key found![/yellow]\n")
    console.print("alfred needs an Anthropic API key to work.\n")
    console.print("[cyan]Get your API key:[/cyan]")
    console.print("  → https://console.anthropic.com/\n")
    console.print("[dim]💡 Tip: New accounts get $5 in free credits![/dim]\n")
    
    # Ask if they want to set it up now
    setup_now = Confirm.ask("Would you like to set up your API key now?", default=True)
    
    if not setup_now:
        console.print("\n[yellow]Setup skipped. You can set up later with:[/yellow]")
        console.print("  alfred setup")
        console.print("\n[yellow]Or set environment variable:[/yellow]")
        console.print("  export ANTHROPIC_API_KEY='your-key-here'\n")
        return None
    
    # Get API key from user
    api_key = Prompt.ask(
        "\n[cyan]Paste your API key[/cyan]",
        password=True
    )
    
    if not api_key or not api_key.strip():
        console.print("[red]No key provided. Setup cancelled.[/red]")
        return None
    
    api_key = api_key.strip()
    
    # Validate key format (basic check)
    if not api_key.startswith("sk-ant-"):
        console.print("\n[yellow]⚠️  Warning: API key doesn't look valid (should start with 'sk-ant-')[/yellow]")
        continue_anyway = Confirm.ask("Continue anyway?", default=False)
        if not continue_anyway:
            return None
    
    # Save to config
    config = Config()
    config.save_api_key(api_key)
    
    console.print(f"\n[green]✅ API key saved to {config.get_config_location()}[/green]")
    console.print("[green]You're all set! alfred will use this key for all reviews.[/green]\n")
    
    return api_key

# GIT HELPER
def get_git_diff(staged: bool = True, since: Optional[str] = None) -> tuple[str, str]:
    """
    Get git diff
    
    Args:
        staged: Get staged changes (True) or unstaged (False)
        since: Compare against branch/commit (e.g., 'main', 'HEAD~1')
        
    Returns:
        Tuple of (diff_output, description)
    """
    try:
        if since:
            # Compare against branch/commit
            result = subprocess.run(
                ['git', 'diff', since],
                capture_output=True,
                text=True,
                encoding='utf-8',      
                errors='replace',  
                check=True
            )
            description = f"changes since {since}"
        elif staged:
            # Staged changes
            result = subprocess.run(
                ['git', 'diff', '--cached'],
                capture_output=True,
                text=True,
                encoding='utf-8',      
                errors='replace',  
                check=True
            )
            description = "staged changes"
        else:
            # Unstaged changes
            result = subprocess.run(
                ['git', 'diff'],
                capture_output=True,
                text=True,
                encoding='utf-8',      
                errors='replace',  
                check=True
            )
            description = "unstaged changes"
        
        return result.stdout, description
    
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Git command failed: {e.stderr}")
    except FileNotFoundError:
        raise ValueError("Git is not installed or not in PATH")
    

# COMMANDS
@app.command()
def history(
    action: str = typer.Argument("list", help="Action: list, show, search, stats, clear"),
    value: Optional[str] = typer.Argument(None, help="Review ID or search query"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of reviews to show"),
    file: Optional[str] = typer.Option(None, "--file", "-f", help="Filter by filename")
):
    """
    View review history (git log style)
    
    Examples:
        alfred history                  # List recent reviews
        alfred history list --limit 20  # Last 20 reviews
        alfred history show 5           # Show review #5
        alfred history search "SQL"     # Search for SQL issues
        alfred history stats            # Show statistics
        alfred history clear            # Clear all history
        alfred history --file script.py # Reviews of script.py
    """
    config = Config()
    history_tracker = ReviewHistory(config.config_dir)
    
    if action == "list" or action == "history":
        # List recent reviews (git log style!)
        if file:
            reviews = history_tracker.get_by_file(file)
            console.print(f"\n[bold cyan]📚 Review History for {file}[/bold cyan]\n")
        else:
            reviews = history_tracker.get_recent(limit)
            console.print(f"\n[bold cyan]📚 Recent Reviews[/bold cyan]\n")
        
        if not reviews:
            console.print("[yellow]No reviews found yet[/yellow]\n")
            console.print("[dim]Reviews will appear here after running:[/dim]")
            console.print("  [cyan]alfred review <file>[/cyan]\n")
            return
        
        # Display in git log style
        for review in reviews:
            # Review ID (like git commit hash)
            console.print(f"[yellow]review {review['id']}[/yellow]")
            
            # File and date
            console.print(f"📄 File:  [cyan]{review['filename']}[/cyan]")
            console.print(f"📅 Date:  {review['date']}")
            
            # Focus area with emoji
            focus_emojis = {
                "general": "🔍",
                "security": "🔒",
                "performance": "⚡",
                "style": "🎨",
                "bugs": "🐛"
            }
            emoji = focus_emojis.get(review['focus'], "🔍")
            console.print(f"{emoji} Focus: {review['focus']}")
            
            # Score with color coding
            if review['score']:
                score = review['score']
                if score >= 8:
                    color = "green"
                elif score >= 6:
                    color = "yellow"
                else:
                    color = "red"
                console.print(f"⭐ Score: [{color}]{score}/10[/{color}]")
            
            # Cost
            if review['cost']:
                console.print(f"💰 Cost:  [yellow]${review['cost']:.4f}[/yellow]")
            
            console.print()  # Blank line between reviews
        
        console.print(f"[dim]View details:[/dim] [cyan]alfred history show <id>[/cyan]\n")
    
    elif action == "show":
        # Show specific review
        if value is None:
            console.print("[red]❌ Please specify review ID[/red]")
            console.print("\n[cyan]Example:[/cyan] alfred history show 5\n")
            sys.exit(1)
        
        try:
            review_id = int(value)
        except ValueError:
            console.print("[red]❌ Review ID must be a number[/red]")
            sys.exit(1)
        
        review = history_tracker.get_review(review_id)
        
        if not review:
            console.print(f"[red]❌ Review #{review_id} not found[/red]\n")
            sys.exit(1)
        
        # Display review header
        console.print(f"\n[bold cyan]Review #{review['id']}[/bold cyan]\n")
        console.print(f"📄 File:  [cyan]{review['filepath']}[/cyan]")
        console.print(f"📅 Date:  {review['date']}")
        console.print(f"🔍 Focus: {review['focus']}")
        
        if review['score']:
            score = review['score']
            if score >= 8:
                color = "green"
            elif score >= 6:
                color = "yellow"
            else:
                color = "red"
            console.print(f"⭐ Score: [{color}]{score}/10[/{color}]")
        
        if review['cost']:
            console.print(f"💰 Cost:  [yellow]${review['cost']:.4f}[/yellow]")
        
        console.print("\n" + "="*70 + "\n")
        
        # Show review content
        md = Markdown(review['review'])
        console.print(Panel(md, title="📋 Review", border_style="cyan"))
        console.print()
    
    elif action == "search":
        # Search reviews
        if value is None:
            console.print("[red]❌ Please specify search query[/red]")
            console.print("\n[cyan]Example:[/cyan] alfred history search SQL\n")
            sys.exit(1)
        
        reviews = history_tracker.search(value)
        
        console.print(f"\n[bold cyan]🔍 Search: '{value}'[/bold cyan]\n")
        
        if not reviews:
            console.print("[yellow]No matching reviews found[/yellow]\n")
            return
        
        console.print(f"[green]Found {len(reviews)} match{'es' if len(reviews) != 1 else ''}[/green]\n")
        
        # Display search results (compact)
        for review in reviews[:limit]:
            console.print(f"[yellow]review {review['id']}[/yellow] - [cyan]{review['filename']}[/cyan]")
            console.print(f"  📅 {review['date']}")
            if review['score']:
                score = review['score']
                if score >= 8:
                    color = "green"
                elif score >= 6:
                    color = "yellow"
                else:
                    color = "red"
                console.print(f"  ⭐ [{color}]{score}/10[/{color}]")
            console.print()
        
        if len(reviews) > limit:
            console.print(f"[dim]Showing {limit} of {len(reviews)}. Use --limit to see more.[/dim]\n")
        
        console.print(f"[dim]View details:[/dim] [cyan]alfred history show <id>[/cyan]\n")
    
    elif action == "stats":
        # Show statistics
        stats = history_tracker.get_stats()
        
        console.print("\n[bold cyan]📊 Review Statistics[/bold cyan]\n")
        
        if stats['total_reviews'] == 0:
            console.print("[yellow]No reviews yet[/yellow]\n")
            return
        
        console.print(f"📝 Total Reviews:     {stats['total_reviews']}")
        console.print(f"📂 Files Reviewed:    {stats['files_reviewed']}")
        console.print(f"⭐ Average Score:     {stats['avg_score']:.1f}/10")
        
        if stats['total_cost'] > 0:
            console.print(f"💰 Total Cost:        [yellow]${stats['total_cost']:.2f}[/yellow]")
        
        # Focus breakdown
        if stats['focus_breakdown']:
            console.print(f"\n[bold]Reviews by Focus:[/bold]")
            for focus, count in stats['focus_breakdown'].items():
                focus_emojis = {
                    "general": "🔍",
                    "security": "🔒",
                    "performance": "⚡",
                    "style": "🎨",
                    "bugs": "🐛"
                }
                emoji = focus_emojis.get(focus, "🔍")
                console.print(f"  {emoji} {focus}: {count}")
        
        console.print()
    
    elif action == "clear":
        # Clear all history
        stats = history_tracker.get_stats()
        
        if stats['total_reviews'] == 0:
            console.print("\n[yellow]No reviews to clear[/yellow]\n")
            return
        
        console.print(f"\n[yellow]⚠️  This will delete {stats['total_reviews']} reviews[/yellow]")
        confirm = Confirm.ask("Are you sure?", default=False)
        
        if confirm:
            count = history_tracker.clear_all()
            console.print(f"\n[green]✅ Deleted {count} reviews[/green]\n")
        else:
            console.print("\n[yellow]Cancelled[/yellow]\n")
    
    else:
        console.print(f"[red]❌ Unknown action: {action}[/red]\n")
        console.print("[cyan]Valid actions:[/cyan]")
        console.print("  alfred history              # List recent")
        console.print("  alfred history show 5       # Show review #5")
        console.print("  alfred history search SQL   # Search reviews")
        console.print("  alfred history stats        # Statistics")
        console.print("  alfred history clear        # Clear all\n")
        sys.exit(1)


@app.command()
def review_git(
    staged: bool = typer.Option(True, "--staged/--unstaged", help="Review staged or unstaged changes"),
    since: Optional[str] = typer.Option(None, "--since", help="Review changes since branch/commit (e.g., main, HEAD~1)"),
    focus: str = typer.Option("general", "--focus", "-f", help="Review focus"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ANTHROPIC_API_KEY"),
    show_cost: bool = typer.Option(True, "--show-cost/--no-cost"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    force: bool = typer.Option(False, "--force", help="Bypass balance warnings")
):
    """
    Review git changes with AI
    
    Examples:
        alfred review-git                     # Review staged changes
        alfred review-git --unstaged          # Review unstaged changes
        alfred review-git --since main        # Review changes since main branch
        alfred review-git --since HEAD~3      # Review last 3 commits
        alfred review-git --focus security    # Security-focused review
    """
    if verbose:
        print_banner()
    
    # Check API key
    config = Config()
    anthropic_key = config.get_api_key(api_key)
    
    if not anthropic_key:
        console.print("[red]❌ Anthropic API key required. Run 'alfred setup'[/red]")
        sys.exit(1)
    
    # Check balance
    if not force:
        balance_tracker = APIBalanceTracker(config.config_dir)
        should_proceed, warning = balance_tracker.check_before_review(estimated_cost=0.15)
        
        if not should_proceed:
            console.print(f"\n{warning}\n")
            sys.exit(1)
        
        if warning:
            console.print(f"\n{warning}\n")
            proceed = Confirm.ask("Continue anyway?", default=True)
            if not proceed:
                console.print("\n[yellow]Review cancelled[/yellow]\n")
                sys.exit(0)
    
    try:
        # Get git diff
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Getting git diff...", total=None)
            diff, description = get_git_diff(staged=staged, since=since)
        
        # Check if there are changes
        if not diff.strip():
            console.print(f"\n[yellow]No {description} to review[/yellow]\n")
            if staged:
                console.print("[dim]Tip: Use --unstaged to review uncommitted changes[/dim]")
            elif not since:
                console.print("[dim]Tip: Stage changes with 'git add' first[/dim]")
            console.print()
            sys.exit(0)
        
        # Show what we're reviewing
        console.print(f"\n📝 Reviewing: [cyan]{description}[/cyan]")
        console.print(f"🎯 Focus: [cyan]{focus}[/cyan]\n")
        
        # Count changes
        lines = diff.split('\n')
        additions = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))
        
        console.print(f"📊 Changes: [green]+{additions}[/green] [red]-{deletions}[/red]\n")
        
        # Review with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("🤖 Claude is reviewing your changes...", total=None)
            agent = CodeReviewAgent(api_key=anthropic_key)
            review_result, cost_info = agent.review_git_diff(diff, focus, track_cost=show_cost)
        
        # Display results
        console.print("\n" + "="*70 + "\n")
        md = Markdown(review_result)
        console.print(Panel(md, title="📋 Git Diff Review", border_style="green"))
        
        # Save to history
        from .review_history import ReviewHistory
        history_tracker = ReviewHistory(config.config_dir)
        review_id = history_tracker.save_review(
            filepath=f"git-{description.replace(' ', '-')}",
            review_text=review_result,
            focus=focus,
            cost=cost_info['cost'] if cost_info else None
        )
        
        # Show cost
        if show_cost and cost_info:
            console.print("\n💰 [bold cyan]Cost Information:[/bold cyan]")
            console.print(f"   Cost: [yellow]${cost_info['cost']:.4f}[/yellow]")
            console.print(f"   [dim]Saved as review #{review_id}[/dim]")
            
            # Show balance
            balance_tracker = APIBalanceTracker(config.config_dir)
            status = balance_tracker.get_detailed_status()
            if status['has_balance']:
                console.print(f"   Balance: ${status['balance']:.2f} (~{status['estimated_reviews_left']} reviews left)")
        
        console.print("\n[green]✅ Review complete![/green]")
        console.print(f"[dim]View again:[/dim] [cyan]alfred history show {review_id}[/cyan]\n")
        
    except ValueError as e:
        console.print(f"\n[red]❌ Error: {str(e)}[/red]\n")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ Error: {str(e)}[/red]")
        if verbose:
            import traceback
            console.print("\n[dim]" + traceback.format_exc() + "[/dim]")
        sys.exit(1)

@app.command()
def review(
    filepath: str = typer.Argument(..., help="Path to the code file to review"),
    focus: str = typer.Option(
        "general", 
        "--focus", 
        "-f",
        help="Review focus: general, security, performance, style, bugs"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        "-k",
        help="Anthropic API key (overrides config file)",
        envvar="ANTHROPIC_API_KEY"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output"
    ),
    show_cost: bool = typer.Option(
        True,
        "--show-cost/--no-cost",
        help="Show cost information after review"
    )
):
    """
    Review a code file with AI
    
    Example:
        alfred review script.py
        alfred review app.js --focus security
        alfred review main.go -f performance
    """
    
    if verbose:
        print_banner()
    
    # Validate file
    path = Path(filepath)
    if not path.exists():
        console.print(f"[red]❌ Error: File not found: {filepath}[/red]")
        sys.exit(1)
    
    # Validate focus
    valid_focuses = ["general", "security", "performance", "style", "bugs"]
    if focus not in valid_focuses:
        console.print(f"[red]❌ Invalid focus. Choose from: {', '.join(valid_focuses)}[/red]")
        sys.exit(1)
    
    # Check for API key and offer interactive setup if missing
    config = Config()
    current_key = config.get_api_key(api_key)
    
    if not current_key:
        # Interactive setup
        setup_key = interactive_setup()
        if not setup_key:
            sys.exit(1)
        # Use the newly set up key
        api_key = setup_key
    
    try:
        # Initialize agent
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task("Initializing alfred...", total=None)
            agent = CodeReviewAgent(api_key=api_key)
        
        # Show what we're reviewing
        console.print(f"\n📄 Reviewing: [cyan]{filepath}[/cyan]")
        console.print(f"🎯 Focus: [cyan]{focus}[/cyan]\n")
        
        # Review with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("🤖 Claude is reviewing your code...", total=None)
            review_result, cost_info = agent.review_code(filepath, focus, track_cost=show_cost)
        
        # Display results in a nice panel
        console.print("\n" + "="*70 + "\n")
        md = Markdown(review_result)
        console.print(Panel(md, title="📋 Code Review Results", border_style="green"))

        # save to history
        history_tracker = ReviewHistory(config.config_dir)
        review_id = history_tracker.save_review(
            filepath=filepath,
            review_text=review_result,
            focus=focus,
            cost=cost_info['cost'] if cost_info else None
        )

        # Show cost information if enabled
        if show_cost and cost_info:
            console.print("\n💰 [bold cyan]Cost Information:[/bold cyan]")
            console.print(f"   Input tokens:  {cost_info['input_tokens']:,}")
            console.print(f"   Output tokens: {cost_info['output_tokens']:,}")
            console.print(f"   Total tokens:  {cost_info['total_tokens']:,}")
            console.print(f"   Cost:          [yellow]${cost_info['cost']:.4f}[/yellow]")
            
            # Show session total
            session = agent.cost_tracker.get_session_summary()
            if session['reviews'] > 1:
                console.print(f"\n   Session total: ${session['total_cost']:.4f} ({session['reviews']} reviews)")
        
        console.print("\n[green]✅ Review complete![/green]\n")
        
    except ValueError as e:
        console.print(f"[red]❌ Configuration Error: {str(e)}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        if verbose:
            import traceback
            console.print("\n[dim]" + traceback.format_exc() + "[/dim]")
        sys.exit(1)


@app.command()
def setup():
    """Configure alfred (API key, preferences)"""
    print_banner()
    
    console.print("\n[bold]alfred Setup[/bold]\n")
    
    config = Config()
    
    # Show current configuration
    if config.has_api_key():
        masked_key = config.get_masked_key()
        console.print(f"[green]✅ Current API key: {masked_key}[/green]")
        console.print(f"[dim]Stored in: {config.get_config_location()}[/dim]\n")
        
        change = Confirm.ask("Would you like to change your API key?", default=False)
        if not change:
            console.print("\n[green]Setup complete! No changes made.[/green]\n")
            return
    else:
        console.print("[yellow]No API key configured yet.[/yellow]\n")
    
    # Get new API key
    console.print("[cyan]Get your API key from:[/cyan]")
    console.print("  → https://console.anthropic.com/\n")
    
    api_key = Prompt.ask(
        "[cyan]Enter your Anthropic API key[/cyan]",
        password=True
    )
    
    if not api_key or not api_key.strip():
        console.print("[red]No key provided. Setup cancelled.[/red]")
        return
    
    api_key = api_key.strip()
    
    # Validate key format
    if not api_key.startswith("sk-ant-"):
        console.print("\n[yellow]⚠️  Warning: API key doesn't look valid (should start with 'sk-ant-')[/yellow]")
        continue_anyway = Confirm.ask("Save anyway?", default=False)
        if not continue_anyway:
            console.print("[red]Setup cancelled.[/red]")
            return
    
    # Save configuration
    config.save_api_key(api_key)
    
    console.print(f"\n[green]✅ API key saved to {config.get_config_location()}[/green]")
    console.print("[green]🎉 Setup complete! Try running:[/green]")
    console.print("  alfred review <your-file>\n")

@app.command()
def revert():
    """Revert alfred configuration to defaults"""
    config = Config()
    
    if config.has_api_key():
        confirm = Confirm.ask(
            "[yellow]⚠️  This will delete your saved API key. Continue?[/yellow]",
            default=False
        )
        if confirm:
            config.clear_config()
            console.print("[green]✅ Configuration reverted to defaults.[/green]")
        else:
            console.print("[yellow]Revert cancelled.[/yellow]")
    else:
        console.print("[yellow]No configuration to revert.[/yellow]")   

@app.command()
def config_cmd(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    reset: bool = typer.Option(False, "--reset", help="Clear all configuration")
):
    """Manage alfred configuration"""
    
    config = Config()
    
    if reset:
        if config.has_api_key():
            confirm = Confirm.ask(
                "[yellow]⚠️  This will delete your saved API key. Continue?[/yellow]",
                default=False
            )
            if confirm:
                config.clear_config()
                console.print("[green]✅ Configuration cleared.[/green]")
            else:
                console.print("[yellow]Reset cancelled.[/yellow]")
        else:
            console.print("[yellow]No configuration to reset.[/yellow]")
        return
    
    if show or True:  # Default to showing config
        console.print("\n[bold]alfred Configuration[/bold]\n")
        
        if config.has_api_key():
            masked_key = config.get_masked_key()
            console.print(f"[green]API Key: {masked_key}[/green]")
            console.print(f"[dim]Location: {config.get_config_location()}[/dim]")
        else:
            console.print("[yellow]API Key: Not configured[/yellow]")
            console.print("\n[cyan]Run 'alfred setup' to configure your API key[/cyan]")
        
        console.print()


@app.command()
def costs(
    limit: int = typer.Option(
        10,
        "--limit",
        "-n",
        help="Number of recent reviews to show"
    ),
    total: bool = typer.Option(
        False,
        "--total",
        "-t",
        help="Show total usage statistics"
    )
):
    """
    View cost tracking and usage statistics
    
    Example:
        alfred costs              # Show recent reviews
        alfred costs --total      # Show all-time stats
        alfred costs --limit 20   # Show last 20 reviews
    """
    console.print("\n💰 [bold cyan]Alfred Cost Tracker[/bold cyan]\n")
    
    config = Config()
    from .cost_tracker import CostTracker
    tracker = CostTracker(config.config_dir)
    
    if total:
        # Show all-time statistics
        stats = tracker.get_total_usage()
        
        if stats['total_reviews'] == 0:
            console.print("[yellow]No reviews tracked yet.[/yellow]")
            console.print("\n[dim]Costs will be tracked automatically when you run 'alfred review'[/dim]\n")
            return
        
        console.print("[bold]All-Time Statistics:[/bold]")
        console.print(f"  Total reviews:    {stats['total_reviews']:,}")
        console.print(f"  Total tokens:     {stats['total_tokens']:,}")
        console.print(f"  Total cost:       [yellow]${stats['total_cost']:.2f}[/yellow]")
        console.print(f"  Avg per review:   ${stats['avg_cost_per_review']:.4f}")
        console.print(f"  Avg tokens/review: {stats['avg_tokens_per_review']:.0f}")
    else:
        # Show recent reviews
        recent = tracker.get_recent_reviews(limit)
        
        if not recent:
            console.print("[yellow]No reviews tracked yet.[/yellow]")
            console.print("\n[dim]Costs will be tracked automatically when you run 'alfred review'[/dim]\n")
            return
        
        console.print(f"[bold]Last {len(recent)} Reviews:[/bold]\n")
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Date", style="dim")
        table.add_column("File", style="cyan")
        table.add_column("Tokens", justify="right")
        table.add_column("Cost", justify="right", style="yellow")
        
        for review in recent:
            # Parse timestamp
            from datetime import datetime
            dt = datetime.fromisoformat(review['timestamp'])
            date_str = dt.strftime("%b %d, %H:%M")
            
            # Get filename or show "N/A"
            filename = review.get('filepath', 'N/A')
            if filename and filename != 'N/A':
                filename = Path(filename).name
            
            # Format numbers
            tokens = f"{review['total_tokens']:,}"
            cost = f"${review['cost']:.4f}"
            
            table.add_row(date_str, filename, tokens, cost)
        
        console.print(table)
        
        # Show total for displayed reviews
        total_cost = sum(r['cost'] for r in recent)
        console.print(f"\n[dim]Total shown: ${total_cost:.4f}[/dim]")
    
    console.print()


@app.command()
def version():
    """Show alfred version"""
    print_banner()
    console.print("[cyan]Version:[/cyan] 0.1.0")
    console.print("[cyan]Model:[/cyan] claude-sonnet-4-20250514")
    console.print("[cyan]Config:[/cyan] ~/.alfred/config.json")



@app.command(name="github-login")
def github_login():
    """
        Login to GitHub (opens browser)
        Example:
            alfred github-login
    """ 
    print_banner()

    config = Config()
    github_auth = GitHubAuth(config.config_dir)

    # Check if already logged in
    if github_auth.is_logged_in():
        user_info = github_auth.get_user_info()
        username = user_info.get('login', 'Unknown') if user_info else 'Unknown'
        
        console.print(f"\n[yellow]Already logged in as:[/yellow] [cyan]{username}[/cyan]")
        
        reauth = Confirm.ask("Would you like to login again?", default=False)
        if not reauth:
            console.print("[green]Keeping current session[/green]\n")
            return
        
        github_auth.logout()

    console.print("\n[bold cyan]🔐 GitHub Login[/bold cyan]\n")
    console.print("Alfred needs permission to access your GitHub repositories.")
    console.print("[dim]This uses GitHub's secure OAuth flow - Alfred never sees your password.[/dim]\n")

    # Start login flow
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Initiating GitHub login...", total=None)
        login_result = github_auth.login()
        
        if not login_result.get('success'):
            console.print(f"[red]❌ {login_result.get('error', 'Login failed')}[/red]\n")
            return

    # Display auth code
    user_code = login_result['user_code']
    verification_uri = login_result['verification_uri']
    device_code = login_result['device_code']
    interval = login_result.get('interval', 5)

    # Create display panel
    auth_panel = Panel(
        f"[bold yellow]{user_code}[/bold yellow]\n\n"
        f"[dim]Visit: {verification_uri}[/dim]",
        title="🔑 Your Code",
        border_style="cyan"
    )

    console.print("\n")
    console.print(auth_panel)
    console.print("\n[bold]Steps:[/bold]")
    console.print("  1. A browser window will open")
    console.print("  2. Enter the code shown above")
    console.print("  3. Authorize Alfred")
    console.print("\n[dim]Waiting for authorization...[/dim]\n")

    # Open browser
    try:
        webbrowser.open(verification_uri)
    except:
        console.print("[yellow]⚠️  Could not open browser automatically[/yellow]")

    # Poll for token
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Waiting for authorization...", total=None)
        result = github_auth.poll_for_token(device_code, interval)

    if result['success']:
        user_info = github_auth.get_user_info()
        username = user_info.get('login', 'Unknown') if user_info else 'Unknown'
        
        console.print("\n[green]✅ Successfully logged in to GitHub![/green]")
        console.print(f"[green]Logged in as:[/green] [cyan]{username}[/cyan]\n")
        console.print("[dim]You can now use:[/dim]")
        console.print("  • [cyan]alfred review-pr <url>[/cyan]")
        console.print("  • [cyan]alfred review-pr <number> --comment[/cyan]\n")
    else:
        error = result.get('error', 'Unknown error')
        console.print(f"\n[red]❌ Login failed: {error}[/red]\n")

@app.command()
def git_status():
    """
    Show git status with review suggestions
    
    Shows what files have changed and suggests review commands
    """
    try:
        # Get git status
        result = subprocess.run(
            ['git', 'status', '--short'],
            capture_output=True,
            text=True,
            check=True
        )
        
        if not result.stdout.strip():
            console.print("\n[green]✅ Working tree clean[/green]\n")
            return
        
        console.print("\n[bold cyan]📊 Git Status[/bold cyan]\n")
        
        # Parse status
        staged = []
        unstaged = []
        untracked = []
        
        for line in result.stdout.strip().split('\n'):
            status = line[:2]
            filename = line[3:]
            
            if status[0] != ' ' and status[0] != '?':
                staged.append(filename)
            if status[1] != ' ' and status[1] != '?':
                unstaged.append(filename)
            if status == '??':
                untracked.append(filename)
        
        # Show changes
        if staged:
            console.print(f"[green]Staged changes:[/green] {len(staged)} files")
            for f in staged[:5]:
                console.print(f"  [green]✓[/green] {f}")
            if len(staged) > 5:
                console.print(f"  [dim]... and {len(staged) - 5} more[/dim]")
            console.print()
        
        if unstaged:
            console.print(f"[yellow]Unstaged changes:[/yellow] {len(unstaged)} files")
            for f in unstaged[:5]:
                console.print(f"  [yellow]M[/yellow] {f}")
            if len(unstaged) > 5:
                console.print(f"  [dim]... and {len(unstaged) - 5} more[/dim]")
            console.print()
        
        if untracked:
            console.print(f"[dim]Untracked files:[/dim] {len(untracked)} files")
            console.print()
        
        # Suggest commands
        console.print("[bold]💡 Review suggestions:[/bold]")
        if staged:
            console.print("  [cyan]alfred review-git[/cyan]                # Review staged changes")
        if unstaged:
            console.print("  [cyan]alfred review-git --unstaged[/cyan]    # Review unstaged changes")
        console.print("  [cyan]alfred review-git --since main[/cyan]    # Review all changes since main")
        console.print()
        
    except subprocess.CalledProcessError:
        console.print("\n[red]❌ Not a git repository[/red]\n")
        sys.exit(1)
    except FileNotFoundError:
        console.print("\n[red]❌ Git is not installed[/red]\n")
        sys.exit(1)


@app.command(name="github-status")
def github_status():
    """
    Check GitHub login status
    Example:
        alfred github-status
    """
    config = Config()
    github_auth = GitHubAuth(config.config_dir)

    console.print("\n[bold cyan]GitHub Status[/bold cyan]\n")

    if not github_auth.is_logged_in():
        console.print("[yellow]Not logged in[/yellow]")
        console.print("\n[dim]Run:[/dim] [cyan]alfred github-login[/cyan]\n")
        return

    user_info = github_auth.get_user_info()
    token_info = github_auth.get_token_info()

    if user_info:
        console.print(f"[green]✅ Logged in[/green]")
        console.print(f"\n[bold]User:[/bold] {user_info.get('login')}")
        console.print(f"[bold]Name:[/bold] {user_info.get('name', 'N/A')}")

    if token_info:
        hours_left = token_info.get('hours_until_expiry')
        console.print(f"\n[bold]Token expires in:[/bold] {hours_left} hours")

    console.print()

@app.command(name="github-logout")
def github_logout():
    """
    Logout from GitHub
    Example:
        alfred github-logout
    """
    config = Config()
    github_auth = GitHubAuth(config.config_dir)

    if not github_auth.is_logged_in():
        console.print("\n[yellow]Not logged in[/yellow]\n")
        return

    user_info = github_auth.get_user_info()
    username = user_info.get('login') if user_info else 'Unknown'

    console.print(f"\n[yellow]Logged in as:[/yellow] [cyan]{username}[/cyan]")

    confirm = Confirm.ask("Are you sure you want to logout?", default=False)

    if confirm:
        github_auth.logout()
        console.print("\n[green]✅ Logged out successfully[/green]\n")
    else:
        console.print("\n[yellow]Logout cancelled[/yellow]\n")

@app.command()
def review_pr(
    pr_url_or_number: str = typer.Argument(..., help="PR URL or number"),
    comment: bool = typer.Option(False, "--comment", "-c", help="Post review as comment"),
    focus: str = typer.Option("general", "--focus", "-f", help="Review focus"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", envvar="ANTHROPIC_API_KEY"),
    show_cost: bool = typer.Option(True, "--show-cost/--no-cost"),
    verbose: bool = typer.Option(False, "--verbose", "-v")
    ):
    
    """
    Review a GitHub Pull Request with AI
    Examples:
        alfred review-pr https://github.com/user/repo/pull/123
        alfred review-pr 123 --comment
    """

    if verbose:
        print_banner()

    # Check API key
    config = Config()
    anthropic_key = config.get_api_key(api_key)

    if not anthropic_key:
        console.print("[red]❌ Anthropic API key required. Run 'alfred setup'[/red]")
        sys.exit(1)

    # Check GitHub auth
    github_auth = GitHubAuth(config.config_dir)

    if not github_auth.is_logged_in():
        console.print("\n[red]❌ Not logged in to GitHub[/red]")
        console.print("\n[cyan]Please login first:[/cyan]")
        console.print("  alfred github-login\n")
        sys.exit(1)

    try:
        gh = GitHubIntegration(github_auth=github_auth)
        
        # Get user
        user_info = github_auth.get_user_info()
        username = user_info.get('login') if user_info else 'Unknown'
        console.print(f"\n[dim]Using GitHub account:[/dim] [cyan]{username}[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Fetching PR...", total=None)
            
            if pr_url_or_number.startswith('http'):
                owner, repo, pr_number = gh.parse_pr_url(pr_url_or_number)
            elif pr_url_or_number.isdigit():
                pr_number = int(pr_url_or_number)
                # Infer repo from git
                try:
                    result = subprocess.run(
                        ['git', 'remote', 'get-url', 'origin'],
                        capture_output=True, text=True, check=True
                    )
                    match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', result.stdout.strip())
                    if match:
                        owner, repo = match.groups()
                    else:
                        raise ValueError("Could not parse repository")
                except:
                    console.print("[red]❌ Could not determine repository. Use full PR URL.[/red]")
                    sys.exit(1)
            else:
                console.print("[red]❌ Invalid PR URL or number[/red]")
                sys.exit(1)
            
            pr = gh.get_pr(owner, repo, pr_number)
            pr_info = gh.get_pr_info(pr)
            diff = gh.get_pr_diff(pr)
        
        # Show PR info
        console.print(f"\n📄 PR #{pr_info['number']}: [cyan]{pr_info['title']}[/cyan]")
        console.print(f"📊 Changes: [green]+{pr_info['additions']}[/green] [red]-{pr_info['deletions']}[/red]\n")
        
        # Review
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("🤖 Reviewing...", total=None)
            agent = CodeReviewAgent(api_key=anthropic_key)
            review_text, cost_info = agent.review_pr_diff(pr_info, diff, focus, track_cost=show_cost)
        
        # Display
        console.print("\n" + "="*70 + "\n")
        md = Markdown(review_text)
        console.print(Panel(md, title="📋 PR Review", border_style="green"))
        
        if show_cost and cost_info:
            console.print(f"\n💰 Cost: [yellow]${cost_info['cost']:.4f}[/yellow]")
        
        # Post comment
        if comment:
            console.print("\n📝 Posting...\n")
            formatted = gh.format_review_for_pr(review_text, pr_info)
            try:
                gh.post_pr_comment(pr, formatted)
                console.print(f"[green]✅ Posted to PR #{pr_number}![/green]\n")
            except Exception as e:
                console.print(f"[red]❌ Failed: {str(e)}[/red]\n")
        
        console.print("\n[green]✅ Done![/green]\n")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        if verbose:
            import traceback
            console.print("\n[dim]" + traceback.format_exc() + "[/dim]")
        sys.exit(1)

if __name__ == "__main__":
    app()