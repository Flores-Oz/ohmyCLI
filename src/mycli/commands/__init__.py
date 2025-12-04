# src/mycli/commands/__init__.py
"""
Paquete de comandos. Importamos los módulos concretos para que el
paquete exponga `who_old`, `who_new` y `notes` cuando se haga:
from mycli.commands import who_old, who_new, notes
"""
from . import who_old, who_new, notes

__all__ = ["who_old", "who_new", "notes"]
