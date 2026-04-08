"""
agents/bill_agent.py
--------------------
Itemized Bill Agent – extracts every line item and financial summary
from itemized_bill and cash_receipt pages only.
"""

import json, os
from openai import OpenAI
from models import ClaimState
from utils  import pages_to_text, pages_to_vision_msgs


SYSTEM_PROMPT = """You are a medical billing expert extracting itemised hospital and
pharmacy charges for insurance claim reimbursement.

Extract EVERY line item – do not group or summarise. Use null for missing fields.
Return ONLY valid JSON – no markdown:

{
  "bill_number":          "<string or null>",
  "bill_date":            "<string or null>",
  "patient_name":         "<string or null>",
  "patient_id":           "<string or null>",
  "hospital_name":        "<string or null>",
  "admission_date":       "<string or null>",
  "discharge_date":       "<string or null>",
  "insurance_provider":   "<string or null>",
  "line_items": [
    {
      "date":        "<string>",
      "description": "<string>",
      "quantity":    <number>,
      "unit_rate":   <number>,
      "amount":      <number>
    }
  ],
  "subtotal":              <number or null>,
  "tax_percentage":        <number or null>,
  "tax_amount":            <number or null>,
  "discount_amount":       <number or null>,
  "total_amount":          <number or null>,
  "insurance_payment":     <number or null>,
  "patient_responsibility":<number or null>,
  "payment_method":        "<string or null>",
  "currency":              "USD",
  "calculated_total":      <sum of all line_item amounts as a number>
}

For calculated_total: add up ALL line_item amounts yourself and put the result here."""


def bill_agent_node(state: ClaimState) -> dict:
    """LangGraph node – extracts itemised billing data."""
    bill_pages = state.get("bill_pages", [])

    if not bill_pages:
        print("[Bill Agent] No pages assigned – skipping.")
        return {"bill_result": {"status": "no_pages_assigned", "data": {}}}

    print(f"[Bill Agent] Processing pages: {bill_pages}")
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    pages  = state["pages"]

    content = pages_to_vision_msgs(pages, bill_pages)
    content.append({
        "type": "text",
        "text": (
            f"Pages assigned to you: {bill_pages}\n\n"
            f"Extracted text:\n{pages_to_text(pages, bill_pages)}\n\n"
            "Extract the complete itemised billing information. "
            "Include EVERY single line item with its date, description, qty, rate, and amount."
        ),
    })

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": content},
        ],
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()

    try:
        extracted = json.loads(raw)
    except json.JSONDecodeError:
        print(f"[Bill Agent] Parse error: {raw[:100]}")
        extracted = {"raw": raw}

    total = extracted.get("total_amount", "N/A")
    items = len(extracted.get("line_items", []))
    print(f"[Bill Agent] Done. {items} line items. Total: {total}")
    return {"bill_result": {"status": "success", "pages_processed": bill_pages, "data": extracted}}