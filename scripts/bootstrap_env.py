"""Create local settings without overwriting an existing .env or printing secrets."""

import secrets
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    target = root / ".env"
    if target.exists() and target.stat().st_size:
        print("Existing .env kept unchanged.")
        return
    template = (root / ".env.example").read_text(encoding="utf-8")
    template = template.replace(
        "JWT_SECRET=\n", f"JWT_SECRET={secrets.token_urlsafe(48)}\n"
    )
    target.write_text(template, encoding="utf-8")
    print("Created .env with a private JWT secret.")


if __name__ == "__main__":
    main()
