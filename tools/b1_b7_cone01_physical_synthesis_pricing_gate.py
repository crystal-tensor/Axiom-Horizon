#!/usr/bin/env python3
"""T-B1-004cs/T-B7-011 physical synthesis pricing gate for line 1381.

T-B1-004cr closed the current shortcut stack for B7 credit and left honest
line-1381 local-U3 pricing as one of the next non-shortcut routes. This gate
turns that route into a conservative physical synthesis pricing check.

It does not synthesize a new circuit. It asks whether the existing line-1381
patch can be counted as a B7 resource improvement after replacing the earlier
20-proxy-T placeholder with a precision-aware Clifford+T-style estimate for the
five off-grid local-U3 parameters. The result is still negative.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from b1_b7_cone01_carrier_absorption_inventory_gate import (
    PROXY_T_PER_OCCURRENCE,
    display_path,
    load_json,
    write_json,
    write_text,
)


ROOT = Path(__file__).resolve().parents[1]
ROUTE_TRIAGE_PATH = ROOT / "results" / "B1_B7_cone01_route_triage_decision_gate_v0.json"
LOCAL_U3_PRICING_PATH = ROOT / "results" / "B1_B7_cone01_line1381_local_u3_pricing_gate_v0.json"
LINE1381_LEAVE_FIVE_PATH = ROOT / "results" / "B1_B7_cone01_line1381_leave_five_out_parameter_gate_v0.json"
JSON_OUT = ROOT / "results" / "B1_B7_cone01_physical_synthesis_pricing_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_physical_synthesis_pricing_gate.md"

METHOD = "b1_b7_cone01_physical_synthesis_pricing_gate_v0"
STATUS = "cone01_physical_synthesis_pricing_rejects_line1381_b7_credit"
MODEL_STATUS = "precision_aware_synthesis_cost_exceeds_selected_cnot_delta_credit"


def t_count_bound(error_tolerance: float) -> int:
    """A conservative deterministic single-rotation T-count proxy.

    This is not a theorem used for publication. It is a project-local guardrail:
    if the line-1381 route cannot survive this generous pricing, it cannot be
    promoted into a B7 ledger improvement.
    """

    return math.ceil(3.0 * math.log2(1.0 / error_tolerance) + 10.0)


def build_payload() -> dict[str, Any]:
    route_triage = load_json(ROUTE_TRIAGE_PATH)
    pricing = load_json(LOCAL_U3_PRICING_PATH)
    leave_five = load_json(LINE1381_LEAVE_FIVE_PATH)
    pricing_summary = pricing["summary"]
    leave_five_summary = leave_five["summary"]

    off_grid_parameter_count = int(
        pricing_summary["line1381_replacement_off_pi_over_four_parameter_count"]
    )
    selected_cnot_delta = int(pricing_summary["selected_candidate_cnot_reduction"])
    placeholder_proxy_t_pressure = int(pricing_summary["line1381_unpriced_proxy_t_pressure"])
    selected_proxy_credit = selected_cnot_delta * PROXY_T_PER_OCCURRENCE

    aggregate_synthesis_error_budget = 1.0e-8
    per_parameter_error_budget = aggregate_synthesis_error_budget / off_grid_parameter_count
    single_parameter_t_bound = t_count_bound(per_parameter_error_budget)
    total_synthesis_t_bound = off_grid_parameter_count * single_parameter_t_bound
    physical_synthesis_cost_minus_selected_credit = total_synthesis_t_bound - selected_proxy_credit

    accepted = physical_synthesis_cost_minus_selected_credit <= 0
    gate_results = {
        "G1_route_triage_requested_honest_pricing": (
            "honest_line1381_local_u3_pricing_with_physical_synthesis_model"
            in route_triage["recommended_next_routes"]
        ),
        "G2_line1381_has_five_off_grid_parameters": off_grid_parameter_count == 5,
        "G3_all_grid_cleanup_still_fails": leave_five_summary["leave_five_out_exact_pass_count"] == 0,
        "G4_physical_synthesis_cost_is_computed": total_synthesis_t_bound > 0,
        "G5_physical_cost_exceeds_selected_cnot_credit": (
            physical_synthesis_cost_minus_selected_credit > 0
        ),
        "G6_no_b7_credit_claimed": not accepted,
    }
    validation_errors = [
        name for name, passed in gate_results.items() if not passed
    ]

    summary = {
        "source_route_triage_method": route_triage["method"],
        "source_local_u3_pricing_method": pricing["method"],
        "source_line1381_leave_five_out_method": leave_five["method"],
        "selected_line_numbers": pricing_summary["selected_line_numbers"],
        "dropped_overlap_candidate_line_numbers": pricing_summary[
            "dropped_overlap_candidate_line_numbers"
        ],
        "line1381_off_grid_parameter_count": off_grid_parameter_count,
        "placeholder_proxy_t_per_parameter": PROXY_T_PER_OCCURRENCE,
        "placeholder_proxy_t_pressure": placeholder_proxy_t_pressure,
        "selected_candidate_cnot_reduction": selected_cnot_delta,
        "selected_cnot_delta_proxy_credit": selected_proxy_credit,
        "aggregate_synthesis_error_budget": aggregate_synthesis_error_budget,
        "per_parameter_error_budget": per_parameter_error_budget,
        "single_parameter_t_count_bound": single_parameter_t_bound,
        "total_physical_synthesis_t_count_bound": total_synthesis_t_bound,
        "physical_synthesis_cost_minus_selected_cnot_credit": (
            physical_synthesis_cost_minus_selected_credit
        ),
        "physical_synthesis_pricing_accepted": accepted,
        "line1381_all_grid_exact_pass_count": leave_five_summary[
            "leave_five_out_exact_pass_count"
        ],
        "line1381_parameters_eliminated": False,
        "line1381_parameters_absorbed": False,
        "line1381_parameters_symbolically_decomposed": False,
        "line1378_delta_recovered": False,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "gate_count": len(gate_results),
        "passed_gate_count": sum(1 for passed in gate_results.values() if passed),
        "failed_gate_count": sum(1 for passed in gate_results.values() if not passed),
        "validation_error_count": len(validation_errors),
    }
    return {
        "benchmark_id": "B1",
        "linked_b7_problem_id": "B7",
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "source_route_triage_result": display_path(ROUTE_TRIAGE_PATH),
        "source_local_u3_pricing_result": display_path(LOCAL_U3_PRICING_PATH),
        "source_line1381_leave_five_out_result": display_path(LINE1381_LEAVE_FIVE_PATH),
        "summary": summary,
        "gate_results": gate_results,
        "validation_errors": validation_errors,
        "claim_boundary": {
            "supported_claim": (
                "Under a conservative precision-aware physical synthesis pricing "
                "guardrail, the five line-1381 off-grid local-U3 parameters cost "
                f"{total_synthesis_t_bound} T-count proxy units, exceeding the "
                f"{selected_proxy_credit} proxy credit from the selected 6-CNOT delta."
            ),
            "unsupported_claims": [
                "This is not a realized Clifford+T synthesis circuit.",
                "This does not prove a global lower bound for line 1381.",
                "This does not recover line 1378.",
                "This does not accept occurrence removal, proxy-T reduction, or B7 ledger improvement.",
            ],
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "physical_synthesis_pricing_accepted": accepted,
        },
    }


def markdown_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 cone_01 Physical Synthesis Pricing Gate",
        "",
        "- Gate: T-B1-004cs / T-B7-011",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Model status: `{payload['model_status']}`",
        f"- Workload: `{payload['workload']}`",
        "",
        "## Inputs",
        "",
        f"- Route triage: `{payload['source_route_triage_result']}`",
        f"- Local-U3 pricing boundary: `{payload['source_local_u3_pricing_result']}`",
        f"- All-grid endpoint pressure: `{payload['source_line1381_leave_five_out_result']}`",
        "",
        "## Result",
        "",
        f"- Line-1381 off-grid local-U3 parameters: `{summary['line1381_off_grid_parameter_count']}`",
        f"- Aggregate synthesis error budget: `{summary['aggregate_synthesis_error_budget']}`",
        f"- Per-parameter error budget: `{summary['per_parameter_error_budget']}`",
        f"- Single-parameter T-count bound: `{summary['single_parameter_t_count_bound']}`",
        f"- Total physical synthesis T-count bound: `{summary['total_physical_synthesis_t_count_bound']}`",
        f"- Selected 6-CNOT delta proxy credit: `{summary['selected_cnot_delta_proxy_credit']}`",
        f"- Cost minus credit: `{summary['physical_synthesis_cost_minus_selected_cnot_credit']}`",
        f"- Physical synthesis pricing accepted: `{summary['physical_synthesis_pricing_accepted']}`",
        f"- Accepted occurrence / proxy-T reduction: `{summary['accepted_occurrence_removal']}` / `{summary['accepted_proxy_t_reduction']}`",
        "",
        "## Claim Boundary",
        "",
        "- This is a conservative pricing guardrail, not a synthesized replacement circuit.",
        "- It rejects B7 credit for the current line-1381 route under the physical synthesis pricing model.",
        "- It leaves full-circuit symbolic equivalence, line-1378 recovery, and alternate scaffolds open.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", default=str(JSON_OUT))
    parser.add_argument("--markdown-output", default=str(MD_OUT))
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    payload = build_payload()
    write_json(Path(args.json_output), payload, args.pretty)
    write_text(Path(args.markdown_output), markdown_report(payload))
    print(
        json.dumps(
            {
                "status": payload["status"],
                "physical_synthesis_pricing_accepted": payload["summary"][
                    "physical_synthesis_pricing_accepted"
                ],
                "total_physical_synthesis_t_count_bound": payload["summary"][
                    "total_physical_synthesis_t_count_bound"
                ],
                "selected_cnot_delta_proxy_credit": payload["summary"][
                    "selected_cnot_delta_proxy_credit"
                ],
                "validation_error_count": payload["summary"]["validation_error_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
