"""
agents/aggregator.py
--------------------
Aggregator Node – merges all three agent outputs into one final JSON.
No AI call needed here – pure Python assembly.
"""

from datetime import datetime, timezone
from models import ClaimState


def aggregator_node(state: ClaimState) -> dict:
    """LangGraph node – assembles the final response."""
    print("[Aggregator] Combining results …")

    id_r = state.get("id_result", {})
    dis_r = state.get("discharge_result", {})
    bill_r = state.get("bill_result", {})
    page_c = state.get("page_classifications", {})

    # Build human-readable page → doc_type map
    page_map: dict = {}
    for pn, dt in page_c.items():
        page_map.setdefault(dt, []).append(pn)

    final = {
        "claim_id": state["claim_id"],
        "processed_at": datetime.now(timezone.utc).isoformat(),
        # ── Pipeline metadata ───────────────────────────────────────
        "pipeline": {
            "total_pages": len(state.get("pages", {})),
            "page_classification_map": page_map,
            "agents_triggered": {
                "id_agent": {
                    "pages": state.get("id_pages", []),
                    "status": id_r.get("status", "not_run"),
                },
                "discharge_agent": {
                    "pages": state.get("discharge_pages", []),
                    "status": dis_r.get("status", "not_run"),
                },
                "bill_agent": {
                    "pages": state.get("bill_pages", []),
                    "status": bill_r.get("status", "not_run"),
                },
            },
        },
        "extracted_data": {
            "identity_and_policy": id_r.get("data", {}),
            "discharge_summary": dis_r.get("data", {}),
            "itemized_billing": bill_r.get("data", {}),
        },
        "patient_name": (
            id_r.get("data", {}).get("patient_name")
            or dis_r.get("data", {}).get("patient_name")
            or bill_r.get("data", {}).get("patient_name")
        ),
        "policy_number": id_r.get("data", {}).get("policy_number"),
        "total_claimed_amount": bill_r.get("data", {}).get("total_amount"),
        "admission_date": dis_r.get("data", {}).get("admission_date"),
        "discharge_date": dis_r.get("data", {}).get("discharge_date"),
        "primary_diagnosis": dis_r.get("data", {}).get("admission_diagnosis"),
    }

    print("[Aggregator]  Final result ready.")
    return {"final_result": final}
