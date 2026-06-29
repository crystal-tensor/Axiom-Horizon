#!/usr/bin/env python3
"""Qiskit-loader replay gate for the B1/B7 cone_01 OpenQASM 3 artifact."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import numpy as np
from qiskit import QuantumCircuit, qasm3
from qiskit.quantum_info import Statevector, state_fidelity


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RESEARCH = ROOT / "research"

METHOD = "b1_b7_cone01_openqasm3_qiskit_loader_replay_gate_v0"
STATUS = "cone01_openqasm3_qiskit_loader_replay_passed_default_input_only"
MODEL_STATUS = "qiskit_loader_openqasm3_replay_matches_source_default_input_without_b7_credit"

SOURCE_QASM_PATH = RESULTS / "b1_native_t_resource_optimizer" / "qasmbench_medium_exact" / "gcm_h6.qasm"
PARSER_PATH = RESULTS / "B1_B7_cone01_openqasm3_parser_readiness_gate_v0.json"
LOCAL_REPLAY_PATH = RESULTS / "B1_B7_cone01_openqasm3_local_semantic_replay_gate_v0.json"
WITNESS_PATH = RESULTS / "B1_B7_cone01_openqasm3_patch_witness_packet_gate_v0.json"
QASM3_PATH = (
    RESULTS
    / "B1_B7_cone01_openqasm3_candidate_export_gate"
    / "gcm_h6_line268_line1381_candidate_openqasm3.qasm"
)
OUT_JSON = RESULTS / "B1_B7_cone01_openqasm3_qiskit_loader_replay_gate_v0.json"
OUT_MD = RESEARCH / "B1_B7_cone01_openqasm3_qiskit_loader_replay_gate.md"

FIDELITY_TOLERANCE = 1e-10
AMPLITUDE_TOLERANCE = 1e-10
PROBABILITY_TOLERANCE = 1e-10
MEASURED_QUBIT = 4


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def without_final_measurements(circuit: QuantumCircuit) -> QuantumCircuit:
    return circuit.remove_final_measurements(inplace=False)


def align_global_phase(reference: np.ndarray, candidate: np.ndarray) -> np.ndarray:
    inner = np.vdot(reference, candidate)
    if abs(inner) == 0:
        return candidate
    return candidate * np.conj(inner / abs(inner))


def measured_marginal(statevector: Statevector, qubit: int) -> dict[str, float]:
    probabilities = statevector.probabilities([qubit])
    return {"0": float(probabilities[0]), "1": float(probabilities[1])}


def max_distribution_delta(left: dict[str, float], right: dict[str, float]) -> float:
    return max(abs(left.get(key, 0.0) - right.get(key, 0.0)) for key in set(left) | set(right))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def main() -> None:
    parser_payload = load_json(PARSER_PATH)
    local_replay_payload = load_json(LOCAL_REPLAY_PATH)
    witness_payload = load_json(WITNESS_PATH)
    qasm3_text = read_text(QASM3_PATH)
    source_circuit = QuantumCircuit.from_qasm_file(str(SOURCE_QASM_PATH))

    errors: list[str] = []
    qiskit_circuit: QuantumCircuit | None = None
    loader_error_type = None
    loader_error_message = None
    try:
        qiskit_circuit = qasm3.loads(qasm3_text)
    except Exception as exc:  # pragma: no cover - kept as result evidence.
        loader_error_type = type(exc).__name__
        loader_error_message = str(exc).splitlines()[0][:240]

    require(errors, qiskit_circuit is not None, "qiskit OpenQASM 3 loader failed")
    require(
        errors,
        parser_payload.get("status")
        == "cone01_openqasm3_local_parse_passed_qiskit_loader_dependency_missing",
        "source parser-readiness status changed",
    )
    require(
        errors,
        local_replay_payload.get("status")
        == "cone01_openqasm3_local_semantic_replay_passed_default_input_only",
        "source local semantic replay status changed",
    )
    require(
        errors,
        witness_payload.get("status")
        == "cone01_openqasm3_patch_witness_packet_passed_without_b7_resource_credit",
        "source patch witness status changed",
    )

    expected_counts = {"cx": 789, "rz": 601, "u": 487, "measure": 1}
    qiskit_counts: dict[str, int] | None = None
    qiskit_depth: int | None = None
    qiskit_num_qubits: int | None = None
    qiskit_num_clbits: int | None = None
    fidelity = None
    infidelity = None
    max_amplitude_delta = None
    max_probability_delta = None
    measured_delta = None
    source_marginal = None
    qiskit_marginal = None
    replay_passed = False

    if qiskit_circuit is not None:
        qiskit_counts = {key: int(value) for key, value in qiskit_circuit.count_ops().items()}
        qiskit_depth = int(qiskit_circuit.depth())
        qiskit_num_qubits = int(qiskit_circuit.num_qubits)
        qiskit_num_clbits = int(qiskit_circuit.num_clbits)
        source_state = Statevector.from_instruction(without_final_measurements(source_circuit))
        qiskit_state = Statevector.from_instruction(without_final_measurements(qiskit_circuit))
        source_data = np.asarray(source_state.data)
        qiskit_data = np.asarray(qiskit_state.data)
        aligned_qiskit = align_global_phase(source_data, qiskit_data)
        amplitude_delta = np.abs(source_data - aligned_qiskit)
        probability_delta = np.abs(np.abs(source_data) ** 2 - np.abs(qiskit_data) ** 2)
        fidelity = float(state_fidelity(source_state, qiskit_state))
        infidelity = float(1.0 - fidelity)
        max_amplitude_delta = float(np.max(amplitude_delta))
        max_probability_delta = float(np.max(probability_delta))
        source_marginal = measured_marginal(source_state, MEASURED_QUBIT)
        qiskit_marginal = measured_marginal(qiskit_state, MEASURED_QUBIT)
        measured_delta = max_distribution_delta(source_marginal, qiskit_marginal)
        replay_passed = (
            infidelity <= FIDELITY_TOLERANCE
            and max_amplitude_delta <= AMPLITUDE_TOLERANCE
            and max_probability_delta <= PROBABILITY_TOLERANCE
            and measured_delta <= PROBABILITY_TOLERANCE
        )
        require(errors, qiskit_num_qubits == 19, "qiskit qubit count changed")
        require(errors, qiskit_num_clbits == 1, "qiskit clbit count changed")
        require(errors, qiskit_counts == expected_counts, "qiskit operation counts changed")
        require(errors, qiskit_depth == 1483, "qiskit circuit depth changed")
        require(errors, replay_passed, "qiskit loader default-input replay failed")

    passed = not errors
    summary = {
        "source_parser_readiness_gate": rel(PARSER_PATH),
        "source_local_semantic_replay_gate": rel(LOCAL_REPLAY_PATH),
        "source_patch_witness_packet_gate": rel(WITNESS_PATH),
        "source_qasm_path": rel(SOURCE_QASM_PATH),
        "openqasm3_candidate_path": rel(QASM3_PATH),
        "qiskit_version": package_version("qiskit"),
        "qiskit_qasm3_import_version": package_version("qiskit-qasm3-import"),
        "openqasm3_package_version": package_version("openqasm3"),
        "qiskit_loader_attempted": True,
        "qiskit_loader_passed": qiskit_circuit is not None,
        "qiskit_loader_error_type": loader_error_type,
        "qiskit_loader_error_message": loader_error_message,
        "qiskit_num_qubits": qiskit_num_qubits,
        "qiskit_num_clbits": qiskit_num_clbits,
        "qiskit_count_ops": qiskit_counts,
        "expected_qiskit_count_ops": expected_counts,
        "qiskit_depth": qiskit_depth,
        "measured_qubit": MEASURED_QUBIT,
        "state_fidelity": fidelity,
        "infidelity": infidelity,
        "max_global_phase_aligned_amplitude_delta": max_amplitude_delta,
        "max_probability_delta": max_probability_delta,
        "source_measured_marginal": source_marginal,
        "qiskit_loader_measured_marginal": qiskit_marginal,
        "measured_marginal_max_delta": measured_delta,
        "qiskit_loader_default_input_replay_passed": replay_passed,
        "accepted_qiskit_loader_parse_artifact_count": 1 if qiskit_circuit is not None else 0,
        "accepted_qiskit_loader_replay_artifact_count": 1 if replay_passed else 0,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_symbolic_unitary_equivalence_count": 0,
        "accepted_local_u3_pricing_certificate_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": 30,
        "missing_proxy_t_after_gate": 600,
        "qiskit_loader_parse_claimed": qiskit_circuit is not None,
        "qiskit_loader_replay_claimed": replay_passed,
        "symbolic_unitary_equivalence_claimed": False,
        "arbitrary_input_equivalence_claimed": False,
        "full_hilbert_space_certificate_claimed": False,
        "local_u3_pricing_accepted": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "validation_error_count": len(errors),
    }
    payload = {
        "benchmark_id": "B1",
        "linked_b7_problem_id": 21,
        "method": METHOD,
        "status": STATUS if passed else "cone01_openqasm3_qiskit_loader_replay_failed",
        "model_status": MODEL_STATUS if passed else "qiskit_loader_openqasm3_replay_rejected",
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "claim_boundary": {
            "supported_claim": (
                "The OpenQASM 3 candidate can be loaded by Qiskit's OpenQASM 3 loader "
                "with qiskit-qasm3-import installed, preserves the expected operation "
                "counts, and matches the optimized source on the default-input "
                "statevector after final measurements are removed."
            ),
            "qiskit_loader_parse_claimed": qiskit_circuit is not None,
            "qiskit_loader_replay_claimed": replay_passed,
            "symbolic_unitary_equivalence_claimed": False,
            "arbitrary_input_equivalence_claimed": False,
            "full_hilbert_space_certificate_claimed": False,
            "local_u3_pricing_accepted": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "unsupported_claims": [
                "This is only default-input statevector replay, not arbitrary-input equivalence.",
                "This is not a symbolic exact full-circuit unitary proof.",
                "This does not price or eliminate the remaining line-1381 off-grid local-U3 parameters.",
                "This does not recover the dropped line-1378 overlap delta.",
                "This does not improve the B7 resource ledger.",
            ],
        },
        "summary": summary,
        "validation_errors": errors,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    if errors:
        raise SystemExit("OpenQASM3 Qiskit-loader replay gate failed: " + "; ".join(errors))


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    claims = payload["claim_boundary"]
    return "\n".join(
        [
            "# B1/B7 cone_01 OpenQASM 3 Qiskit-Loader Replay Gate",
            "",
            f"- Method: `{payload['method']}`",
            f"- Status: `{payload['status']}`",
            f"- Model status: `{payload['model_status']}`",
            f"- Workload: `{payload['workload']}`",
            f"- Supported claim: {claims['supported_claim']}",
            "",
            "## Inputs",
            "",
            f"- Parser-readiness gate: `{summary['source_parser_readiness_gate']}`",
            f"- Local semantic replay gate: `{summary['source_local_semantic_replay_gate']}`",
            f"- Patch witness packet gate: `{summary['source_patch_witness_packet_gate']}`",
            f"- OpenQASM 3 candidate: `{summary['openqasm3_candidate_path']}`",
            "",
            "## Loader Evidence",
            "",
            f"- Qiskit / qiskit-qasm3-import / openqasm3 versions: {summary['qiskit_version']} / {summary['qiskit_qasm3_import_version']} / {summary['openqasm3_package_version']}",
            f"- Loader attempted / passed: {summary['qiskit_loader_attempted']} / {summary['qiskit_loader_passed']}",
            f"- Qubits / clbits / depth: {summary['qiskit_num_qubits']} / {summary['qiskit_num_clbits']} / {summary['qiskit_depth']}",
            f"- Operation counts: {summary['qiskit_count_ops']}",
            "",
            "## Replay Evidence",
            "",
            f"- State fidelity / infidelity: {summary['state_fidelity']} / {summary['infidelity']}",
            f"- Max amplitude / probability delta: {summary['max_global_phase_aligned_amplitude_delta']} / {summary['max_probability_delta']}",
            f"- Measured q[{summary['measured_qubit']}] marginal delta: {summary['measured_marginal_max_delta']}",
            f"- Accepted Qiskit-loader parse / replay artifacts: {summary['accepted_qiskit_loader_parse_artifact_count']} / {summary['accepted_qiskit_loader_replay_artifact_count']}",
            f"- Accepted occurrence / proxy-T reduction / B7 claim: {summary['accepted_occurrence_removal']} / {summary['accepted_proxy_t_reduction']} / {summary['b7_ledger_improvement_claimed']}",
            "",
            "## Claim Boundary",
            "",
            *[f"- {claim}" for claim in claims["unsupported_claims"]],
            "",
            "## Validation",
            "",
            f"- Qiskit-loader default-input replay passed: {summary['qiskit_loader_default_input_replay_passed']}",
            f"- Validation errors: {summary['validation_error_count']}",
            "",
        ]
    )


if __name__ == "__main__":
    main()
