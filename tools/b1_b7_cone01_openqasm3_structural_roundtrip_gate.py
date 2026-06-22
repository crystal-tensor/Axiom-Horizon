#!/usr/bin/env python3
"""Structural roundtrip gate for the B1/B7 cone_01 OpenQASM 3 artifact.

T-B1-004bu exported a modern OpenQASM 3 candidate and T-B1-004bv showed it
passes the project-local parser. This gate checks the stronger dialect bridge:
the legacy OpenQASM 2 candidate and the OpenQASM 3 artifact must normalize to
the exact same instruction stream.

The gate deliberately accepts only a structural roundtrip artifact. It is not a
semantic replay proof, local-U3 pricing certificate, occurrence removal, or B7
resource credit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from b1_b7_cone01_carrier_absorption_inventory_gate import (
    PROXY_T_PER_OCCURRENCE,
    REQUIRED_OCCURRENCE_REMOVALS,
    display_path,
    load_json,
    write_json,
    write_text,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_RESULT = ROOT / "results" / "B1_B7_cone01_openqasm3_parser_readiness_gate_v0.json"
QASM2_PATH = (
    ROOT
    / "results"
    / "B1_B7_cone01_qasm2_candidate_rewrite_gate"
    / "gcm_h6_line268_line1381_candidate.qasm"
)
QASM3_PATH = (
    ROOT
    / "results"
    / "B1_B7_cone01_openqasm3_candidate_export_gate"
    / "gcm_h6_line268_line1381_candidate_openqasm3.qasm"
)
JSON_OUT = ROOT / "results" / "B1_B7_cone01_openqasm3_structural_roundtrip_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_openqasm3_structural_roundtrip_gate.md"

METHOD = "b1_b7_cone01_openqasm3_structural_roundtrip_gate_v0"
STATUS = "cone01_openqasm3_structural_roundtrip_matches_legacy_candidate"
MODEL_STATUS = "openqasm3_candidate_structurally_matches_legacy_instruction_stream_without_replay_credit"

QASM2_SKIP_RE = re.compile(
    r'^(?:OPENQASM 2\.0;|include "qelib1\.inc";|qreg\s+q\[\d+\];|creg\s+c\[\d+\];)$'
)
QASM3_SKIP_RE = re.compile(
    r'^(?:OPENQASM 3\.0;|include "stdgates\.inc";|qubit\[\d+\]\s+q;|bit\[\d+\]\s+c;)$'
)
U_RE = re.compile(r"^(?:u3|U)\(([^()]*)\)\s+q\[(\d+)\];$", re.IGNORECASE)
RZ_RE = re.compile(r"^rz\(([^()]*)\)\s+q\[(\d+)\];$", re.IGNORECASE)
CX_RE = re.compile(r"^cx\s+q\[(\d+)\]\s*,\s*q\[(\d+)\];$", re.IGNORECASE)
MEASURE_ARROW_RE = re.compile(r"^measure\s+q\[(\d+)\]\s*->\s*c\[(\d+)\];$", re.IGNORECASE)
MEASURE_ASSIGN_RE = re.compile(r"^c\[(\d+)\]\s*=\s*measure\s+q\[(\d+)\];$", re.IGNORECASE)


def normalize_args(args: str) -> str:
    return ",".join(part.strip().replace(" ", "") for part in args.split(","))


def normalize_line(line: str, dialect: str, line_number: int) -> str | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("//"):
        return None
    if dialect == "qasm2" and QASM2_SKIP_RE.match(stripped):
        return None
    if dialect == "qasm3" and QASM3_SKIP_RE.match(stripped):
        return None

    u_match = U_RE.match(stripped)
    if u_match:
        return f"U({normalize_args(u_match.group(1))})|q[{u_match.group(2)}]"

    rz_match = RZ_RE.match(stripped)
    if rz_match:
        return f"rz({normalize_args(rz_match.group(1))})|q[{rz_match.group(2)}]"

    cx_match = CX_RE.match(stripped)
    if cx_match:
        return f"cx|q[{cx_match.group(1)}],q[{cx_match.group(2)}]"

    arrow_match = MEASURE_ARROW_RE.match(stripped)
    if arrow_match:
        return f"measure|q[{arrow_match.group(1)}]->c[{arrow_match.group(2)}]"

    assign_match = MEASURE_ASSIGN_RE.match(stripped)
    if assign_match:
        return f"measure|q[{assign_match.group(2)}]->c[{assign_match.group(1)}]"

    raise ValueError(f"unparsed_{dialect}_line_{line_number}: {stripped}")


def normalize_qasm(text: str, dialect: str) -> list[str]:
    rows: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        normalized = normalize_line(line, dialect, line_number)
        if normalized is not None:
            rows.append(normalized)
    return rows


def operation_name(row: str) -> str:
    return row.split("(", 1)[0] if row.startswith(("U(", "rz(")) else row.split("|", 1)[0]


def stream_hash(rows: list[str]) -> str:
    return hashlib.sha256(("\n".join(rows) + "\n").encode("utf-8")).hexdigest()


def find_mismatches(left: list[str], right: list[str]) -> list[dict[str, Any]]:
    mismatches: list[dict[str, Any]] = []
    for index, (left_row, right_row) in enumerate(zip(left, right)):
        if left_row != right_row:
            mismatches.append(
                {
                    "index": index,
                    "qasm2": left_row,
                    "qasm3": right_row,
                }
            )
    if len(left) != len(right):
        longer = left if len(left) > len(right) else right
        label = "qasm2" if len(left) > len(right) else "qasm3"
        for index in range(min(len(left), len(right)), len(longer)):
            mismatches.append({"index": index, label: longer[index]})
    return mismatches


def build_payload() -> dict[str, Any]:
    parser_payload = load_json(SOURCE_RESULT)
    qasm2_text = QASM2_PATH.read_text(encoding="utf-8")
    qasm3_text = QASM3_PATH.read_text(encoding="utf-8")
    qasm2_rows = normalize_qasm(qasm2_text, "qasm2")
    qasm3_rows = normalize_qasm(qasm3_text, "qasm3")
    mismatches = find_mismatches(qasm2_rows, qasm3_rows)
    counts = dict(Counter(operation_name(row) for row in qasm3_rows))
    expected_counts = {"U": 487, "rz": 601, "cx": 789, "measure": 1}
    accepted_removed = 0
    streams_match = qasm2_rows == qasm3_rows
    qasm2_hash = stream_hash(qasm2_rows)
    qasm3_hash = stream_hash(qasm3_rows)
    summary = {
        "source_method": parser_payload.get("method"),
        "source_openqasm3_parser_readiness_gate": display_path(SOURCE_RESULT),
        "qasm2_candidate_path": display_path(QASM2_PATH),
        "openqasm3_candidate_path": display_path(QASM3_PATH),
        "qasm2_normalized_instruction_count": len(qasm2_rows),
        "openqasm3_normalized_instruction_count": len(qasm3_rows),
        "normalized_instruction_count": len(qasm3_rows),
        "normalized_streams_match": streams_match,
        "stream_mismatch_count": len(mismatches),
        "stream_length_delta": len(qasm3_rows) - len(qasm2_rows),
        "qasm2_normalized_stream_sha256": qasm2_hash,
        "openqasm3_normalized_stream_sha256": qasm3_hash,
        "normalized_stream_sha256": qasm3_hash,
        "operation_counts": counts,
        "expected_operation_counts": expected_counts,
        "operation_counts_match": counts == expected_counts,
        "first_normalized_instruction": qasm3_rows[0] if qasm3_rows else None,
        "last_normalized_instruction": qasm3_rows[-1] if qasm3_rows else None,
        "accepted_structural_roundtrip_artifact_count": 1 if streams_match and counts == expected_counts else 0,
        "accepted_qiskit_loader_parse_artifact_count": 0,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_local_u3_pricing_certificate_count": 0,
        "accepted_occurrence_removal": accepted_removed,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": max(0, REQUIRED_OCCURRENCE_REMOVALS - accepted_removed),
        "missing_proxy_t_after_gate": max(
            0,
            (REQUIRED_OCCURRENCE_REMOVALS - accepted_removed) * PROXY_T_PER_OCCURRENCE,
        ),
        "structural_roundtrip_claimed": streams_match,
        "qiskit_loader_parse_claimed": False,
        "full_circuit_replay_claimed": False,
        "local_u3_pricing_accepted": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "validation_error_count": 0,
    }
    validation_errors = validate_summary(summary)
    summary["validation_error_count"] = len(validation_errors)
    return {
        "benchmark_id": "B1",
        "linked_b7_problem_id": 21,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "workload": parser_payload.get("workload", "qasmbench_medium_exact/gcm_h6.qasm"),
        "source_openqasm3_parser_readiness_gate": display_path(SOURCE_RESULT),
        "qasm2_candidate_qasm": display_path(QASM2_PATH),
        "openqasm3_candidate_qasm": display_path(QASM3_PATH),
        "summary": summary,
        "mismatch_preview": mismatches[:10],
        "validation_errors": validation_errors,
        "claim_boundary": {
            "supported_claim": (
                "The legacy OpenQASM 2 candidate and OpenQASM 3 artifact normalize to the same "
                "1,878-instruction stream with zero structural mismatches."
            ),
            "unsupported_claims": [
                "The structural roundtrip is not a Qiskit OpenQASM 3 loader parse.",
                "The structural roundtrip is not a full-circuit semantic replay proof.",
                "The structural roundtrip does not price or eliminate local-U3 burden.",
                "The structural roundtrip does not create B7 occurrence, proxy-T, or space-time-volume credit.",
            ],
            "structural_roundtrip_claimed": streams_match,
            "qiskit_loader_parse_claimed": False,
            "full_circuit_replay_claimed": False,
            "local_u3_pricing_accepted": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
    }


def validate_summary(summary: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_fields = {
        "qasm2_normalized_instruction_count": 1878,
        "openqasm3_normalized_instruction_count": 1878,
        "normalized_instruction_count": 1878,
        "normalized_streams_match": True,
        "stream_mismatch_count": 0,
        "stream_length_delta": 0,
        "operation_counts": {"U": 487, "rz": 601, "cx": 789, "measure": 1},
        "expected_operation_counts": {"U": 487, "rz": 601, "cx": 789, "measure": 1},
        "operation_counts_match": True,
        "first_normalized_instruction": "U(pi,-pi/8,-7*pi/8)|q[1]",
        "last_normalized_instruction": "measure|q[4]->c[0]",
        "accepted_structural_roundtrip_artifact_count": 1,
        "accepted_qiskit_loader_parse_artifact_count": 0,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_local_u3_pricing_certificate_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": 30,
        "missing_proxy_t_after_gate": 600,
        "structural_roundtrip_claimed": True,
        "qiskit_loader_parse_claimed": False,
        "full_circuit_replay_claimed": False,
        "local_u3_pricing_accepted": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
    }
    for field, expected in expected_fields.items():
        if summary.get(field) != expected:
            errors.append(f"{field}_expected_{expected}_got_{summary.get(field)}")
    if summary.get("qasm2_normalized_stream_sha256") != summary.get("openqasm3_normalized_stream_sha256"):
        errors.append("normalized_stream_hashes_differ")
    return errors


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 cone_01 OpenQASM 3 Structural Roundtrip Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This artifact consumes T-B1-004bv and compares the legacy OpenQASM 2 candidate against the OpenQASM 3 artifact after dialect normalization.",
        "",
        "## Summary",
        "",
        f"- OpenQASM 2 candidate: `{payload['qasm2_candidate_qasm']}`",
        f"- OpenQASM 3 candidate: `{payload['openqasm3_candidate_qasm']}`",
        f"- Normalized instruction counts, QASM2 / QASM3: `{summary['qasm2_normalized_instruction_count']}` / `{summary['openqasm3_normalized_instruction_count']}`",
        f"- Normalized streams match / mismatch count / length delta: `{summary['normalized_streams_match']}` / `{summary['stream_mismatch_count']}` / `{summary['stream_length_delta']}`",
        f"- Operation counts: `{summary['operation_counts']}`",
        f"- Normalized stream SHA256: `{summary['normalized_stream_sha256']}`",
        f"- First / last normalized instruction: `{summary['first_normalized_instruction']}` / `{summary['last_normalized_instruction']}`",
        f"- Accepted structural roundtrip artifacts: `{summary['accepted_structural_roundtrip_artifact_count']}`",
        f"- Accepted Qiskit loader parse / replay / local-U3 pricing artifacts: `{summary['accepted_qiskit_loader_parse_artifact_count']}` / `{summary['accepted_full_circuit_replay_certificate_count']}` / `{summary['accepted_local_u3_pricing_certificate_count']}`",
        f"- Accepted occurrence / proxy-T reduction: `{summary['accepted_occurrence_removal']}` / `{summary['accepted_proxy_t_reduction']}`",
        f"- Validation errors: `{summary['validation_error_count']}`",
        "",
        "## Claim Boundary",
        "",
        payload["claim_boundary"]["supported_claim"],
        "",
        "Unsupported claims:",
        "",
    ]
    for claim in payload["claim_boundary"]["unsupported_claims"]:
        lines.append(f"- {claim}")
    lines.extend(
        [
            "",
            "## Next Required Gate",
            "",
            "Run the same artifact through a reproducible OpenQASM 3 loader or a full semantic replay path, then separately prove or price the remaining local-U3 burden before any B7 resource credit is accepted.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path, default=JSON_OUT)
    parser.add_argument("--markdown-output", type=Path, default=MD_OUT)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    payload = build_payload()
    write_json(args.json_output, payload, args.pretty)
    write_text(args.markdown_output, render_markdown(payload))
    print(json.dumps(payload["summary"], indent=2 if args.pretty else None, sort_keys=True))


if __name__ == "__main__":
    main()
