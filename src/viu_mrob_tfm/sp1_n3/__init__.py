"""SP1.N3: the frozen N2 problem solved without a coordinator.

N3 keeps the N2 integer programme exactly

    min  sum_ik d_ik y_ik   s.t.  sum_k y_ik <= 1,  sum_i c_i y_ik >= m_k

and removes only the optimizer and the global robot registry. Loads stay a
common announced catalogue; everything about another robot must arrive as a
counted message over an edge of the communication graph.

The package is new rather than an adaptation of ``sp1_geo``: that module's
allocators compute a global argmax and bill simulated rounds, optimize a
saturating coverage utility instead of pure distance, and cannot express a
disconnected graph. Those results remain on disk as a historical pilot.
"""

from __future__ import annotations

# Stamped into every RAW row so a result can always be traced to the exact
# protocol that produced it.
PROTOCOL_VERSION = "sp1-n3-1.1"

from . import capacity_cbba, certificate, contract, graph, messages, weighted_grape, worlds
from .runner import METHOD_LABELS, METHODS, RunRecord, run_method

__all__ = [
    "PROTOCOL_VERSION",
    "METHODS",
    "METHOD_LABELS",
    "RunRecord",
    "capacity_cbba",
    "certificate",
    "contract",
    "graph",
    "messages",
    "run_method",
    "weighted_grape",
    "worlds",
]
