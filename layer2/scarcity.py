"""UK scarcity compiler (Layer 2 interface).

Delegates to compiler/scarcity.py — single implementation.
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
