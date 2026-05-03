import typer

app = typer.Typer(help="Fridgestare management commands.")
system_app = typer.Typer(help="System commands.")
app.add_typer(system_app, name="system")


@system_app.command("health")
def health() -> None:
    """Confirm the CLI is wired."""
    typer.echo("fridgestare cli ready")


if __name__ == "__main__":
    app()
