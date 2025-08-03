"""
Command-line interface for AI Prompt Toolkit.
"""

import asyncio
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ai_prompt_toolkit.core.config import settings
from ai_prompt_toolkit.core.database import init_db
from ai_prompt_toolkit.templates.builtin_templates import BUILTIN_TEMPLATES
from ai_prompt_toolkit.services.template_service import template_service
from ai_prompt_toolkit.models.prompt_template import PromptTemplateCreate

app = typer.Typer(help="AI Prompt Toolkit CLI")
console = Console()


@app.command()
def init():
    """Initialize the AI Prompt Toolkit database and load built-in templates."""
    console.print("[bold blue]Initializing AI Prompt Toolkit...[/bold blue]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Initialize database
        task1 = progress.add_task("Initializing database...", total=None)
        asyncio.run(init_db())
        progress.update(task1, completed=True)
        
        # Load built-in templates
        task2 = progress.add_task("Loading built-in templates...", total=None)
        asyncio.run(_load_builtin_templates())
        progress.update(task2, completed=True)
    
    console.print("[bold green]✓ AI Prompt Toolkit initialized successfully![/bold green]")
    console.print(f"[dim]Database: {settings.database.url}[/dim]")
    console.print(f"[dim]Default LLM Provider: {settings.default_llm_provider.value}[/dim]")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    reload: bool = typer.Option(False, help="Enable auto-reload")
):
    """Start the AI Prompt Toolkit server."""
    import uvicorn
    
    console.print(f"[bold blue]Starting AI Prompt Toolkit server...[/bold blue]")
    console.print(f"[dim]Host: {host}[/dim]")
    console.print(f"[dim]Port: {port}[/dim]")
    console.print(f"[dim]Reload: {reload}[/dim]")
    
    uvicorn.run(
        "ai_prompt_toolkit.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=settings.log_level.lower()
    )


@app.command()
def status():
    """Show system status and configuration."""
    
    # Create status table
    table = Table(title="AI Prompt Toolkit Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="dim")
    
    # Application info
    table.add_row("Application", "✓ Running", f"Version {settings.version}")
    table.add_row("Debug Mode", "✓ Enabled" if settings.debug else "✗ Disabled", "")
    table.add_row("Log Level", settings.log_level.value, "")
    
    # Database
    table.add_row("Database", "✓ Connected", settings.database.url)
    
    # LLM Providers
    enabled_providers = settings.get_enabled_providers()
    table.add_row("LLM Providers", f"✓ {len(enabled_providers)} enabled", ", ".join(p.value for p in enabled_providers))
    table.add_row("Default Provider", settings.default_llm_provider.value, "")
    
    # Security
    table.add_row("Injection Detection", "✓ Enabled" if settings.security.enable_prompt_injection_detection else "✗ Disabled", "")
    table.add_row("Optimization", "✓ Enabled" if settings.optimization.enabled else "✗ Disabled", "")
    
    console.print(table)


@app.command()
def test_prompt(
    prompt: str = typer.Argument(..., help="Prompt to test"),
    provider: Optional[str] = typer.Option(None, help="LLM provider to use")
):
    """Test a prompt with the specified provider."""
    console.print(f"[bold blue]Testing prompt...[/bold blue]")
    console.print(Panel(prompt, title="Input Prompt"))

    async def _test_prompt():
        from ai_prompt_toolkit.services.llm_factory import llm_factory
        from ai_prompt_toolkit.utils.prompt_analyzer import PromptAnalyzer
        from ai_prompt_toolkit.core.config import LLMProvider

        try:
            # Initialize LLM factory
            await llm_factory.initialize()

            # Get provider
            if provider:
                try:
                    llm_provider = LLMProvider(provider.upper())
                except ValueError:
                    console.print(f"[red]Error: Unknown provider '{provider}'. Available: {[p.value for p in LLMProvider]}[/red]")
                    return
            else:
                llm_provider = settings.default_llm_provider

            # Analyze prompt first
            analyzer = PromptAnalyzer()
            analysis = await analyzer.analyze_prompt(prompt)

            # Show analysis
            table = Table(title="Prompt Analysis")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")

            table.add_row("Token Count", str(analysis["token_count"]))
            table.add_row("Quality Score", f"{analysis['quality_score']:.2f}")
            table.add_row("Clarity Score", f"{analysis['clarity_score']:.2f}")
            table.add_row("Safety Score", f"{analysis['safety_score']:.2f}")

            console.print(table)

            # Test with LLM
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                task = progress.add_task(f"Testing with {llm_provider.value}...", total=None)

                llm = llm_factory.get_llm(llm_provider)
                result = await llm.agenerate([prompt])
                response = result.generations[0][0].text

                progress.update(task, completed=True)

            console.print(Panel(response, title=f"Response from {llm_provider.value}"))

        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")

    asyncio.run(_test_prompt())


@app.command()
def optimize_prompt(
    prompt: str = typer.Argument(..., help="Prompt to optimize"),
    iterations: int = typer.Option(5, help="Maximum optimization iterations"),
    strategy: str = typer.Option("genetic", help="Optimization strategy: genetic or hill_climbing")
):
    """Optimize a prompt for cost and performance."""
    console.print(f"[bold blue]Optimizing prompt...[/bold blue]")
    console.print(Panel(prompt, title="Original Prompt"))

    async def _optimize_prompt():
        from ai_prompt_toolkit.services.optimization_service import PromptOptimizer
        from ai_prompt_toolkit.models.optimization import OptimizationRequest
        from ai_prompt_toolkit.core.database import SessionLocal

        try:
            # Create optimization request
            request = OptimizationRequest(
                prompt=prompt,
                max_iterations=iterations,
                use_genetic_algorithm=(strategy.lower() == "genetic"),
                target_cost_reduction=0.3,
                target_quality_threshold=0.8
            )

            # Initialize optimizer
            optimizer = PromptOptimizer()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Running {strategy} optimization...", total=None)

                # Run optimization
                db = SessionLocal()
                try:
                    job_id = await optimizer.optimize_prompt(db, request)

                    # Wait for completion (simplified for CLI)
                    import time
                    while True:
                        status = await optimizer.get_optimization_status(db, job_id)
                        if status.status in ["completed", "failed"]:
                            break
                        time.sleep(1)

                    progress.update(task, completed=True)

                    if status.status == "completed":
                        # Show results
                        console.print(Panel(status.optimized_prompt, title="Optimized Prompt", style="green"))

                        # Show improvements
                        results_table = Table(title="Optimization Results")
                        results_table.add_column("Metric", style="cyan")
                        results_table.add_column("Original", style="red")
                        results_table.add_column("Optimized", style="green")
                        results_table.add_column("Improvement", style="yellow")

                        if status.results:
                            cost_reduction = status.results.get("cost_reduction", 0) * 100
                            performance_change = status.results.get("performance_change", 0) * 100

                            results_table.add_row(
                                "Cost Reduction",
                                f"${status.cost_original:.4f}",
                                f"${status.cost_optimized:.4f}",
                                f"{cost_reduction:.1f}%"
                            )
                            results_table.add_row(
                                "Performance",
                                f"{status.performance_original:.2f}",
                                f"{status.performance_optimized:.2f}",
                                f"{performance_change:+.1f}%"
                            )

                        console.print(results_table)
                    else:
                        console.print(f"[red]Optimization failed: {status.error_message}[/red]")

                finally:
                    db.close()

        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")

    asyncio.run(_optimize_prompt())


@app.command()
def list_templates(
    category: Optional[str] = typer.Option(None, help="Filter by category"),
    limit: int = typer.Option(10, help="Number of templates to show")
):
    """List available prompt templates."""
    console.print(f"[bold blue]Available Templates[/bold blue]")
    
    # Create templates table
    table = Table()
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Description", style="dim")
    
    # Show built-in templates as example
    for template in BUILTIN_TEMPLATES[:limit]:
        if category and template["category"].value != category:
            continue
        
        table.add_row(
            template["name"],
            template["category"].value,
            template["description"][:50] + "..." if len(template["description"]) > 50 else template["description"]
        )
    
    console.print(table)


@app.command()
def security_scan(prompt: str = typer.Argument(..., help="Prompt to scan for security issues")):
    """Scan a prompt for potential security issues."""
    console.print(f"[bold blue]Security Scan[/bold blue]")
    console.print(Panel(prompt, title="Prompt to Scan"))

    async def _security_scan():
        from ai_prompt_toolkit.security.injection_detector import injection_detector
        from ai_prompt_toolkit.security.enhanced_guardrails import enhanced_guardrail_engine

        try:
            # Run injection detection
            injection_result = injection_detector.detect_injection(prompt)

            # Run enhanced guardrails
            guardrail_result = await enhanced_guardrail_engine.validate_prompt(prompt)

            # Show injection detection results
            injection_table = Table(title="Injection Detection Results")
            injection_table.add_column("Metric", style="cyan")
            injection_table.add_column("Value", style="magenta")
            injection_table.add_column("Status", style="green")

            injection_table.add_row(
                "Injection Detected",
                "Yes" if injection_result["is_injection"] else "No",
                "🚨" if injection_result["is_injection"] else "✅"
            )
            injection_table.add_row(
                "Threat Level",
                injection_result["threat_level"],
                "🚨" if injection_result["threat_level"] in ["HIGH", "CRITICAL"] else "⚠️" if injection_result["threat_level"] == "MEDIUM" else "✅"
            )
            injection_table.add_row(
                "Confidence",
                f"{injection_result['confidence']:.2f}",
                "📊"
            )

            console.print(injection_table)

            # Show detections
            if injection_result["detections"]:
                console.print("\n🚨 Security Issues Found:")
                for detection in injection_result["detections"]:
                    console.print(f"  • {detection['type']}: {detection['description']}")
                    console.print(f"    Pattern: {detection['pattern']}")
                    console.print(f"    Severity: {detection['severity']}")

            # Show guardrail results
            guardrail_table = Table(title="Guardrail Validation Results")
            guardrail_table.add_column("Metric", style="cyan")
            guardrail_table.add_column("Value", style="magenta")
            guardrail_table.add_column("Status", style="green")

            guardrail_table.add_row(
                "Overall Safety",
                "Safe" if guardrail_result.is_safe else "Unsafe",
                "✅" if guardrail_result.is_safe else "🚨"
            )
            guardrail_table.add_row(
                "Total Violations",
                str(len(guardrail_result.violations)),
                "✅" if len(guardrail_result.violations) == 0 else "⚠️"
            )

            console.print(guardrail_table)

            # Show violations
            if guardrail_result.violations:
                console.print("\n⚠️ Guardrail Violations:")
                for violation in guardrail_result.violations:
                    severity_emoji = "🚨" if violation.get("severity") == "critical" else "⚠️" if violation.get("severity") == "error" else "ℹ️"
                    console.print(f"  {severity_emoji} {violation.get('rule_name', 'Unknown')}: {violation.get('description', 'No description')}")

            # Show recommendations
            if guardrail_result.recommendations:
                console.print("\n💡 Security Recommendations:")
                for rec in guardrail_result.recommendations:
                    console.print(f"  • {rec}")

            # Overall assessment
            if injection_result["is_injection"] or not guardrail_result.is_safe:
                console.print("\n[bold red]⚠️ SECURITY RISK DETECTED - Review and modify prompt before use[/bold red]")
            else:
                console.print("\n[bold green]✅ Prompt appears safe for use[/bold green]")

        except Exception as e:
            console.print(f"[red]Error during security scan: {str(e)}[/red]")

    asyncio.run(_security_scan())


async def _load_builtin_templates():
    """Load built-in templates into the database."""
    from ai_prompt_toolkit.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        for template_data in BUILTIN_TEMPLATES:
            template = PromptTemplateCreate(**template_data)
            try:
                await template_service.create_template(db, template)
            except Exception as e:
                # Template might already exist, skip
                pass
    finally:
        db.close()


if __name__ == "__main__":
    app()
