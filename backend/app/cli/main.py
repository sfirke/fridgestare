import subprocess

import typer

from sqlalchemy.exc import OperationalError

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.services.users import create_user

app = typer.Typer(help="Fridgestare management commands.")
system_app = typer.Typer(help="System commands.")
users_app = typer.Typer(help="User management commands.")
app.add_typer(system_app, name="system")
app.add_typer(users_app, name="users")


def bootstrap_alembic() -> None:
    subprocess.run(["alembic", "upgrade", "head"], check=True)


@system_app.command("health")
def health() -> None:
    """Confirm the CLI is wired."""
    typer.echo("fridgestare cli ready")


@system_app.command("init-db")
def init_db() -> None:
    """Create database tables for local development."""
    Base.metadata.create_all(bind=engine)
    typer.echo("database initialized")


@system_app.command("bootstrap-db")
def bootstrap_db() -> None:
    """Bring a database under Alembic management and apply all migrations."""
    bootstrap_alembic()
    typer.echo("database migrations applied")


@users_app.command("create")
def create_user_command(
    email: str = typer.Option(...),
    password: str = typer.Option(...),
    admin: bool = typer.Option(False, "--admin"),
    timezone: str = typer.Option("UTC"),
    week_starts_on: int = typer.Option(0, min=0, max=6),
) -> None:
    """Create a user for bootstrap or invite-only operation."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        user = create_user(
            session,
            email=email,
            password=password,
            is_admin=admin,
            timezone=timezone,
            week_starts_on=week_starts_on,
        )
    except OperationalError as exc:
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # pragma: no cover - CLI fallback
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc
    finally:
        session.close()
    typer.echo(f"created user {user.email}")


if __name__ == "__main__":
    app()
