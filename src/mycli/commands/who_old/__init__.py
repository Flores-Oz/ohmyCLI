# src/mycli/commands/who_old/__init__.py
# Reexportar la API pública del módulo who_old.who_old
from .who_old import register_parser, run

__all__ = ["register_parser", "run"]
