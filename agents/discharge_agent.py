"""
Discharge Summary Agent - extracts clinical and hospitalization data
from discharge_summary pages only.
"""

import json,os
from openai import OpenAI
from models import ClaimState
from utils import pages_to_text,pages_to_Vision_msgs


SYSTEM_PROMPT = """You are a clinical data extraction specialist processing hospital
discharge summaries for insurance claims.
 
Extract every available field. Use null for missing. Lists should be arrays.
Return ONLY valid JSON – no markdown:
 
{
  "patient_name":           "<string or null>",
  "mrn":                    "<string or null>",
  "date_of_birth":          "<string or null>",
  "hospital_name":          "<string or null>",
  "admission_date":         "<string or null>",
  "discharge_date":         "<string or null>",
  "length_of_stay_days":    <int or null>,
  "attending_physician":    "<string or null>",
  "admission_diagnosis":    "<string or null>",
  "discharge_diagnosis":    "<string or null>",
  "icd_codes":              ["<string>"],
  "hospital_course_summary":"<string or null>",
  "procedures_performed":   ["<string>"],
  "condition_at_discharge": "<string or null>",
  "discharge_medications":  [
    {"name": "<string>", "dose": "<string>", "frequency": "<string>"}
  ],
  "follow_up_instructions": "<string or null>",
  "diet_instructions":      "<string or null>",
  "activity_restrictions":  "<string or null>",
  "signed_by":              "<string or null>",
  "signed_date":            "<string or null>"
}"""

def discharge_agent_node(state:ClaimState)->dict:
    """LangGraph node - extracts discharge summary data."""
    discharge_pages=state.get("discharge_pages",[])

    if not discharge_pages:
        print("[Discharge Agent] No pages assigned - skipping.")
        return {"discharge_result":{"status":"no_pages_assigned","data":{}}}

    print("processing pages :{discharge_pages}")
    client=OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    pages=state("pages")
    content=pages_to_vision_pages(pages,discharage_pages)
    content.append({
        "type": "text",
        "text": (
            f"Pages assigned to you: {discharge_pages}\n\n"
            f"Extracted text:\n{pages_to_text(pages, discharge_pages)}\n\n"
            "Extract all discharge summary and clinical information."
        ),
    })

    response=client.chat.completions.create(
        model='gpt-4o',
        max_tokens=2000,
        messages=[
            {"role":"system","content":SYSTEM_PROMPT},
            {"role":"user","content":content}
        ]
    )
    
    raw=response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()

    try:
        extracted=json.loads(raw)
    except json.JSONDecodeError:
        print("[Discharge Agent] parse error: {raw[:100]}")
        extracted={"raw":raw}

    print(f"[Discharge Agent] Done. Diagnosis: {extracted.get('admission_diagnosis')}")
    return {"discharge_result": {"status": "success", "pages_processed": discharge_pages, "data": extracted}}