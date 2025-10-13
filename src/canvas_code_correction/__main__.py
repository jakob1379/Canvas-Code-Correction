"""CLI entrypoint for `python -m canvas_code_correction`."""

from .cli import app


def main() -> None:
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
