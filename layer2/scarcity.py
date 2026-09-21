"""UK scarcity compiler (Layer 2 interface).

Delegates to compiler/scarcity.py — single implementation.

STALE: This module re-exports from compiler/scarcity.py but is never imported
by any other file. The canonical implementation is compiler/scarcity.py.
Kept as a Layer 2 facade for when the layer2 package is actively used.
"""
from compiler.scarcity import (
    compute_severity,
    compile_grid_constraint,
    compile_trade_constraint,
    compile_scarsity_view as compile_scarcity_view,
)

__all__ = [
    "compute_severity",
    "compile_grid_constraint",
    "compile_trade_constraint",
    "compile_scarcity_view",
]
