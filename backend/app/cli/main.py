import subprocess

import typer
from sqlalchemy.exc import OperationalError

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.services.users import create_user, list_users, set_user_password

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
        typer.echo(
            "Could not reach the database. Check DATABASE_URL and that the server is up.",
            err=True,
        )
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # pragma: no cover - CLI fallback
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    finally:
        session.close()
    typer.echo(f"created user {user.email}")


@users_app.command("set-password")
def set_password_command(
    email: str = typer.Option(...),
    password: str = typer.Option(..., prompt=True, hide_input=True, confirmation_prompt=True),
) -> None:
    """Rotate a user's password.

    The bootstrap password is typed on a command line and lands in shell history, so
    there has to be a way to change it that is not a hand-written UPDATE.
    """
    session = SessionLocal()
    try:
        user = set_user_password(session, email=email, password=password)
    except OperationalError as exc:
        typer.echo(
            "Could not reach the database. Check DATABASE_URL and that the server is up.",
            err=True,
        )
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # pragma: no cover - CLI fallback
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    finally:
        session.close()
    typer.echo(f"updated password for {user.email}")


@users_app.command("list")
def list_users_command() -> None:
    """List accounts, so you can confirm what a deployment actually has."""
    session = SessionLocal()
    try:
        users = list_users(session)
    except OperationalError as exc:
        typer.echo(
            "Could not reach the database. Check DATABASE_URL and that the server is up.",
            err=True,
        )
        raise typer.Exit(code=1) from exc
    finally:
        session.close()
    if not users:
        typer.echo("no users yet")
        return
    for user in users:
        flags = []
        if user.is_admin:
            flags.append("admin")
        if not user.is_active:
            flags.append("inactive")
        suffix = f" [{', '.join(flags)}]" if flags else ""
        typer.echo(f"{user.id}\t{user.email}\t{user.timezone}{suffix}")


if __name__ == "__main__":
    app()
