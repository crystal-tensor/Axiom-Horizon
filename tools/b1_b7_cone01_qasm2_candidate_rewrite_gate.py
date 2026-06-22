#!/usr/bin/env python3
"""QASM2 candidate rewrite gate for the B1/B7 cone_01 patch subset.

T-B1-004au selected a non-overlapping bounded patch subset, but still left the
patches as OpenQASM 3 snippets rather than a source-circuit candidate. This
gate performs the narrow dialect bridge needed for the next replay step:
selected snippets are converted to OpenQASM 2 `u3`/`cx` lines and inserted into
the original `gcm_h6` source windows.

The emitted QASM is intentionally a candidate artifact only. It is not accepted
as a full-circuit replay certificate or a B7 ledger saving until a later gate
proves whole-circuit equivalence and resource accounting.
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
SUBSET_PATH = ROOT / "results" / "B1_B7_cone01_nonoverlap_patch_subset_gate_v0.json"
SOURCE_QASM_PATH = (
    ROOT / "results" / "b1_native_t_resource_optimizer" / "qasmbench_medium_exact" / "gcm_h6.qasm"
)
OUT_DIR = ROOT / "results" / "B1_B7_cone01_qasm2_candidate_rewrite_gate"
QASM_OUT = OUT_DIR / "gcm_h6_line268_line1381_candidate.qasm"
JSON_OUT = ROOT / "results" / "B1_B7_cone01_qasm2_candidate_rewrite_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_qasm2_candidate_rewrite_gate.md"

METHOD = "b1_b7_cone01_qasm2_candidate_rewrite_gate_v0"
STATUS = "cone01_qasm2_candidate_rewrite_emitted_not_replay_certified"
MODEL_STATUS = "qasm2_candidate_rewrite_exists_but_full_circuit_replay_is_pending"

CX_RE = re.compile(r"^\s*cx\s+q\[\d+\]\s*,\s*q\[\d+\]\s*;\s*$", re.IGNORECASE)
QASM3_U_RE = re.compile(r"^U\((.*)\)\s+(q\[\d+\]);$")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def qasm_dialect(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped.rstrip(";")
    return "unknown"


def count_cx(lines: list[str]) -> int:
    return sum(1 for line in lines if CX_RE.match(line))


def qasm3_snippet_to_qasm2(snippet: list[str]) -> list[str]:
    converted: list[str] = []
    for raw in snippet:
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("//"):
            converted.append("// QASM2 bridged bounded replacement snippet")
            continue
        match = QASM3_U_RE.match(stripped)
        if match:
            converted.append(f"u3({match.group(1)}) {match.group(2)};")
        elif stripped.lower().startswith("cx "):
            converted.append(stripped)
        else:
            raise ValueError(f"unsupported snippet line for QASM2 bridge: {raw}")
    return converted


def replace_windows(source_lines: list[str], rows: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    output = list(source_lines)
    replacement_rows: list[dict[str, Any]] = []
    offset = 0
    for row in sorted(rows, key=lambda item: int(item["window_start_line"])):
        start = int(row["window_start_line"])
        end = int(row["window_end_line"])
        start_index = start - 1 + offset
        end_index = end + offset
        original_window = output[start_index:end_index]
        replacement = qasm3_snippet_to_qasm2(row["qasm3_patch_snippet"])
        original_cx = count_cx(original_window)
        replacement_cx = count_cx(replacement)
        output[start_index:end_index] = replacement
        offset += len(replacement) - len(original_window)
        replacement_rows.append(
            {
                "candidate_line_number": int(row["candidate_line_number"]),
                "source_window_start_line": start,
                "source_window_end_line": end,
                "source_window_line_count": len(original_window),
                "replacement_line_count": len(replacement),
                "source_cnot_count": original_cx,
                "replacement_cnot_count": replacement_cx,
                "candidate_cnot_reduction": original_cx - replacement_cx,
                "replacement_comment_line_count": sum(1 for line in replacement if line.startswith("//")),
                "source_window_sha256": sha256_text("\n".join(original_window) + "\n"),
                "replacement_window_sha256": sha256_text("\n".join(replacement) + "\n"),
                "qasm2_bridge_available": True,
                "accepted_full_circuit_replay_certificate": False,
                "accepted_full_circuit_qasm_patch": False,
                "accepted_occurrence_removal": 0,
                "accepted_proxy_t_reduction": 0,
            }
        )
    return output, replacement_rows


def build_payload(qasm_output: Path) -> dict[str, Any]:
    subset = load_json(SUBSET_PATH)
    selected_rows = subset["selected_nonoverlap_patch_rows"]
    source_text = SOURCE_QASM_PATH.read_text(encoding="utf-8")
    source_lines = source_text.splitlines()
    candidate_lines, replacement_rows = replace_windows(source_lines, selected_rows)
    candidate_text = "\n".join(candidate_lines) + "\n"

    qasm_output.parent.mkdir(parents=True, exist_ok=True)
    write_text(qasm_output, candidate_text)

    source_cx = count_cx(source_lines)
    candidate_cx = count_cx(candidate_lines)
    selected_delta = sum(row["candidate_cnot_reduction"] for row in replacement_rows)
    accepted_removed = 0
    summary = {
        "source_nonoverlap_method": subset.get("method"),
        "selected_candidate_line_numbers": [row["candidate_line_number"] for row in replacement_rows],
        "dropped_overlap_candidate_line_numbers": subset["summary"][
            "dropped_overlap_candidate_line_numbers"
        ],
        "source_qasm_dialect": qasm_dialect(source_text),
        "candidate_qasm_dialect": qasm_dialect(candidate_text),
        "qasm2_candidate_rewrite_emitted": True,
        "qasm2_candidate_path": display_path(qasm_output),
        "source_line_count": len(source_lines),
        "candidate_line_count": len(candidate_lines),
        "selected_source_window_line_count": sum(
            row["source_window_line_count"] for row in replacement_rows
        ),
        "selected_replacement_line_count": sum(
            row["replacement_line_count"] for row in replacement_rows
        ),
        "source_cnot_count": source_cx,
        "candidate_cnot_count": candidate_cx,
        "candidate_cnot_delta": source_cx - candidate_cx,
        "selected_candidate_cnot_reduction": selected_delta,
        "replacement_window_count": len(replacement_rows),
        "qasm2_bridge_patch_count": sum(1 for row in replacement_rows if row["qasm2_bridge_available"]),
        "full_circuit_replay_certificate_count": 0,
        "accepted_full_circuit_qasm_patch_count": 0,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_occurrence_removal": accepted_removed,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": max(0, REQUIRED_OCCURRENCE_REMOVALS - accepted_removed),
        "missing_proxy_t_after_gate": max(
            0,
            (REQUIRED_OCCURRENCE_REMOVALS - accepted_removed) * PROXY_T_PER_OCCURRENCE,
        ),
        "qasm2_candidate_claimed_as_full_circuit_patch": False,
        "full_circuit_rewrite_claimed": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "source_sha256": sha256_text(source_text),
        "candidate_sha256": sha256_text(candidate_text),
    }
    payload = {
        "benchmark_id": "B1",
        "linked_b7_problem_id": 21,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "workload": subset.get("workload", "qasmbench_medium_exact/gcm_h6.qasm"),
        "source_nonoverlap_patch_subset_result": display_path(SUBSET_PATH),
        "source_qasm": display_path(SOURCE_QASM_PATH),
        "candidate_qasm": display_path(qasm_output),
        "summary": summary,
        "replacement_rows": replacement_rows,
        "claim_boundary": {
            "supported_claim": (
                "A QASM2 candidate rewrite file now exists for the selected non-overlap "
                "bounded patch subset at line 268 and line 1381."
            ),
            "unsupported_claims": [
                "The candidate rewrite is not yet a full-circuit replay certificate.",
                "The candidate rewrite does not recover the dropped line-1378 overlap delta.",
                "The candidate rewrite does not yet accept a B7 occurrence or proxy-T reduction.",
                "The remaining line-1381 off-grid local-U3 parameters are not priced or eliminated.",
            ],
            "qasm2_candidate_claimed_as_full_circuit_patch": False,
            "full_circuit_rewrite_claimed": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
    }
    payload["summary"]["validation_error_count"] = len(validate_payload(payload, qasm_output))
    return payload


def validate_payload(payload: dict[str, Any], qasm_output: Path) -> list[str]:
    errors: list[str] = []
    summary = payload.get("summary", {})
    rows = payload.get("replacement_rows", [])
    if payload.get("method") != METHOD:
        errors.append("method_mismatch")
    if payload.get("status") != STATUS:
        errors.append("status_mismatch")
    expected = {
        "selected_candidate_line_numbers": [268, 1381],
        "dropped_overlap_candidate_line_numbers": [1378],
        "source_qasm_dialect": "OPENQASM 2.0",
        "candidate_qasm_dialect": "OPENQASM 2.0",
        "qasm2_candidate_rewrite_emitted": True,
        "candidate_cnot_delta": 6,
        "selected_candidate_cnot_reduction": 6,
        "replacement_window_count": 2,
        "qasm2_bridge_patch_count": 2,
        "full_circuit_replay_certificate_count": 0,
        "accepted_full_circuit_qasm_patch_count": 0,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": 30,
        "missing_proxy_t_after_gate": 600,
    }
    for field, value in expected.items():
        if summary.get(field) != value:
            errors.append(f"{field}_expected_{value}_got_{summary.get(field)}")
    for field in [
        "qasm2_candidate_claimed_as_full_circuit_patch",
        "full_circuit_rewrite_claimed",
        "resource_saving_claimed",
        "b7_ledger_improvement_claimed",
    ]:
        if summary.get(field) is not False or payload.get("claim_boundary", {}).get(field) is not False:
            errors.append(f"{field}_must_remain_false")
    if not qasm_output.exists():
        errors.append("candidate_qasm_missing")
    else:
        candidate_text = qasm_output.read_text(encoding="utf-8")
        if "OPENQASM 3" in candidate_text:
            errors.append("candidate_qasm_must_not_contain_openqasm3_marker")
        if re.search(r"^U\(", candidate_text, re.MULTILINE):
            errors.append("candidate_qasm_must_not_contain_qasm3_U_gate")
    if [row.get("candidate_line_number") for row in rows] != [268, 1381]:
        errors.append("replacement_rows_must_be_268_1381")
    for row in rows:
        if row.get("qasm2_bridge_available") is not True:
            errors.append(f"line_{row.get('candidate_line_number')}_bridge_missing")
        if row.get("accepted_full_circuit_qasm_patch") is not False:
            errors.append(f"line_{row.get('candidate_line_number')}_must_not_accept_patch")
        if row.get("accepted_full_circuit_replay_certificate") is not False:
            errors.append(f"line_{row.get('candidate_line_number')}_must_not_accept_replay")
        if row.get("accepted_occurrence_removal") != 0:
            errors.append(f"line_{row.get('candidate_line_number')}_must_not_remove_occurrence")
    return errors


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 cone_01 QASM2 Candidate Rewrite Gate",
        "",
        "## Summary",
        "",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Candidate QASM: `{payload['candidate_qasm']}`",
        f"- Source / candidate dialect: `{summary['source_qasm_dialect']}` / `{summary['candidate_qasm_dialect']}`",
        f"- Selected lines / dropped overlap lines: `{summary['selected_candidate_line_numbers']}` / `{summary['dropped_overlap_candidate_line_numbers']}`",
        f"- Source / candidate CNOT count: `{summary['source_cnot_count']}` / `{summary['candidate_cnot_count']}`",
        f"- Candidate CNOT delta: `{summary['candidate_cnot_delta']}`",
        f"- QASM2 bridge patch count: `{summary['qasm2_bridge_patch_count']}`",
        f"- Accepted full-circuit patch / replay / occurrence / proxy-T reduction: `{summary['accepted_full_circuit_qasm_patch_count']}` / `{summary['accepted_full_circuit_replay_certificate_count']}` / `{summary['accepted_occurrence_removal']}` / `{summary['accepted_proxy_t_reduction']}`",
        f"- Validation errors: `{summary['validation_error_count']}`",
        "",
        "## Replacement Rows",
        "",
        "| Line | Source window | Source lines | Replacement lines | Source CNOT | Replacement CNOT | Candidate delta |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["replacement_rows"]:
        lines.append(
            f"| {row['candidate_line_number']} | {row['source_window_start_line']}-{row['source_window_end_line']} | "
            f"{row['source_window_line_count']} | {row['replacement_line_count']} | "
            f"{row['source_cnot_count']} | {row['replacement_cnot_count']} | {row['candidate_cnot_reduction']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            payload["claim_boundary"]["supported_claim"],
            "",
            "Unsupported claims:",
            "",
        ]
    )
    for claim in payload["claim_boundary"]["unsupported_claims"]:
        lines.append(f"- {claim}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "This moves the B1/B7 branch from standalone bounded snippets into a "
                "replay-consumable QASM2 candidate file. The candidate has the expected "
                "6-CNOT structural delta from line 268 plus line 1381, but it remains "
                "unaccepted until whole-circuit replay and B7 resource pricing pass."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path, default=JSON_OUT)
    parser.add_argument("--markdown-output", type=Path, default=MD_OUT)
    parser.add_argument("--qasm-output", type=Path, default=QASM_OUT)
    args = parser.parse_args()
    payload = build_payload(args.qasm_output)
    write_json(args.json_output, payload, True)
    write_text(args.markdown_output, render_markdown(payload))
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
