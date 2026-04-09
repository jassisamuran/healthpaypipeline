# Claim Processing Pipeline

A **FastAPI + LangGraph** multi-agent AI service that processes PDF insurance claims. It uses OpenAI GPT-4o vision to classify every page of a PDF into document types, routes pages to specialist extraction agents, and returns a single structured JSON with all extracted data.

---

## Live Demo

- **Live URL:** `https://healthpaypipeline.onrender.com/`
- **Swagger Docs:** `https://healthpaypipeline.onrender.com/docs`

---

## Architecture & Workflow

```
START
  │
  ▼
┌─────────────────────────────────────────┐
│           SEGREGATOR AGENT              │
│  - Opens PDF with PyMuPDF               │
│  - Extracts text + renders page as PNG  │
│  - Sends each page to GPT-4o vision     │
│  - Classifies into 1 of 9 doc types     │
│  - Routes page numbers to 3 agents      │
└─────────────────────────────────────────┘
  │
  ├──── id_pages [3, 1] ────────────────────────────┐
  ├──── discharge_pages [4] ──────────────────────┐ │
  └──── bill_pages [7, 9, 10] ──────────────────┐ │ │
                                                 │ │ │
  ┌──────────────────────────────────────────────┘ │ │
  ▼                                                │ │
┌──────────────────┐                              │ │
│   BILL AGENT     │                              │ │
│ pages: [7,9,10]  │                              │ │
│ Extracts:        │                              │ │
│ - Every line item│                              │ │
│ - Qty, rate,     │                              │ │
│   amount         │                              │ │
│ - Subtotal, tax  │                              │ │
│ - Insurance pay  │                              │ │
│ - Patient share  │                              │ │
└──────────────────┘                              │ │
  │                                               │ │
  │  ┌────────────────────────────────────────────┘ │
  │  ▼                                              │
  │ ┌──────────────────────┐                        │
  │ │  DISCHARGE AGENT     │                        │
  │ │  pages: [4]          │                        │
  │ │  Extracts:           │                        │
  │ │  - Admission date    │                        │
  │ │  - Discharge date    │                        │
  │ │  - Diagnosis + ICD   │                        │
  │ │  - Physician name    │                        │
  │ │  - Medications       │                        │
  │ │  - Follow-up instrs  │                        │
  │ └──────────────────────┘                        │
  │   │                                             │
  │   │  ┌──────────────────────────────────────────┘
  │   │  ▼
  │   │ ┌──────────────────────┐
  │   │ │      ID AGENT        │
  │   │ │  pages: [1, 3]       │
  │   │ │  Extracts:           │
  │   │ │  - Patient name      │
  │   │ │  - Date of birth     │
  │   │ │  - Gov't ID number   │
  │   │ │  - Policy number     │
  │   │ │  - Insurance provider│
  │   │ │  - Contact, email    │
  │   │ └──────────────────────┘
  │   │   │
  └───┴───┘
        │
        ▼
┌─────────────────────────────────────────┐
│            AGGREGATOR NODE              │
│  - Pure Python, no AI call              │
│  - Merges id_result + discharge_result  │
│    + bill_result                        │
│  - Adds pipeline metadata               │
│  - Returns final JSON                   │
└─────────────────────────────────────────┘
  │
  ▼
END → JSON Response
```

---

## The 9 Document Types (Segregator)

| Type | Description | Sample PDF Pages |
|------|-------------|-----------------|
| `claim_forms` | Medical / insurance claim forms | 1, 8 |
| `cheque_or_bank_details` | Cheques, bank account info | 2 |
| `identity_document` | Gov't ID, passport, Aadhaar | 3 |
| `itemized_bill` | Hospital / pharmacy itemised bills | 9, 10 |
| `discharge_summary` | Hospital discharge summaries | 4 |
| `prescription` | Doctor Rx / prescriptions | 5 |
| `investigation_report` | Lab reports, CBC, radiology | 6, 11, 12 |
| `cash_receipt` | Cash payment receipts | 7 |
| `other` | Consent forms, referral letters | 13-18 |

---

## Project Structure

```
claim_pipeline/
├── main.py                    ← FastAPI app — POST /api/process
├── graph.py                   ← LangGraph StateGraph (5 nodes wired together)
├── models.py                  ← ClaimState TypedDict + DocumentType enum
├── utils.py                   ← PDF helpers using PyMuPDF
├── agents/
│   ├── __init__.py
│   ├── segregator.py          ← AI page classifier (GPT-4o vision)
│   ├── id_agent.py            ← Extracts identity & policy data
│   ├── discharge_agent.py     ← Extracts clinical / discharge data
│   ├── bill_agent.py          ← Extracts itemised billing data
│   └── aggregator.py          ← Merges all results, pure Python
├── test_api.py                ← Test script
├── requirements.txt
├── .env.example
└── README.md
```

---

## Tech Stack

| Technology | Purpose |
|---|---|
| **FastAPI** | REST API framework with auto Swagger docs |
| **LangGraph** | Multi-agent workflow orchestration via StateGraph |
| **OpenAI GPT-4o** | Vision + text LLM for classification and extraction |
| **PyMuPDF** | PDF text extraction and page image rendering |
| **Pydantic** | Data validation |
| **python-dotenv** | Environment variable management |

---

## Setup & Run Locally

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/claim-pipeline.git
cd claim-pipeline
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set your OpenAI API key
```bash
cp .env.example .env
# Edit .env and add your key:
# OPENAI_API_KEY=sk-proj-your-key-here
```

### 5. Start the server
```bash
python main.py
```

Server runs at **http://localhost:8000**

---

## API Usage

### Endpoint

```
POST /api/process
Content-Type: multipart/form-data
```

### Parameters

| Field | Type | Description |
|-------|------|-------------|
| `claim_id` | string (Form) | Unique claim identifier |
| `file` | PDF (File) | The claim document PDF |

### cURL Example

```bash
curl -X POST http://localhost:8000/api/process \
  -F "claim_id=CLM-2024-789456" \
  -F "file=@final_image_protected.pdf"
```

### Python Example

```python
import requests

with open("final_image_protected.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/process",
        data={"claim_id": "CLM-2024-789456"},
        files={"file": ("claim.pdf", f, "application/pdf")},
    )

print(response.json())
```

### Sample Response

```json
{
  "claim_id": "CLM-2024-789456",
  "processed_at": "2025-04-08T10:30:00+00:00",
  "patient_name": "John Michael Smith",
  "policy_number": "POL-987654321",
  "total_claimed_amount": 6418.65,
  "admission_date": "January 20, 2025",
  "discharge_date": "January 25, 2025",
  "primary_diagnosis": "Community Acquired Pneumonia (CAP)",
  "pipeline": {
    "total_pages": 18,
    "page_classification_map": {
      "claim_forms": [1],
      "cheque_or_bank_details": [2],
      "identity_document": [3],
      "discharge_summary": [4],
      "prescription": [5],
      "investigation_report": [6, 11, 12],
      "cash_receipt": [7],
      "other": [8, 13, 14, 15, 16, 17, 18],
      "itemized_bill": [9, 10]
    },
    "agents_triggered": {
      "id_agent": {
        "pages": [1, 3],
        "status": "success"
      },
      "discharge_agent": {
        "pages": [4],
        "status": "success"
      },
      "bill_agent": {
        "pages": [7, 9, 10],
        "status": "success"
      }
    }
  },
  "extracted_data": {
    "identity_and_policy": {
      "patient_name": "John Michael Smith",
      "date_of_birth": "March 15, 1985",
      "government_id_type": "Government ID Card",
      "government_id_number": "ID-987-654-321",
      "policy_number": "POL-987654321",
      "insurance_provider": "HealthCare Insurance Company",
      "contact_number": "+1-555-0123",
      "email": "john.smith@email.com"
    },
    "discharge_summary": {
      "admission_date": "January 20, 2025",
      "discharge_date": "January 25, 2025",
      "length_of_stay_days": 5,
      "attending_physician": "Dr. Sarah Johnson, MD",
      "admission_diagnosis": "Community Acquired Pneumonia (CAP)",
      "condition_at_discharge": "Stable, improved",
      "discharge_medications": [
        {"name": "Amoxicillin", "dose": "500mg", "frequency": "TID x 7 days"},
        {"name": "Acetaminophen", "dose": "500mg", "frequency": "PRN for pain"}
      ]
    },
    "itemized_billing": {
      "bill_number": "BILL-2025-789456",
      "total_amount": 6418.65,
      "subtotal": 6113.00,
      "tax_amount": 305.65,
      "insurance_payment": 5134.92,
      "patient_responsibility": 1283.73,
      "line_items": [
        {
          "date": "01/20/25",
          "description": "Room Charges - Semi-Private (5 days)",
          "quantity": 5,
          "unit_rate": 200.00,
          "amount": 1000.00
        }
      ]
    }
  }
}
```

---

## Testing

### Option A — Swagger UI (easiest)
Open http://localhost:8000/docs → click `POST /api/process` → Try it out → upload PDF → Execute

### Option B — Python test script
```bash
python test_api.py
# or with custom PDF:
python test_api.py my_claim.pdf
```

### Option C — cURL
```bash
curl -X POST http://localhost:8000/api/process \
  -F "claim_id=CLM-TEST-001" \
  -F "file=@final_image_protected.pdf" \
  | python -m json.tool
```

---

## Deployment (Render.com — Free)

1. Push code to GitHub (make sure `.env` is in `.gitignore`)
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Set the following:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variable: `OPENAI_API_KEY = sk-proj-...`
6. Click Deploy

Your live URL will be: `https://your-app-name.onrender.com`

---

## Key Design Decisions

### Why dual input (image + text)?
Each page is sent to GPT-4o as both a rendered PNG image AND extracted text. This means the pipeline works on:
- **Text-based PDFs** — PyMuPDF extracts clean text directly
- **Scanned / image PDFs** — GPT-4o reads the image visually

### Why only page numbers are passed to agents?
The Segregator stores page numbers in state (`id_pages`, `discharge_pages`, `bill_pages`). Agents fetch only their assigned pages from the shared `pages` dict. This means:
- Each agent makes fewer API calls (processes fewer images)
- Clean separation of concerns
- Lower cost — bill agent never pays to process the ID card page

### Why is the Aggregator pure Python?
No AI call needed for merging — it just reads the 3 results from state and builds the final dict. This makes it fast, deterministic, and free.

---

## Environment Variables

| Variable | Required | Description | 
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key from platform.openai.com |

---

## Author

Jaspreet — Assignment submission for HealthPay AI
