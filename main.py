"""
main.py
---------
FastAPI application.

    GET  /            - simple HTML UI
    POST /api/process - main claim processing endpoint
"""

import os, sys, tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, HTMLResponse
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
        "**FastAPI + LangGraph** multi-agent service that processes PDF insurance claims.\n\n"
        "**Workflow:** Segregator → ID Agent → Discharge Agent → Bill Agent → Aggregator"
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


# 🌐 ================= UI ROUTE =================
@app.get("/", response_class=HTMLResponse)
async def ui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Claim Processing UI</title>
        <style>
            body { font-family: Arial; padding: 20px; background: #f5f5f5; }
            h2 { color: #333; }
            input, button {
                margin: 8px 0;
                padding: 8px;
                width: 300px;
            }
            button {
                background: #007bff;
                color: white;
                border: none;
                cursor: pointer;
            }
            button:hover { background: #0056b3; }
            pre {
                background: #111;
                color: #0f0;
                padding: 15px;
                overflow-x: auto;
                max-height: 400px;
            }
        </style>
    </head>
    <body>

        <h2>📄 Claim Processing Pipeline</h2>

        <form id="form">
            <label>Claim ID:</label><br>
            <input type="text" name="claim_id" value="CLM-TEST-001" required><br>

            <label>Upload PDF:</label><br>
            <input type="file" name="file" accept="application/pdf" required><br>

            <button type="submit">Process Claim</button>
        </form>

        <h3>Response</h3>
        <pre id="output">Waiting...</pre>

        <script>
            const form = document.getElementById("form");
            const output = document.getElementById("output");

            form.addEventListener("submit", async (e) => {
                e.preventDefault();

                const formData = new FormData(form);
                output.textContent = "⏳ Processing... This may take time";

                try {
                    const res = await fetch("/api/process", {
                        method: "POST",
                        body: formData
                    });

                    const text = await res.text();

                    try {
                        const json = JSON.parse(text);
                        output.textContent = JSON.stringify(json, null, 2);
                    } catch {
                        output.textContent = text;
                    }

                } catch (err) {
                    output.textContent = "❌ Error: " + err;
                }
            });
        </script>

    </body>
    </html>
    """


# 🔥 ================= MAIN API =================
@app.post("/api/process", tags=["claims"])
async def process_claim(
    claim_id: str = Form(..., description="unique Claim ID"),
    file: UploadFile = File(..., description="PDF file"),
):
    filename = file.filename or ""

    if not filename.lower().endswith(".pdf") and file.content_type not in (
        "application/pdf",
        "application/octet-stream",
    ):
        raise HTTPException(400, "Only PDF files are accepted.")

    pdf_bytes = await file.read()

    if not pdf_bytes:
        raise HTTPException(400, "Uploaded file is empty.")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    print(f"  claim_id : {claim_id}")
    print(f"  file     : {filename}  ({len(pdf_bytes):,} bytes)")

    try:
        initial_state = {
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

        final_state = claim_graph.invoke(initial_state)
        result = final_state.get("final_result", {})

        print(f"\n✅ Claim {claim_id} processed successfully.\n")
        return JSONResponse(content=result, status_code=200)

    except Exception as exc:
        print(f"\n❌ Error:\n {exc}")
        raise HTTPException(
            status_code=500,
            detail={"error": str(exc), "claim_id": claim_id},
        )

    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# 🚀 ================= RUN =================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
