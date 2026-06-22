#!/usr/bin/env python3
"""OpenQASM 3 export gate for the B1/B7 cone_01 candidate.

T-B1-004av emitted a legacy-dialect replay candidate because the source fixture
is still OpenQASM 2.0. This gate keeps that artifact intact and exports an
OpenQASM 3-facing version that future replay, parser, and hardware-toolchain
checks can consume.

The export is intentionally a dialect gate only. It preserves operation counts
and the existing candidate path, but it does not claim new equivalence, local-U3
pricing, occurrence removal, or B7 resource credit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
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
SOURCE_RESULT = ROOT / "results" / "B1_B7_cone01_qasm2_candidate_rewrite_gate_v0.json"
SOURCE_QASM = (
    ROOT
    / "results"
    / "B1_B7_cone01_qasm2_candidate_rewrite_gate"
    / "gcm_h6_line268_line1381_candidate.qasm"
)
OUT_DIR = ROOT / "results" / "B1_B7_cone01_openqasm3_candidate_export_gate"
QASM_OUT = OUT_DIR / "gcm_h6_line268_line1381_candidate_openqasm3.qasm"
JSON_OUT = ROOT / "results" / "B1_B7_cone01_openqasm3_candidate_export_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_openqasm3_candidate_export_gate.md"

METHOD = "b1_b7_cone01_openqasm3_candidate_export_gate_v0"
STATUS = "cone01_openqasm3_candidate_exported_not_replay_certified"
MODEL_STATUS = "openqasm3_candidate_export_exists_without_new_b7_credit"

QREG_RE = re.compile(r"^qreg\s+([A-Za-z_]\w*)\[(\d+)\];$")
CREG_RE = re.compile(r"^creg\s+([A-Za-z_]\w*)\[(\d+)\];$")
QUBIT_RE = re.compile(r"^qubit\[\d+\]\s+[A-Za-z_]\w*;$")
BIT_RE = re.compile(r"^bit\[\d+\]\s+[A-Za-z_]\w*;$")
U3_RE = re.compile(r"^u3\((.*)\)\s+(q\[\d+\]);$", re.IGNORECASE)
MEASURE_RE = re.compile(r"^measure\s+(q\[\d+\])\s*->\s*(c\[\d+\]);$", re.IGNORECASE)
CX_RE = re.compile(r"^cx\s+q\[\d+\]\s*,\s*q\[\d+\]\s*;$", re.IGNORECASE)
RZ_RE = re.compile(r"^rz\(.*\)\s+q\[\d+\];$", re.IGNORECASE)
U_RE = re.compile(r"^U\(.*\)\s+q\[\d+\];$")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def op_counts(lines: list[str]) -> dict[str, int]:
    counts = {"u3_or_U": 0, "rz": 0, "cx": 0, "measure": 0, "other_operation": 0}
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        if line.startswith("OPENQASM") or line.startswith("include "):
            continue
        if QREG_RE.match(line) or CREG_RE.match(line) or QUBIT_RE.match(line) or BIT_RE.match(line):
            continue
        if U3_RE.match(line) or U_RE.match(line):
            counts["u3_or_U"] += 1
        elif RZ_RE.match(line):
            counts["rz"] += 1
        elif CX_RE.match(line):
            counts["cx"] += 1
        elif MEASURE_RE.match(line) or re.match(r"^c\[\d+\]\s*=\s*measure\s+q\[\d+\];$", line):
            counts["measure"] += 1
        else:
            counts["other_operation"] += 1
    return counts


def qasm2_to_qasm3(source_text: str) -> tuple[str, list[dict[str, Any]]]:
    output: list[str] = []
    conversions: list[dict[str, Any]] = []
    for line_number, raw in enumerate(source_text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            output.append("")
            continue
        if stripped == "OPENQASM 2.0;":
            output.append("OPENQASM 3.0;")
            conversions.append({"line": line_number, "from": stripped, "to": "OPENQASM 3.0;"})
            continue
        if stripped == 'include "qelib1.inc";':
            output.append('include "stdgates.inc";')
            conversions.append(
                {"line": line_number, "from": stripped, "to": 'include "stdgates.inc";'}
            )
            continue
        qreg = QREG_RE.match(stripped)
        if qreg:
            converted = f"qubit[{qreg.group(2)}] {qreg.group(1)};"
            output.append(converted)
            conversions.append({"line": line_number, "from": stripped, "to": converted})
            continue
        creg = CREG_RE.match(stripped)
        if creg:
            converted = f"bit[{creg.group(2)}] {creg.group(1)};"
            output.append(converted)
            conversions.append({"line": line_number, "from": stripped, "to": converted})
            continue
        u3 = U3_RE.match(stripped)
        if u3:
            converted = f"U({u3.group(1)}) {u3.group(2)};"
            output.append(converted)
            conversions.append({"line": line_number, "from": "u3", "to": "U"})
            continue
        measure = MEASURE_RE.match(stripped)
        if measure:
            converted = f"{measure.group(2)} = measure {measure.group(1)};"
            output.append(converted)
            conversions.append({"line": line_number, "from": stripped, "to": converted})
            continue
        output.append(stripped)
    return "\n".join(output) + "\n", conversions


def validate_openqasm3_text(text: str, source_counts: dict[str, int]) -> list[str]:
    errors: list[str] = []
    lines = text.splitlines()
    if not lines or lines[0].strip() != "OPENQASM 3.0;":
        errors.append("missing_openqasm3_header")
    if len(lines) < 2 or lines[1].strip() != 'include "stdgates.inc";':
        errors.append("missing_stdgates_include")
    if not any(line.strip() == "qubit[19] q;" for line in lines):
        errors.append("missing_qubit_register")
    if not any(line.strip() == "bit[1] c;" for line in lines):
        errors.append("missing_bit_register")
    if any("qreg " in line or "creg " in line or "qelib1.inc" in line for line in lines):
        errors.append("legacy_declaration_remains")
    if any(line.strip().lower().startswith("u3(") for line in lines):
        errors.append("legacy_u3_gate_remains")
    if any("->" in line for line in lines if "measure" in line):
        errors.append("legacy_measurement_arrow_remains")
    qasm3_counts = op_counts(lines)
    if qasm3_counts != source_counts:
        errors.append(f"operation_count_mismatch:{qasm3_counts}!={source_counts}")
    return errors


def build_payload(qasm_output: Path) -> dict[str, Any]:
    source_result = load_json(SOURCE_RESULT)
    source_text = SOURCE_QASM.read_text(encoding="utf-8")
    source_lines = source_text.splitlines()
    qasm3_text, conversions = qasm2_to_qasm3(source_text)
    qasm_output.parent.mkdir(parents=True, exist_ok=True)
    write_text(qasm_output, qasm3_text)

    source_counts = op_counts(source_lines)
    qasm3_counts = op_counts(qasm3_text.splitlines())
    validation_errors = validate_openqasm3_text(qasm3_text, source_counts)
    source_summary = source_result["summary"]
    accepted_removed = 0
    summary = {
        "source_method": source_result.get("method"),
        "source_candidate_qasm": display_path(SOURCE_QASM),
        "openqasm3_candidate_path": display_path(qasm_output),
        "source_dialect": "OPENQASM 2.0",
        "export_dialect": "OPENQASM 3.0",
        "stdgates_include_present": 'include "stdgates.inc";' in qasm3_text,
        "legacy_qelib_include_present": 'include "qelib1.inc";' in qasm3_text,
        "legacy_qreg_or_creg_present": any(
            line.strip().startswith(("qreg ", "creg ")) for line in qasm3_text.splitlines()
        ),
        "legacy_u3_gate_present": any(
            line.strip().lower().startswith("u3(") for line in qasm3_text.splitlines()
        ),
        "legacy_measure_arrow_present": any(
            "->" in line and "measure" in line for line in qasm3_text.splitlines()
        ),
        "qasm3_header_valid": qasm3_text.startswith("OPENQASM 3.0;\n"),
        "qubit_register_count": 19,
        "bit_register_count": 1,
        "source_line_count": len(source_lines),
        "openqasm3_line_count": len(qasm3_text.splitlines()),
        "source_operation_counts": source_counts,
        "openqasm3_operation_counts": qasm3_counts,
        "operation_counts_preserved": source_counts == qasm3_counts,
        "conversion_row_count": len(conversions),
        "u3_to_U_conversion_count": sum(1 for row in conversions if row["from"] == "u3"),
        "measurement_conversion_count": sum(1 for row in conversions if "measure" in row["from"]),
        "candidate_cnot_count": source_summary.get("candidate_cnot_count"),
        "candidate_cnot_delta": source_summary.get("candidate_cnot_delta"),
        "selected_candidate_line_numbers": source_summary.get("selected_candidate_line_numbers"),
        "accepted_openqasm3_export_artifact_count": 1 if not validation_errors else 0,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_local_u3_pricing_certificate_count": 0,
        "accepted_occurrence_removal": accepted_removed,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": max(0, REQUIRED_OCCURRENCE_REMOVALS - accepted_removed),
        "missing_proxy_t_after_gate": max(
            0,
            (REQUIRED_OCCURRENCE_REMOVALS - accepted_removed) * PROXY_T_PER_OCCURRENCE,
        ),
        "openqasm3_export_claimed": not validation_errors,
        "full_circuit_rewrite_claimed": False,
        "full_circuit_replay_claimed": False,
        "local_u3_pricing_accepted": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "source_sha256": sha256_text(source_text),
        "openqasm3_sha256": sha256_text(qasm3_text),
        "validation_error_count": len(validation_errors),
    }
    payload = {
        "benchmark_id": "B1",
        "linked_b7_problem_id": 21,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "workload": source_result.get("workload", "qasmbench_medium_exact/gcm_h6.qasm"),
        "source_candidate_rewrite_result": display_path(SOURCE_RESULT),
        "source_candidate_qasm": display_path(SOURCE_QASM),
        "openqasm3_candidate_qasm": display_path(qasm_output),
        "summary": summary,
        "conversion_rows": conversions[:25],
        "validation_errors": validation_errors,
        "claim_boundary": {
            "supported_claim": (
                "The selected line-268 plus line-1381 candidate now has an OpenQASM 3.0 "
                "export artifact with preserved operation counts and valid modern headers."
            ),
            "unsupported_claims": [
                "The export is not a new full-circuit replay proof.",
                "The export does not recover the dropped line-1378 overlap delta.",
                "The export does not price or eliminate the remaining off-grid local-U3 burden.",
                "The export does not create B7 occurrence, proxy-T, or space-time-volume credit.",
            ],
            "openqasm3_export_claimed": not validation_errors,
            "full_circuit_rewrite_claimed": False,
            "full_circuit_replay_claimed": False,
            "local_u3_pricing_accepted": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
    }
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    source_counts = summary["source_operation_counts"]
    qasm3_counts = summary["openqasm3_operation_counts"]
    lines = [
        "# B1/B7 cone_01 OpenQASM 3 Candidate Export Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This artifact consumes the legacy-dialect T-B1-004av candidate and exports an OpenQASM 3.0 candidate artifact for the line-268 plus line-1381 non-overlap patch subset. It is a dialect and portability gate, not a new resource-saving claim.",
        "",
        "## Summary",
        "",
        f"- Source candidate: `{payload['source_candidate_qasm']}`",
        f"- OpenQASM 3 candidate: `{payload['openqasm3_candidate_qasm']}`",
        f"- Source / export dialect: `{summary['source_dialect']}` / `{summary['export_dialect']}`",
        f"- Header valid / stdgates include present: `{summary['qasm3_header_valid']}` / `{summary['stdgates_include_present']}`",
        f"- Legacy qelib/qreg/creg/u3/measure-arrow remnants: `{summary['legacy_qelib_include_present']}` / `{summary['legacy_qreg_or_creg_present']}` / `{summary['legacy_u3_gate_present']}` / `{summary['legacy_measure_arrow_present']}`",
        f"- Source / OpenQASM 3 operation counts: `{source_counts}` / `{qasm3_counts}`",
        f"- Operation counts preserved: `{summary['operation_counts_preserved']}`",
        f"- u3 -> U conversions / measurement conversions: `{summary['u3_to_U_conversion_count']}` / `{summary['measurement_conversion_count']}`",
        f"- Candidate CNOT count / delta: `{summary['candidate_cnot_count']}` / `{summary['candidate_cnot_delta']}`",
        f"- Accepted OpenQASM 3 export artifacts: `{summary['accepted_openqasm3_export_artifact_count']}`",
        f"- Accepted replay / local-U3 pricing / occurrence / proxy-T reduction: `{summary['accepted_full_circuit_replay_certificate_count']}` / `{summary['accepted_local_u3_pricing_certificate_count']}` / `{summary['accepted_occurrence_removal']}` / `{summary['accepted_proxy_t_reduction']}`",
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
            "The next gate must parse or replay this OpenQASM 3 artifact through a modern toolchain, then connect it to symbolic equivalence or local-U3 pricing before any B7 resource credit is allowed.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path, default=JSON_OUT)
    parser.add_argument("--markdown-output", type=Path, default=MD_OUT)
    parser.add_argument("--qasm-output", type=Path, default=QASM_OUT)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    payload = build_payload(args.qasm_output)
    write_json(args.json_output, payload, args.pretty)
    write_text(args.markdown_output, render_markdown(payload))
    print(json.dumps(payload["summary"], indent=2 if args.pretty else None, sort_keys=True))


if __name__ == "__main__":
    main()
