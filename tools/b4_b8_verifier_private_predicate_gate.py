#!/usr/bin/env python3
"""Add verifier-private predicate pressure to the B4/B8 support-spoofer boundary."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b4_b8_verifier_private_predicate_gate_v0"
STATUS = "verifier_private_predicate_pressure_not_protocol_soundness"
MODEL_STATUS = "analytic_private_predicate_gate_not_hardware_or_soundness_proof"
VERSION = "0.1"
SOURCE_METHOD = "b4_b8_nonstabilizer_support_spoofer_gate_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def digest_bits(label: str, count: int) -> list[int]:
    raw = hashlib.sha256(label.encode("utf-8")).digest()
    bits: list[int] = []
    for byte in raw:
        for shift in range(8):
            bits.append((byte >> shift) & 1)
            if len(bits) == count:
                return bits
    return bits


def predicate_packet(row: dict[str, Any], predicate_bits: int) -> dict[str, Any]:
    label = f"{row['task_id']}|{row['refresh_mode']}|{row['packet_index']}|private-v0"
    bits = digest_bits(label, predicate_bits)
    mask_digest = hashlib.sha256((label + "|mask").encode("utf-8")).hexdigest()
    target_digest = hashlib.sha256(("".join(str(bit) for bit in bits) + "|" + label).encode("utf-8")).hexdigest()
    return {
        "predicate_bit_count": predicate_bits,
        "private_mask_commitment": mask_digest,
        "private_target_commitment": target_digest,
        "predicate_family": "late_bound_private_parity_checks_over_challenge_bits",
        "predicate_material_public_to_spoofer": False,
    }


def build_gate(source_support_gate: Path, predicate_bits: int) -> dict[str, Any]:
    started = time.time()
    support = read_json(source_support_gate)
    rows: list[dict[str, Any]] = []

    for source_row in support.get("rows", []):
        packet = predicate_packet(source_row, predicate_bits)
        hidden_acceptance = 2.0 ** (-predicate_bits)
        one_bit_leaked_acceptance = 2.0 ** (-(predicate_bits - 1)) if predicate_bits > 0 else 1.0
        full_leakage_acceptance = 1.0
        rows.append(
            {
                "task_id": source_row["task_id"],
                "refresh_mode": source_row["refresh_mode"],
                "packet_index": source_row["packet_index"],
                "spoofer": source_row["spoofer"],
                "support_size": source_row["support_size"],
                "public_support_acceptance_rate": source_row[
                    "support_acceptance_rate_if_verifier_checks_only_public_support"
                ],
                "exact_transcript_success_probability": source_row[
                    "exact_transcript_success_probability"
                ],
                **packet,
                "hidden_private_predicate_acceptance_rate": hidden_acceptance,
                "one_private_bit_leaked_acceptance_rate": one_bit_leaked_acceptance,
                "full_private_predicate_leaked_acceptance_rate": full_leakage_acceptance,
                "support_only_to_private_predicate_suppression_factor": (
                    source_row["support_acceptance_rate_if_verifier_checks_only_public_support"]
                    / hidden_acceptance
                    if hidden_acceptance
                    else None
                ),
            }
        )

    circuit_count = int(support.get("circuit_count", 0))
    spoofer_count = int(support.get("spoofer_count", 0))
    attack_row_count = len(rows)
    hidden_acceptance_values = [row["hidden_private_predicate_acceptance_rate"] for row in rows]
    one_bit_values = [row["one_private_bit_leaked_acceptance_rate"] for row in rows]
    full_leak_values = [row["full_private_predicate_leaked_acceptance_rate"] for row in rows]
    support_values = [row["public_support_acceptance_rate"] for row in rows]
    max_hidden_acceptance = max(hidden_acceptance_values, default=1.0)
    min_hidden_acceptance = min(hidden_acceptance_values, default=1.0)
    max_one_bit_acceptance = max(one_bit_values, default=1.0)
    max_full_leak_acceptance = max(full_leak_values, default=1.0)
    max_support_acceptance = max(support_values, default=0.0)
    suppression_factor = max_support_acceptance / max_hidden_acceptance if max_hidden_acceptance else None
    private_predicate_suppresses_support_spoofer = max_hidden_acceptance < max_support_acceptance
    full_predicate_leakage_breaks_private_gate = max_full_leak_acceptance >= max_support_acceptance

    acceptance_gates = [
        {
            "gate": "source_support_spoofer_loaded",
            "passed": support.get("method") == SOURCE_METHOD and circuit_count == 36,
            "interpretation": "The gate consumes the support-aware spoofer boundary.",
        },
        {
            "gate": "private_predicate_commitments_present",
            "passed": attack_row_count == circuit_count * spoofer_count and all(
                row.get("private_mask_commitment") and row.get("private_target_commitment")
                for row in rows
            ),
            "interpretation": "Every attacked public transcript gets late-bound private predicate commitments.",
        },
        {
            "gate": "support_spoofer_suppressed_when_private_predicate_hidden",
            "passed": private_predicate_suppresses_support_spoofer
            and max_hidden_acceptance == 2.0 ** (-predicate_bits),
            "interpretation": "Without the private predicate, support-aware spoofers must guess predicate bits.",
        },
        {
            "gate": "leakage_boundary_explicit",
            "passed": full_predicate_leakage_breaks_private_gate
            and max_one_bit_acceptance > max_hidden_acceptance,
            "interpretation": "If predicate material leaks, the private-predicate protection degrades.",
        },
        {
            "gate": "hardware_or_backend_execution_present",
            "passed": False,
            "interpretation": "No real backend properties or hardware execution are used.",
        },
        {
            "gate": "cryptographic_soundness_proved",
            "passed": False,
            "interpretation": "This is an analytic pressure gate, not a cryptographic proof.",
        },
        {
            "gate": "protocol_soundness_proved",
            "passed": False,
            "interpretation": "The result adds a verifier-private burden but does not prove protocol soundness.",
        },
        {
            "gate": "no_forbidden_claims",
            "passed": True,
            "interpretation": "The report keeps hardware, hardness, soundness, advantage, and BQP claims false.",
        },
    ]
    passed_gate_count = sum(1 for gate in acceptance_gates if gate["passed"])
    failed_gate_count = len(acceptance_gates) - passed_gate_count

    report = {
        "benchmark_id": "B4_B8",
        "problem_ids": [16, 30, 11],
        "title": "B4/B8 verifier-private predicate gate",
        "version": VERSION,
        "last_updated": time.strftime("%Y-%m-%d"),
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "method": METHOD,
        "source_method": SOURCE_METHOD,
        "source_support_spoofer_result": str(source_support_gate),
        "source_support_spoofer_status": support.get("status"),
        "circuit_count": circuit_count,
        "spoofer_count": spoofer_count,
        "attack_row_count": attack_row_count,
        "private_predicate_bit_count": predicate_bits,
        "max_public_support_acceptance_rate": max_support_acceptance,
        "max_hidden_private_predicate_acceptance_rate": max_hidden_acceptance,
        "min_hidden_private_predicate_acceptance_rate": min_hidden_acceptance,
        "max_one_private_bit_leaked_acceptance_rate": max_one_bit_acceptance,
        "max_full_private_predicate_leaked_acceptance_rate": max_full_leak_acceptance,
        "support_only_to_private_predicate_suppression_factor": suppression_factor,
        "private_predicate_suppresses_support_spoofer": private_predicate_suppresses_support_spoofer,
        "full_predicate_leakage_breaks_private_gate": full_predicate_leakage_breaks_private_gate,
        "verifier_private_predicates_added": True,
        "predicate_material_public_to_spoofer": False,
        "hardware_execution_performed": False,
        "real_backend_properties_used": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "sampling_hardness_proved": False,
        "cryptographic_soundness_proved": False,
        "protocol_soundness_proved": False,
        "acceptance_gate_count": len(acceptance_gates),
        "passed_gate_count": passed_gate_count,
        "failed_gate_count": failed_gate_count,
        "acceptance_gates": acceptance_gates,
        "rows": rows,
        "claim_boundary": {
            "what_is_supported": (
                "Adding hidden verifier-private predicate bits turns the support-only acceptance "
                "of the tested spoofers from 1.0 into a 1/16 guessing burden."
            ),
            "what_is_not_supported": (
                "This is not hardware execution, not cryptographic soundness, not protocol "
                "soundness, not sampling hardness, not quantum advantage, and not BQP separation."
            ),
            "next_gate": (
                "Replace analytic private predicates with a formal challenge protocol or real "
                "backend/hardware transcript, then attack leakage and learned spoofers again."
            ),
        },
        "runtime_seconds": round(time.time() - started, 6),
    }
    report["validation_errors"] = validate_report(report)
    report["validation_error_count"] = len(report["validation_errors"])
    return report


def validate_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("status") != STATUS:
        errors.append("status mismatch")
    if report.get("method") != METHOD:
        errors.append("method mismatch")
    if report.get("source_method") != SOURCE_METHOD:
        errors.append("source method mismatch")
    if report.get("circuit_count") != 36:
        errors.append("gate should cover 36 pilot circuits")
    if report.get("spoofer_count") != 4:
        errors.append("gate should cover four spoofer families")
    if report.get("attack_row_count") != 144:
        errors.append("gate should emit 144 predicate attack rows")
    if report.get("private_predicate_bit_count") != 4:
        errors.append("expected four private predicate bits")
    if report.get("max_public_support_acceptance_rate") != 1.0:
        errors.append("source support-only acceptance should be 1.0")
    if report.get("max_hidden_private_predicate_acceptance_rate") != 0.0625:
        errors.append("hidden private predicate acceptance should be 1/16")
    if report.get("support_only_to_private_predicate_suppression_factor") != 16.0:
        errors.append("private predicate should provide a 16x analytic suppression factor")
    if report.get("private_predicate_suppresses_support_spoofer") is not True:
        errors.append("private predicate should suppress support-only spoofers")
    if report.get("full_predicate_leakage_breaks_private_gate") is not True:
        errors.append("full predicate leakage should break the private gate")
    for field in [
        "hardware_execution_performed",
        "real_backend_properties_used",
        "quantum_advantage_claimed",
        "bqp_separation_claimed",
        "sampling_hardness_proved",
        "cryptographic_soundness_proved",
        "protocol_soundness_proved",
    ]:
        if report.get(field) is not False:
            errors.append(f"must keep {field}=False")
    return errors


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# B4/B8 Verifier-Private Predicate Gate v0.1",
        "",
        f"Last updated: {report['last_updated']}",
        "",
        f"Status: **{report['status']}**",
        "",
        "## Summary",
        "",
        f"- Source support-spoofer result: `{report['source_support_spoofer_result']}`",
        f"- Circuits attacked: {report['circuit_count']}",
        f"- Spoofer families: {report['spoofer_count']}",
        f"- Attack rows: {report['attack_row_count']}",
        f"- Private predicate bits: {report['private_predicate_bit_count']}",
        f"- Max public support-only acceptance: {report['max_public_support_acceptance_rate']:.6f}",
        f"- Max hidden private-predicate acceptance: {report['max_hidden_private_predicate_acceptance_rate']:.6f}",
        f"- One private bit leaked acceptance: {report['max_one_private_bit_leaked_acceptance_rate']:.6f}",
        f"- Full private predicate leaked acceptance: {report['max_full_private_predicate_leaked_acceptance_rate']:.6f}",
        f"- Suppression factor: {report['support_only_to_private_predicate_suppression_factor']:.1f}x",
        f"- Acceptance gates passed / failed: {report['passed_gate_count']} / {report['failed_gate_count']}",
        "",
        "## Interpretation",
        "",
        (
            "The previous support-aware attack showed that a verifier checking only public support "
            "membership can be passed with acceptance 1.0. This gate adds four late-bound "
            "verifier-private predicate bits. Under the no-leakage analytic model, the same "
            "support-aware spoofers must guess those bits, reducing acceptance to 1/16."
        ),
        "",
        (
            "The result is intentionally limited. If the private predicate fully leaks, acceptance "
            "returns to 1.0; with one predicate bit leaked, acceptance rises to 1/8. Therefore this "
            "is a verifier-burden gate and leakage boundary, not a soundness proof."
        ),
        "",
        "## Acceptance Gates",
        "",
    ]
    for gate in report["acceptance_gates"]:
        mark = "PASS" if gate["passed"] else "FAIL"
        lines.append(f"- {mark}: `{gate['gate']}` - {gate['interpretation']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Not hardware execution.",
            "- Not cryptographic or protocol soundness.",
            "- Not sampling hardness.",
            "- Not quantum advantage.",
            "- Not BQP separation.",
            "",
            "## Validation",
            "",
            f"- Validation errors: {report['validation_error_count']}",
        ]
    )
    if report["validation_errors"]:
        lines.extend([f"  - {error}" for error in report["validation_errors"]])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-support-gate",
        type=Path,
        default=Path("results/B4_B8_nonstabilizer_support_spoofer_gate_v0.json"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B4_B8_verifier_private_predicate_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B4_B8_verifier_private_predicate_gate.md"),
    )
    parser.add_argument("--predicate-bits", type=int, default=4)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    report = build_gate(args.source_support_gate, args.predicate_bits)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(markdown(report), encoding="utf-8")
    if args.pretty:
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "circuit_count": report["circuit_count"],
                    "spoofer_count": report["spoofer_count"],
                    "max_public_support_acceptance_rate": report[
                        "max_public_support_acceptance_rate"
                    ],
                    "max_hidden_private_predicate_acceptance_rate": report[
                        "max_hidden_private_predicate_acceptance_rate"
                    ],
                    "support_only_to_private_predicate_suppression_factor": report[
                        "support_only_to_private_predicate_suppression_factor"
                    ],
                    "full_predicate_leakage_breaks_private_gate": report[
                        "full_predicate_leakage_breaks_private_gate"
                    ],
                    "validation_error_count": report["validation_error_count"],
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
