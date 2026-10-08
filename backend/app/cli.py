"""Admin CLI.

python -m app.cli create-admin --email me@example.com --username me   (password is prompted)
python -m app.cli create-invite [--days 7]                             (prints the code once)
"""

import argparse
import asyncio
import getpass
import sys
from collections.abc import Coroutine
from datetime import timedelta
from typing import Any

from pydantic import ValidationError

from app.core.errors import AppError
from app.db.enums import UserRole
from app.db.session import SessionLocal, engine
from app.services import auth as auth_service
from app.services.auth import NewUser


async def create_admin(data: NewUser) -> None:
    async with SessionLocal() as session:
        user = await auth_service.create_user(session, data, role=UserRole.ADMIN)
        await session.commit()
    print(f"Admin created: {user.username} <{user.email}> id={user.id}")


async def create_invite(days: int) -> str:
    async with SessionLocal() as session:
        _, code = await auth_service.create_invite(session, ttl=timedelta(days=days))
        await session.commit()
    return code


def _prompt_new_admin(email: str, username: str) -> NewUser:
    password = getpass.getpass("Password: ")
    if getpass.getpass("Repeat password: ") != password:
        sys.exit("Passwords do not match")
    try:
        return NewUser(email=email, username=username, password=password)
    except ValidationError as exc:
        errors = "; ".join(f"{e['loc'][0]}: {e['msg']}" for e in exc.errors())
        sys.exit(f"Invalid input: {errors}")


async def _run(command: Coroutine[Any, Any, None]) -> None:
    try:
        await command
    finally:
        await engine.dispose()


async def _print_invite(days: int) -> None:
    code = await create_invite(days)
    print(f"Invite code (shown once, valid {days} days): {code}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    admin = sub.add_parser("create-admin", help="create an admin user (password is prompted)")
    admin.add_argument("--email", required=True)
    admin.add_argument("--username", required=True)
    invite = sub.add_parser("create-invite", help="create a registration invite code")
    invite.add_argument("--days", type=int, default=auth_service.INVITE_TTL.days)
    args = parser.parse_args(argv)

    if args.command == "create-admin":
        command = create_admin(_prompt_new_admin(args.email, args.username))
    else:
        if args.days < 1:
            parser.error("--days must be >= 1")
        command = _print_invite(args.days)
    try:
        asyncio.run(_run(command))
    except AppError as exc:
        sys.exit(f"Error: {exc.code}")


if __name__ == "__main__":
    main()
