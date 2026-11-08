"""Interactive Rich-based Live Terminal Dashboard for evolutionary mathematical discovery."""

import sys
from pathlib import Path

_src_dir = str(Path(__file__).resolve().parent.parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

import time
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text

from evolutionary_math.core.ast import ExprNode
from evolutionary_math.evolution.engine import EvolutionEngine, DiscoveryTelemetry
from evolutionary_math.evolution.island import Island
from evolutionary_math.storage.knowledge_base import KnowledgeBase
from evolutionary_math.utils.formatting import to_latex


class DiscoveryDashboard:
    """Live terminal UI visualizing the evolutionary search and LLM advisory dynamics."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.advisory_logs: List[str] = []

    def run_live(
        self,
        engine: EvolutionEngine,
        target_lhs: ExprNode,
        max_generations: int = 100,
        experiment_id: str = "live_exp",
    ):
        """Execute discovery run with a real-time updating terminal layout."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=4),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=6),
        )
        layout["body"].split_row(
            Layout(name="islands", ratio=3),
            Layout(name="advisory", ratio=2),
        )

        start_time = time.perf_counter()

        with Live(layout, console=self.console, refresh_per_second=4, screen=False) as live:
            def update_ui(telem: DiscoveryTelemetry):
                elapsed = time.perf_counter() - start_time

                # 1. Header
                header_text = Text()
                header_text.append("EVOLUTIONARY MATHEMATICAL DISCOVERY ENGINE\n", style="bold cyan")
                header_text.append(f"Target Problem Space: {target_lhs} | ", style="bold white")
                header_text.append(f"Gen: {telem.generation}/{max_generations} | ", style="yellow")
                header_text.append(f"Elapsed: {elapsed:.1f}s | ", style="green")
                header_text.append(f"Evals: {telem.total_individuals_evaluated:,}", style="magenta")
                layout["header"].update(Panel(header_text, border_style="cyan"))

                # 2. Islands Table
                island_table = Table(title="🏝️ Multi-Island Population Status", expand=True, border_style="blue")
                island_table.add_column("Island", justify="center", style="cyan", width=8)
                island_table.add_column("Regime", justify="center", style="magenta", width=14)
                island_table.add_column("Top Candidate", style="white")
                island_table.add_column("Validity", justify="right", style="green", width=10)

                for island in engine.islands:
                    if island.population:
                        top = max(island.population, key=lambda ind: ind.validity)
                        val_style = "bold green" if top.validity >= 0.9 else ("yellow" if top.validity > 0.4 else "red")
                        island_table.add_row(
                            f"#{island.island_id}",
                            island.regime.upper(),
                            str(top.candidate)[:40],
                            f"[{val_style}]{top.validity:.4f}[/]",
                        )
                layout["islands"].update(Panel(island_table, border_style="blue"))

                # 3. Advisory Intervention Feed
                if telem.advisory_intervention:
                    self.advisory_logs.append(f"[Gen {telem.generation}] {telem.advisory_intervention}")
                    if len(self.advisory_logs) > 6:
                        self.advisory_logs.pop(0)

                adv_text = Text()
                if self.advisory_logs:
                    for log in self.advisory_logs:
                        adv_text.append(f"⚡ {log}\n", style="bold yellow")
                else:
                    adv_text.append("Evolution proceeding deterministically.\nLLM adviser monitoring stagnation...\n", style="dim white")

                layout["advisory"].update(Panel(adv_text, title="🤖 Air-Gapped Advisory Stream", border_style="yellow"))

                # 4. Footer
                footer_text = Text()
                footer_text.append(f"Leading Global Expression: ", style="dim")
                footer_text.append(f"{telem.best_candidate_str}\n", style="bold green")
                footer_text.append(f"Pareto Front Size: {telem.pareto_front_size} | Verification Status: Tier 1 & Tier 2 Active", style="dim")
                layout["footer"].update(Panel(footer_text, border_style="green"))

            # Execute evolutionary search
            result = engine.run(
                target_lhs=target_lhs,
                max_generations=max_generations,
                experiment_id=experiment_id,
                callback=update_ui,
            )

        # Post-run discovery summary
        if result.success and result.discovered_theorem:
            th = result.discovered_theorem
            self.console.print("\n")
            disc_panel = Panel(
                f"[bold green]🏆 DISCOVERY CONFIRMED & FORMALLY VERIFIED![/bold green]\n\n"
                f"[bold white]Target:[/bold white]           {th.target_str}\n"
                f"[bold white]Discovered Form:[/bold white]  [cyan]{th.discovery_str}[/cyan]\n"
                f"[bold white]LaTeX:[/bold white]            [yellow]{to_latex(th.definition_ast) if th.definition_ast else th.discovery_str}[/yellow]\n"
                f"[bold white]Proof Method:[/bold white]     {th.proof_method} via Tier 2 Induction\n"
                f"[bold white]Generations:[/bold white]      {result.total_generations} in {result.total_time_sec:.3f} s\n"
                f"[bold white]Knowledge Base:[/bold white]   Saved in SQLite [ID: {th.id}]",
                title="Mathematical Discovery Established",
                border_style="green",
            )
            self.console.print(disc_panel)
        else:
            self.console.print(f"\n[yellow]Search terminated after {result.total_generations} generations.[/yellow]")

        return result

