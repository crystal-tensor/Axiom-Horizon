#!/usr/bin/env python3
"""Build row-level DFT/B5 observable intake templates for B6."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b6_observable_row_intake_template_gate_v0"
STATUS = "observable_row_intake_template_open_missing_dft_b5_rows"
MODEL_STATUS = "top_post_materials_mapped_to_observable_row_templates_no_rows_submitted"
VERSION = "0.1"
EXPECTED_FAILED_IDS = ["T6", "T7"]
EXPECTED_SOURCE_HASH = "ce134d0a5d295af982b77be0a8a43e90ea19e828af20cc80ac3f20b7664d2fdc"
EXPECTED_FORMULA_HASH = "e23239648dd11aa8e0db8ecdeb5824506a5a379c9ba2777965c3aafa5d5d8230"
EXPECTED_REPLAY_HASH = "c44099194d0bc04d74cd3c4c4e068bf51a9e114d11c6e0b5e3890786cda5b8de"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2 if pretty else None, sort_keys=True)
    path.write_text(text + "\n", encoding="utf-8")


def stable_hash(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def requirement(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def find_packet(contract: dict[str, Any], packet_id: str) -> dict[str, Any]:
    for packet in contract["observable_packets"]:
        if packet["packet_id"] == packet_id:
            return packet
    raise KeyError(packet_id)


def build_row_templates(
    top_post_rows: list[dict[str, Any]], dft_keys: list[str], b5_keys: list[str]
) -> list[dict[str, Any]]:
    templates = []
    for row in top_post_rows:
        prefilled = {
            "material_id": row["material_id"],
            "formula": row["formula"],
            "family": row["family"],
            "rank": row["rank"],
            "tc_k": row["tc_k"],
            "pressure_gpa": row["pressure_gpa"],
            "physics_risk_adjusted_v0": row["physics_risk_adjusted_v0"],
            "is_negative_control": row["is_negative_control"],
        }
        dft_missing = [key for key in dft_keys if key != "material_id"]
        b5_missing = [key for key in b5_keys if key != "material_id"]
        template = {
            "material_id": row["material_id"],
            "rank": row["rank"],
            "family": row["family"],
            "formula": row["formula"],
            "is_negative_control": row["is_negative_control"],
            "prefilled_values": prefilled,
            "dft_required_keys": dft_keys,
            "b5_required_keys": b5_keys,
            "dft_missing_keys": dft_missing,
            "b5_missing_keys": b5_missing,
            "submitted_dft_row_present": False,
            "submitted_b5_row_present": False,
            "accepted_dft_row": False,
            "accepted_b5_row": False,
        }
        template["template_hash"] = stable_hash(
            {
                "material_id": row["material_id"],
                "rank": row["rank"],
                "dft_required_keys": dft_keys,
                "b5_required_keys": b5_keys,
                "source_table_hash": EXPECTED_SOURCE_HASH,
                "replay_table_hash": EXPECTED_REPLAY_HASH,
            }
        )
        templates.append(template)
    return templates


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    contract = load_json(args.observable_contract)
    replay = load_json(args.backend_replay)

    dft_packet = find_packet(contract, "B6-O1-dft-row-schema")
    b5_packet = find_packet(contract, "B6-O2-b5-row-schema")
    dft_keys = dft_packet["required_keys"]
    b5_keys = b5_packet["required_keys"]
    top_post_rows = replay["top_post_rows"]
    templates = build_row_templates(top_post_rows, dft_keys, b5_keys)

    submitted_dft_rows = sum(row["submitted_dft_row_present"] for row in templates)
    submitted_b5_rows = sum(row["submitted_b5_row_present"] for row in templates)
    accepted_dft_rows = sum(row["accepted_dft_row"] for row in templates)
    accepted_b5_rows = sum(row["accepted_b5_row"] for row in templates)
    template_table_hash = stable_hash(templates)

    requirements = [
        requirement(
            "T1",
            "Observable contract is open only on O5/O6",
            contract.get("method") == "b6_observable_contract_gate_v0"
            and contract.get("failed_observable_contract_requirement_ids") == ["O5", "O6"],
            {
                "source_method": contract.get("method"),
                "source_status": contract.get("status"),
                "failed_observable_contract_requirement_ids": contract.get(
                    "failed_observable_contract_requirement_ids"
                ),
            },
        ),
        requirement(
            "T2",
            "Backend replay source is stable and still missing observables",
            replay.get("method") == "b6_backend_replay_scout_v0"
            and replay.get("failed_backend_replay_requirement_ids") == ["R7", "R8"]
            and replay.get("dft_observable_rows") == 0
            and replay.get("b5_computed_observable_rows") == 0,
            {
                "source_method": replay.get("method"),
                "source_status": replay.get("status"),
                "failed_backend_replay_requirement_ids": replay.get(
                    "failed_backend_replay_requirement_ids"
                ),
                "dft_observable_rows": replay.get("dft_observable_rows"),
                "b5_computed_observable_rows": replay.get("b5_computed_observable_rows"),
            },
        ),
        requirement(
            "T3",
            "Twelve top-post replay materials are converted into row templates",
            len(templates) == 12
            and [row["rank"] for row in templates] == list(range(1, 13)),
            {
                "template_row_count": len(templates),
                "template_material_ids": [row["material_id"] for row in templates],
            },
        ),
        requirement(
            "T4",
            "DFT and B5 observable schemas are preserved",
            len(dft_keys) == 11
            and len(b5_keys) == 11
            and stable_hash(dft_keys) == contract["dft_schema_hash"]
            and stable_hash(b5_keys) == contract["b5_schema_hash"],
            {
                "required_dft_key_count": len(dft_keys),
                "required_b5_key_count": len(b5_keys),
                "dft_schema_hash": stable_hash(dft_keys),
                "b5_schema_hash": stable_hash(b5_keys),
            },
        ),
        requirement(
            "T5",
            "Source, formula, and replay hashes are preserved",
            replay.get("source_table_hash") == EXPECTED_SOURCE_HASH
            and replay.get("replay_formula_hash") == EXPECTED_FORMULA_HASH
            and replay.get("replay_table_hash") == EXPECTED_REPLAY_HASH,
            {
                "source_table_hash": replay.get("source_table_hash"),
                "replay_formula_hash": replay.get("replay_formula_hash"),
                "replay_table_hash": replay.get("replay_table_hash"),
                "template_table_hash": template_table_hash,
            },
        ),
        requirement(
            "T6",
            "Submitted DFT observable rows exist",
            submitted_dft_rows > 0,
            {"submitted_dft_rows": submitted_dft_rows, "required_material_rows": len(templates)},
        ),
        requirement(
            "T7",
            "Submitted B5-computed observable rows exist",
            submitted_b5_rows > 0,
            {"submitted_b5_rows": submitted_b5_rows, "required_material_rows": len(templates)},
        ),
        requirement(
            "T8",
            "Forbidden discovery, mechanism, and solution claims remain false",
            all(
                contract["claims"].get(key) is False
                for key in [
                    "dft_observable_claimed",
                    "b5_computed_observable_claimed",
                    "material_discovery_claimed",
                    "mechanism_solved",
                    "solution_claimed",
                ]
            ),
            {
                "dft_observable_claimed": contract["claims"].get("dft_observable_claimed"),
                "b5_computed_observable_claimed": contract["claims"].get(
                    "b5_computed_observable_claimed"
                ),
                "material_discovery_claimed": contract["claims"].get(
                    "material_discovery_claimed"
                ),
                "mechanism_solved": contract["claims"].get("mechanism_solved"),
                "solution_claimed": contract["claims"].get("solution_claimed"),
            },
        ),
    ]
    passed = sum(row["passed"] for row in requirements)
    failed_ids = [row["requirement_id"] for row in requirements if not row["passed"]]
    validation_errors: list[str] = []
    if failed_ids != EXPECTED_FAILED_IDS:
        validation_errors.append(f"unexpected observable row intake failures: {failed_ids}")
    if submitted_dft_rows != 0 or submitted_b5_rows != 0:
        validation_errors.append("intake template must not fabricate DFT or B5 rows")
    if accepted_dft_rows != 0 or accepted_b5_rows != 0:
        validation_errors.append("intake template must not accept observable rows")

    summary = {
        "source_observable_contract_status": contract.get("status"),
        "source_backend_replay_status": replay.get("status"),
        "intake_requirement_count": len(requirements),
        "intake_requirements_passed": passed,
        "intake_requirements_failed": len(requirements) - passed,
        "failed_intake_requirement_ids": failed_ids,
        "failed_observable_contract_requirement_ids": contract.get(
            "failed_observable_contract_requirement_ids"
        ),
        "failed_backend_replay_requirement_ids": replay.get(
            "failed_backend_replay_requirement_ids"
        ),
        "template_row_count": len(templates),
        "template_table_hash": template_table_hash,
        "required_dft_key_count": len(dft_keys),
        "required_b5_key_count": len(b5_keys),
        "dft_schema_hash": stable_hash(dft_keys),
        "b5_schema_hash": stable_hash(b5_keys),
        "source_table_hash": replay.get("source_table_hash"),
        "replay_formula_hash": replay.get("replay_formula_hash"),
        "replay_table_hash": replay.get("replay_table_hash"),
        "post_split_record_count": replay.get("post_split_record_count"),
        "top_k": replay.get("top_k"),
        "submitted_dft_rows": submitted_dft_rows,
        "submitted_b5_rows": submitted_b5_rows,
        "accepted_dft_rows": accepted_dft_rows,
        "accepted_b5_rows": accepted_b5_rows,
        "observable_row_intake_ready": False,
        "dft_observable_claimed": False,
        "b5_computed_observable_claimed": False,
        "material_discovery_claimed": False,
        "mechanism_solved": False,
        "solution_claimed": False,
        "validation_error_count": len(validation_errors),
    }

    return {
        "benchmark_id": "B6",
        "linked_benchmark_id": "B5",
        "problem_id": 38,
        "title": "B6/B5 Observable Row Intake Template Gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_observable_contract_result": str(args.observable_contract),
        "source_backend_replay_result": str(args.backend_replay),
        "summary": summary,
        "requirements": requirements,
        "dft_required_keys": dft_keys,
        "b5_required_keys": b5_keys,
        "row_templates": templates,
        "claim_boundary": {
            "what_is_supported": (
                "The top-post B6 replay materials are converted into row-level DFT and "
                "B5 observable intake templates with preserved replay hashes."
            ),
            "what_is_not_supported": (
                "No DFT rows, B5 computed-observable rows, material discovery, mechanism "
                "solution, or B6 solution claim is established."
            ),
            "next_gate": (
                "Submit DFT and B5 observable rows for the templated material_id set while "
                "preserving source_table_hash, replay_formula_hash, and replay_table_hash."
            ),
            "dft_observable_claimed": False,
            "b5_computed_observable_claimed": False,
            "material_discovery_claimed": False,
            "mechanism_solved": False,
            "solution_claimed": False,
        },
        "validation_errors": validation_errors,
        "runtime_seconds": time.time() - started,
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# B6/B5 Observable Row Intake Template Gate",
        "",
        f"Status: **{payload['status']}**",
        "",
        "## Summary",
        "",
        f"- Method: `{payload['method']}`",
        f"- Model status: `{payload['model_status']}`",
        f"- Intake requirements passed/failed: {summary['intake_requirements_passed']} / {summary['intake_requirements_failed']}",
        f"- Failed intake requirement IDs: {summary['failed_intake_requirement_ids']}",
        f"- Template rows: {summary['template_row_count']}",
        f"- DFT/B5 required key counts: {summary['required_dft_key_count']} / {summary['required_b5_key_count']}",
        f"- Template table hash: `{summary['template_table_hash']}`",
        f"- Submitted DFT/B5 rows: {summary['submitted_dft_rows']} / {summary['submitted_b5_rows']}",
        f"- Accepted DFT/B5 rows: {summary['accepted_dft_rows']} / {summary['accepted_b5_rows']}",
        "",
        "## Row Templates",
        "",
        "| Rank | Material | Family | DFT submitted | B5 submitted | Template hash |",
        "|---:|---|---|---|---|---|",
    ]
    for row in payload["row_templates"]:
        lines.append(
            f"| {row['rank']} | {row['material_id']} | {row['family']} | "
            f"{row['submitted_dft_row_present']} | {row['submitted_b5_row_present']} | "
            f"`{row['template_hash']}` |"
        )
    lines.extend(["", "## Requirement Results", ""])
    for row in payload["requirements"]:
        status = "PASS" if row["passed"] else "FAIL"
        lines.append(f"- {row['requirement_id']} [{status}]: {row['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            f"- material_discovery_claimed: {payload['claim_boundary']['material_discovery_claimed']}",
            f"- mechanism_solved: {payload['claim_boundary']['mechanism_solved']}",
            f"- solution_claimed: {payload['claim_boundary']['solution_claimed']}",
            "",
            "## Validation",
            "",
            f"- validation_error_count: {summary['validation_error_count']}",
        ]
    )
    if payload["validation_errors"]:
        for error in payload["validation_errors"]:
            lines.append(f"- {error}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--observable-contract",
        type=Path,
        default=Path("results/B6_observable_contract_gate_v0.json"),
    )
    parser.add_argument(
        "--backend-replay",
        type=Path,
        default=Path("results/B6_backend_replay_scout_v0.json"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B6_B5_observable_row_intake_template_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B6_B5_observable_row_intake_template_gate.md"),
    )
    parser.add_argument("--last-updated", default="2026-07-01")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    write_json(args.json_output, payload, pretty=args.pretty)
    write_markdown(payload, args.markdown_output)
    print(json.dumps(payload["summary"], indent=2 if args.pretty else None, sort_keys=True))
    if payload["validation_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
