import json, os
from openai import OpenAI
from models import ClaimState
from utils import pages_to_text, pages_to_vision_msgs


SYSTEM_PROMPT = """You are a medical document specialist extracting patient identity
and insurance policy data for claim processing.

Extract every available field from the provided pages. Use null for missing fields.
Return ONLY valid JSON – no markdown, no explanation:

{
  "patient_name":       "<string or null>",
  "date_of_birth":      "<string or null>",
  "gender":             "<string or null>",
  "blood_group":        "<string or null>",
  "government_id_type": "<string or null>",
  "government_id_number":"<string or null>",
  "address":            "<string or null>",
  "contact_number":     "<string or null>",
  "email":              "<string or null>",
  "patient_id":         "<string or null>",
  "mrn":                "<string or null>",
  "policy_number":      "<string or null>",
  "group_number":       "<string or null>",
  "insurance_provider": "<string or null>",
  "policy_status":      "<string or null>",
  "subscriber_name":    "<string or null>",
  "relationship":       "<string or null>"
}"""


def id_agent_node(state: ClaimState) -> dict:
    """LangGraph node – extracts identity information."""
    id_pages = state.get("id_pages", [])

    if not id_pages:
        print("[ID Agent] No pages assigned – skipping.")
        return {"id_result": {"status": "no_pages_assigned", "data": {}}}

    print(f"[ID Agent] Processing pages: {id_pages}")
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    pages = state["pages"]

    content = pages_to_vision_msgs(pages, id_pages)
    content.append(
        {
            "type": "text",
            "text": (
                f"Pages assigned to you: {id_pages}\n\n"
                f"Extracted text:\n{pages_to_text(pages, id_pages)}\n\n"
                "Extract all patient identity and insurance policy information."
            ),
        }
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()

    try:
        extracted = json.loads(raw)
    except json.JSONDecodeError:
        print(f"[ID Agent] Parse error: {raw[:100]}")
        extracted = {"raw": raw}

    print(
        f"[ID Agent] Done. Fields extracted: {[k for k, v in extracted.items() if v]}"
    )
    return {
        "id_result": {
            "status": "success",
            "pages_processed": id_pages,
            "data": extracted,
        }
    }
