#!/usr/bin/env python3
"""Semantic replay packet gate for B1/B7 cone_01 blocker stacks.

T-B1-004ad rejected cheap interleaving commutation for the current
source-aligned carrier candidates. This gate turns those blocked CNOT stacks
into exact, bounded local replay targets. It does not synthesize a shorter
replacement. It creates the auditable 2-qubit semantic packets that the next
rewrite/synthesis step must consume.
"""

from __future__ import annotations

import argparse
import cmath
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from b1_b7_cone01_carrier_absorption_inventory_gate import (
    INVENTORY_QASM_PATH,
    PROXY_T_PER_OCCURRENCE,
    REQUIRED_OCCURRENCE_REMOVALS,
    display_path,
    eval_angle_expr,
    load_json,
    split_args,
    write_json,
    write_text,
)


ROOT = Path(__file__).resolve().parents[1]
INTERLEAVING_GATE_PATH = (
    ROOT / "results" / "B1_B7_cone01_carrier_interleaving_commutation_gate_v0.json"
)
PARITY_GATE_PATH = ROOT / "results" / "B1_B7_cone01_carrier_blocker_parity_gate_v0.json"
JSON_OUT = ROOT / "results" / "B1_B7_cone01_semantic_replay_packet_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_semantic_replay_packet_gate.md"

METHOD = "b1_b7_cone01_semantic_replay_packet_gate_v0"
STATUS = "cone01_semantic_replay_packet_constructed_not_solved"
MODEL_STATUS = "blocked_carrier_cnot_stacks_are_bounded_two_qubit_semantic_replay_targets"
CX_RE = re.compile(r"^cx q\[(\d+)\],q\[(\d+)\];$")
ONE_Q_RE = re.compile(r"^(u3|u|rz|rx|ry|u1|u2)\((.*)\) q\[(\d+)\];$")
QUBIT_RE = re.compile(r"q\[(\d+)\]")
ROUND_DIGITS = 12
ZERO_TOLERANCE = 1e-10


Matrix = list[list[complex]]


def parse_qasm_lines(path: Path) -> dict[int, str]:
    return {idx: line.strip() for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)}


def qubits_in_line(text: str) -> list[int]:
    return [int(value) for value in QUBIT_RE.findall(text)]


def gate_name(text: str) -> str:
    if match := CX_RE.match(text):
        return "cx"
    if match := ONE_Q_RE.match(text):
        return match.group(1)
    return "other"


def identity(size: int) -> Matrix:
    return [[1.0 + 0.0j if row == col else 0.0 + 0.0j for col in range(size)] for row in range(size)]


def matmul(left: Matrix, right: Matrix) -> Matrix:
    size = len(left)
    return [
        [
            sum(left[row][inner] * right[inner][col] for inner in range(size))
            for col in range(size)
        ]
        for row in range(size)
    ]


def one_qubit_matrix(gate: str, raw_args: str) -> Matrix:
    args = split_args(raw_args)
    if gate == "rz" or gate == "u1":
        theta = eval_angle_expr(args[0])
        return [[cmath.exp(-0.5j * theta), 0.0j], [0.0j, cmath.exp(0.5j * theta)]]
    if gate == "rx":
        theta = eval_angle_expr(args[0])
        c = math.cos(theta / 2.0)
        s = math.sin(theta / 2.0)
        return [[c, -1j * s], [-1j * s, c]]
    if gate == "ry":
        theta = eval_angle_expr(args[0])
        c = math.cos(theta / 2.0)
        s = math.sin(theta / 2.0)
        return [[c, -s], [s, c]]
    if gate == "u2":
        phi = eval_angle_expr(args[0])
        lam = eval_angle_expr(args[1])
        return u3_matrix(math.pi / 2.0, phi, lam)
    if gate == "u3" or gate == "u":
        theta = eval_angle_expr(args[0])
        phi = eval_angle_expr(args[1])
        lam = eval_angle_expr(args[2])
        return u3_matrix(theta, phi, lam)
    raise ValueError(f"unsupported one-qubit gate: {gate}")


def u3_matrix(theta: float, phi: float, lam: float) -> Matrix:
    c = math.cos(theta / 2.0)
    s = math.sin(theta / 2.0)
    return [
        [c, -cmath.exp(1j * lam) * s],
        [cmath.exp(1j * phi) * s, cmath.exp(1j * (phi + lam)) * c],
    ]


def expand_one_qubit(local_qubit: int, support_count: int, gate: Matrix) -> Matrix:
    size = 1 << support_count
    expanded = [[0.0j for _ in range(size)] for _ in range(size)]
    mask = 1 << (support_count - 1 - local_qubit)
    for col in range(size):
        bit = 1 if col & mask else 0
        base = col & ~mask
        for out_bit in (0, 1):
            row = base | (mask if out_bit else 0)
            expanded[row][col] = gate[out_bit][bit]
    return expanded


def expand_cx(local_control: int, local_target: int, support_count: int) -> Matrix:
    size = 1 << support_count
    expanded = [[0.0j for _ in range(size)] for _ in range(size)]
    control_mask = 1 << (support_count - 1 - local_control)
    target_mask = 1 << (support_count - 1 - local_target)
    for col in range(size):
        row = col ^ target_mask if col & control_mask else col
        expanded[row][col] = 1.0 + 0.0j
    return expanded


def rounded_complex(value: complex) -> list[float]:
    real = 0.0 if abs(value.real) < ZERO_TOLERANCE else round(value.real, ROUND_DIGITS)
    imag = 0.0 if abs(value.imag) < ZERO_TOLERANCE else round(value.imag, ROUND_DIGITS)
    return [real, imag]


def global_phase_normalized(matrix: Matrix) -> Matrix:
    phase = 1.0 + 0.0j
    for row in matrix:
        for value in row:
            if abs(value) > ZERO_TOLERANCE:
                phase = value / abs(value)
                return [[cell / phase for cell in source_row] for source_row in matrix]
    return matrix


def matrix_fingerprint(matrix: Matrix) -> dict[str, Any]:
    normalized = global_phase_normalized(matrix)
    rounded = [[rounded_complex(value) for value in row] for row in normalized]
    encoded = json.dumps(rounded, separators=(",", ":"), sort_keys=True)
    nonzero_count = sum(
        1
        for row in normalized
        for value in row
        if abs(value) > ZERO_TOLERANCE
    )
    off_diagonal_nonzero_count = sum(
        1
        for row_index, row in enumerate(normalized)
        for col_index, value in enumerate(row)
        if row_index != col_index and abs(value) > ZERO_TOLERANCE
    )
    return {
        "dimension": len(matrix),
        "nonzero_entry_count": nonzero_count,
        "off_diagonal_nonzero_entry_count": off_diagonal_nonzero_count,
        "global_phase_normalized_sha256": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
        "global_phase_normalized_matrix_rounded": rounded,
    }


def normalized_ops(window_lines: list[dict[str, Any]], local_index: dict[int, int]) -> list[dict[str, Any]]:
    ops = []
    for item in window_lines:
        text = item["text"]
        if match := CX_RE.match(text):
            control = int(match.group(1))
            target = int(match.group(2))
            ops.append(
                {
                    "line_number": item["line_number"],
                    "gate": "cx",
                    "physical_control": control,
                    "physical_target": target,
                    "local_control": local_index[control],
                    "local_target": local_index[target],
                    "text": text,
                }
            )
            continue
        if match := ONE_Q_RE.match(text):
            gate, raw_args, qubit_text = match.groups()
            qubit = int(qubit_text)
            ops.append(
                {
                    "line_number": item["line_number"],
                    "gate": gate,
                    "physical_qubit": qubit,
                    "local_qubit": local_index[qubit],
                    "raw_args": split_args(raw_args),
                    "text": text,
                }
            )
            continue
        ops.append({"line_number": item["line_number"], "gate": "other", "text": text})
    return ops


def unitary_for_ops(ops: list[dict[str, Any]], support_count: int) -> Matrix:
    unitary = identity(1 << support_count)
    for op in ops:
        if op["gate"] == "cx":
            gate = expand_cx(op["local_control"], op["local_target"], support_count)
        elif "local_qubit" in op:
            gate = expand_one_qubit(
                op["local_qubit"],
                support_count,
                one_qubit_matrix(op["gate"], ",".join(op["raw_args"])),
            )
        else:
            raise ValueError(f"unsupported op in semantic packet: {op}")
        unitary = matmul(gate, unitary)
    return unitary


def parity_candidates_by_line(parity: dict[str, Any]) -> dict[int, dict[str, Any]]:
    rows = {}
    for row in parity.get("carrier_blocker_parity_rows", []):
        for candidate in row.get("parity_candidates", []):
            enriched = dict(candidate)
            enriched["pattern_id"] = row["pattern_id"]
            enriched["occurrence_count"] = int(row["occurrence_count"])
            enriched["target_qubits"] = row["target_qubits"]
            rows[int(candidate["candidate_line_number"])] = enriched
    return rows


def build_packet(candidate: dict[str, Any], parity_candidate: dict[str, Any], qasm_lines: dict[int, str]) -> dict[str, Any]:
    start = min(int(pair["left_blocker_line"]) for pair in parity_candidate["repeated_same_edge_pairs"])
    end = max(int(pair["right_blocker_line"]) for pair in parity_candidate["repeated_same_edge_pairs"])
    window_lines = [
        {"line_number": line_number, "text": qasm_lines[line_number]}
        for line_number in range(start, end + 1)
    ]
    support_qubits = sorted({qubit for item in window_lines for qubit in qubits_in_line(item["text"])})
    local_index = {qubit: idx for idx, qubit in enumerate(support_qubits)}
    ops = normalized_ops(window_lines, local_index)
    gate_counts: dict[str, int] = {}
    for op in ops:
        gate_counts[op["gate"]] = gate_counts.get(op["gate"], 0) + 1
    unitary = unitary_for_ops(ops, len(support_qubits))
    fingerprint = matrix_fingerprint(unitary)
    cx_edges = [
        f"{min(op['physical_control'], op['physical_target'])}-{max(op['physical_control'], op['physical_target'])}"
        for op in ops
        if op["gate"] == "cx"
    ]
    return {
        "pattern_id": parity_candidate["pattern_id"],
        "occurrence_count": parity_candidate["occurrence_count"],
        "candidate_line_number": int(candidate["candidate_line_number"]),
        "candidate_qubit": int(candidate["candidate_qubit"]),
        "source_distance": int(candidate["source_distance"]),
        "window_start_line": start,
        "window_end_line": end,
        "window_line_count": len(window_lines),
        "support_qubits": support_qubits,
        "support_qubit_count": len(support_qubits),
        "local_qubit_order": support_qubits,
        "normalized_ops": ops,
        "gate_counts": gate_counts,
        "cx_count": gate_counts.get("cx", 0),
        "single_qubit_gate_count": len(ops) - gate_counts.get("cx", 0),
        "unique_cx_edge_signatures": sorted(set(cx_edges)),
        "semantic_matrix": fingerprint,
        "semantic_replay_target_constructed": True,
        "semantic_replay_certificate_claimed": False,
        "shorter_rewrite_claimed": False,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "next_obligation": (
            "Use this 2-qubit unitary target to search for an equivalent replacement "
            "with fewer accepted B7-costed operations, then replay it against the full circuit."
        ),
    }


def build_payload() -> dict[str, Any]:
    source = load_json(INTERLEAVING_GATE_PATH)
    parity = load_json(PARITY_GATE_PATH)
    qasm_lines = parse_qasm_lines(INVENTORY_QASM_PATH)
    parity_by_line = parity_candidates_by_line(parity)
    packets = []
    for row in source.get("carrier_interleaving_commutation_rows", []):
        for candidate in row.get("commutation_candidates", []):
            candidate_line = int(candidate["candidate_line_number"])
            packets.append(build_packet(candidate, parity_by_line[candidate_line], qasm_lines))

    accepted_removed = sum(packet["accepted_occurrence_removal"] for packet in packets)
    support_counts = [packet["support_qubit_count"] for packet in packets]
    summary = {
        "source_method": source.get("method"),
        "source_status": source.get("status"),
        "inventory_qasm": display_path(INVENTORY_QASM_PATH),
        "semantic_replay_packet_count": len(packets),
        "two_qubit_packet_count": sum(1 for packet in packets if packet["support_qubit_count"] == 2),
        "min_support_qubit_count": min(support_counts) if support_counts else 0,
        "max_support_qubit_count": max(support_counts) if support_counts else 0,
        "total_window_gate_count": sum(packet["window_line_count"] for packet in packets),
        "total_cx_count": sum(packet["cx_count"] for packet in packets),
        "total_single_qubit_gate_count": sum(packet["single_qubit_gate_count"] for packet in packets),
        "unique_semantic_fingerprint_count": len(
            {packet["semantic_matrix"]["global_phase_normalized_sha256"] for packet in packets}
        ),
        "all_packets_have_single_cx_edge_family": all(
            len(packet["unique_cx_edge_signatures"]) == 1 for packet in packets
        ),
        "all_packets_have_exact_matrix_target": all(
            packet["semantic_matrix"]["dimension"] == 4 for packet in packets
        ),
        "semantic_replay_targets_constructed": True,
        "semantic_replay_certificate_claimed": False,
        "shorter_rewrite_claimed": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "accepted_occurrence_removal": accepted_removed,
        "accepted_proxy_t_reduction": accepted_removed * PROXY_T_PER_OCCURRENCE,
        "missing_occurrences_after_gate": max(0, REQUIRED_OCCURRENCE_REMOVALS - accepted_removed),
        "missing_proxy_t_after_gate": max(0, REQUIRED_OCCURRENCE_REMOVALS - accepted_removed)
        * PROXY_T_PER_OCCURRENCE,
        "validation_error_count": None,
    }
    payload = {
        "benchmark_id": "B1",
        "problem_id": 25,
        "linked_b7_problem_id": 21,
        "title": "B1/B7 cone_01 semantic replay packet gate",
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "method": METHOD,
        "source_result": display_path(INTERLEAVING_GATE_PATH),
        "source_method": source.get("method"),
        "workload": source.get("workload", "qasmbench_medium_exact/gcm_h6.qasm"),
        "summary": summary,
        "semantic_replay_packets": packets,
        "claim_boundary": {
            "semantic_replay_targets_constructed": True,
            "semantic_replay_certificate_claimed": False,
            "shorter_rewrite_claimed": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "supported_claim": (
                "The currently blocked carrier candidates are now represented as exact, "
                "bounded 2-qubit semantic replay targets with stable matrix fingerprints."
            ),
            "unsupported_claims": [
                "No shorter equivalent circuit has been synthesized.",
                "No full-circuit replay certificate has been produced.",
                "No occurrence is removed from the B7 ledger.",
            ],
        },
    }
    errors = validate(payload)
    payload["summary"]["validation_error_count"] = len(errors)
    payload["validation_errors"] = errors
    return payload


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = payload["summary"]
    expected = {
        "semantic_replay_packet_count": 3,
        "two_qubit_packet_count": 3,
        "min_support_qubit_count": 2,
        "max_support_qubit_count": 2,
        "total_window_gate_count": 32,
        "total_cx_count": 14,
        "total_single_qubit_gate_count": 18,
        "unique_semantic_fingerprint_count": 3,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": 30,
        "missing_proxy_t_after_gate": 600,
    }
    if payload.get("method") != METHOD:
        errors.append("method_mismatch")
    if payload.get("status") != STATUS:
        errors.append("status_mismatch")
    if payload.get("source_method") != "b1_b7_cone01_carrier_interleaving_commutation_gate_v0":
        errors.append("source_method_mismatch")
    for field, value in expected.items():
        if summary.get(field) != value:
            errors.append(f"{field}_mismatch")
    for field in [
        "all_packets_have_single_cx_edge_family",
        "all_packets_have_exact_matrix_target",
        "semantic_replay_targets_constructed",
    ]:
        if summary.get(field) is not True:
            errors.append(f"{field}_must_be_true")
    for field in [
        "semantic_replay_certificate_claimed",
        "shorter_rewrite_claimed",
        "resource_saving_claimed",
        "b7_ledger_improvement_claimed",
    ]:
        if summary.get(field) is not False:
            errors.append(f"{field}_must_remain_false")
        if payload["claim_boundary"].get(field) is not False:
            errors.append(f"claim_boundary_{field}_must_remain_false")
    for packet in payload.get("semantic_replay_packets", []):
        if packet["semantic_matrix"]["dimension"] != 4:
            errors.append(f"{packet['candidate_line_number']}_matrix_dimension_not_4")
        if packet["accepted_occurrence_removal"] != 0:
            errors.append(f"{packet['candidate_line_number']}_accepted_removal_must_be_zero")
    return errors


def markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone_01 Semantic Replay Packet Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This artifact consumes T-B1-004ad and converts the blocked carrier CNOT stacks into exact local semantic replay targets. It creates synthesis inputs; it does not claim a shorter rewrite or B7 resource improvement.",
        "",
        "## Summary",
        "",
        f"- Semantic replay packets: `{summary['semantic_replay_packet_count']}`",
        f"- Two-qubit packets: `{summary['two_qubit_packet_count']}`",
        f"- Support qubit range: `{summary['min_support_qubit_count']}` to `{summary['max_support_qubit_count']}`",
        f"- Total window gates: `{summary['total_window_gate_count']}`",
        f"- Total CNOT / single-qubit gates: `{summary['total_cx_count']}` / `{summary['total_single_qubit_gate_count']}`",
        f"- Unique semantic fingerprints: `{summary['unique_semantic_fingerprint_count']}`",
        f"- Exact matrix targets constructed: `{summary['all_packets_have_exact_matrix_target']}`",
        f"- Accepted occurrence/proxy-T reduction: `{summary['accepted_occurrence_removal']}` / `{summary['accepted_proxy_t_reduction']}`",
        f"- Validation errors: `{summary['validation_error_count']}`",
        "",
        "## Replay Packets",
        "",
        "| Pattern | Candidate line | Window | Support | Gates | CX | 1Q | Fingerprint |",
        "|---|---:|---|---|---:|---:|---:|---|",
    ]
    for packet in payload["semantic_replay_packets"]:
        fingerprint = packet["semantic_matrix"]["global_phase_normalized_sha256"][:16]
        lines.append(
            "| "
            f"{packet['pattern_id']} | "
            f"{packet['candidate_line_number']} | "
            f"{packet['window_start_line']}-{packet['window_end_line']} | "
            f"{packet['support_qubits']} | "
            f"{packet['window_line_count']} | "
            f"{packet['cx_count']} | "
            f"{packet['single_qubit_gate_count']} | "
            f"`{fingerprint}` |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "The supported claim is limited to packet construction: three blocked carrier candidates now have stable 2-qubit unitary targets and normalized operation lists. The gate does not synthesize a replacement, does not replay a replacement in the full circuit, and does not reduce the B7 ledger.",
            "",
            "## Next Required Gate",
            "",
            "The next gate must consume these packets and search for an equivalent local replacement with fewer accepted B7-costed operations, then produce a full-circuit replay certificate before any resource-saving claim is allowed.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path, default=JSON_OUT)
    parser.add_argument("--md-out", type=Path, default=MD_OUT)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    payload = build_payload()
    write_json(args.json_out, payload, args.pretty)
    write_text(args.md_out, markdown(payload))
    if args.pretty:
        print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    if payload["validation_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
