"""
main.py
---------
FastAPI application.

    POST /api/process - main claim processing endpoint
"""

import os, sys, tempfile, traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()


sys.path.insert(0, os.path.dirname(__file__))
from graph import claim_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Claim processing Pipeline ready.")
    yield
    print("Shutting down.")


app = FastAPI(
    title="Claim Processing Pipeline",
    description=(
        "**FastAPI + LangGraph** multi-agent service that proceses PDF insurance claims.\n\n"
        "**WorkFlow:** Segregator->ID Agent -> Discharge Agent -> Bill Agent ->Aggregator"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/process", tags=["claims"])
async def process_claim(
    claim_id: str = Form(..., description="unique Claim ID, e.g. CLM-2024-344343"),
    file: UploadFile = File(..., description="PDF file containing claim documents"),
):
    """
    Upload a PDF claim and get structured JSON back.

    **Steps performed:**
    1. Segregator classifies every page into 1 of 9 document types
    2. ID Agent extracts patient identity & policy info (identity_document / claim_form pages)
    3. Discharge Agent extracts clinical data (discharge_summary pages)
    4. Bill Agent extracts itemised charges (itemized_bill / cash_receipt pages)
    5. Aggregator merges everything into the response JSON
    """
    filename = file.filename or ""
    if not filename.lower().endswith(".pdf") and file.content_type not in (
        "application/pdf",
        "application/octet-stream",
    ):
        raise HTTPException(400, "Only pdf files are accepted.")

    pdf_bytes = await file.read()

    if not pdf_bytes:
        raise HTTPException(400, "UPloaded file is empty.")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    print(f"  claim_id : {claim_id}")
    print(f"  file     : {filename}  ({len(pdf_bytes):,} bytes)")

    try:
        intial_state = {
            "claim_id": claim_id,
            "pdf_path": tmp_path,
            "pages": {},
            "page_classifications": {},
            "id_pages": [],
            "discharge_pages": [],
            "bill_pages": [],
            "id_result": {},
            "discharge_result": {},
            "bill_result": {},
            "final_result": {},
            "error": None,
        }

        final_state = claim_graph.invoke(intial_state)
        result = final_state.get("final_result", {})

        print(f"\n Claim {claim_id} processed successfully.\n")
        return JSONResponse(content=result, status_code=200)

    except Exception as exc:
        print(f"\n Error:\n {exc}")
        raise HTTPException(
            status_code=500,
            detail={"error": str(exc), "claim_id": claim_id},
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
