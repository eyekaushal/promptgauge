"""Composition root and Typer app: promptgauge eval | ablate | ui. Every object is built here and
injected through constructors.
"""

import typer

app = typer.Typer(
    help="Which lines of your system prompt actually do anything.",
    no_args_is_help=True,
)


@app.command()
def eval(config: str = "promptgauge.yaml") -> None:
    """Run every case against the prompt, score it, store it, print a table."""
    raise NotImplementedError


@app.command()
def ablate(config: str = "promptgauge.yaml", calls_per_month: int = 100_000) -> None:
    """Knock out blocks then lines, measure, paint the prompt, write the cut prompt."""
    raise NotImplementedError


@app.command()
def ui(port: int = 7331) -> None:
    """Serve the local dashboard and open the browser."""
    raise NotImplementedError
