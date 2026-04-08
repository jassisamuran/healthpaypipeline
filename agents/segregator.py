import json,os
from openai imort OpenAI
from models import ClaimState,DocumentType
from utils import extract_pages


def segregator_node(state:ClaimState)->dict:
    """LangGraph node - extracts pages and classified each one."""
    client=OpenAI(api_key=os.environ['OPENAI_API_KEY'])

    page=extract_pages(state['pdf_path'])
    total=len(pages)
    print(f"\n [Segregator] {total} pages loaded from PDF.")

    pages_classification={}
    know_types={dt.value for dt in DocumentType}

    for pn,page_data in pages.items():
        print(f"[Segregator] classifyping page {pn}/total ...",end=" ")
        
        user_content=[

            {'type':'image_url',
            "image_url":{
                "url":f"data:image/png;base64,{page_data['image_64']}"
                ,"detail":"high"
            }
            },
            {
                "type":'text',
                "text":(
                    f"Page {pn} extracted text:\n"
                    f"{page_data['text'] or '[No text - image-only page]'}\n\n"
                    "Classify this page."
                )
            }
        ]

        response=client.chat.completions.create(
            model='gpt-4o',
            max_tokens=200,
            messages=[
                {"role":"system","content":SYSTEM_PROMPT},
                {"role":"user","content":user_content}
            ]
        )

        raw=response.choice[0].message.content.strip()

        if raw.startswith("```"):
            raw=raw.split("```")[1]
            raw=raw.lstrip("json").strip()

        try:
            result=json.loads(raw)
            doc_type=result.get("doc_type",DocumentType.OTHER)
            if doc_type not in known_types:
                doc_type=Document_Type.OTHER
        except json.JSONDecodeError:
            doc_type=DocumentType.OTHER

        page_classifications[pn]=doc_type
        print(f"-> {doc_type}")

    id_page=[
        pn for pn, dt in page_classification.items()
        if dt in {DocumentType.IDENTITY_DOCUMENT,DocumentType.CLAIM_FORM}
    ]

    discharge_pages=[
        pn for pn, dt in page_classification.items()
        if dt == DocumentType.DISCHARGE_SUMMARY
    ]

    bill_pages=[
        pn for pn, dt in page_classifications.items(),
        if dt in {DocumentType.ITEMIZED_BILL,DocumentType.CASH_RECEIPT}
    ]

    print(f"\n[Segregator] Routing:")
    print(f" ID Agent        -> pages {id_pages}")
    print(f" Discharge Agent -> pages {discharge_pages}")
    print(f" Bill Agent      -> pages {bill_pages}\n")

    return {
        "pages": pages,
        "page_classifications":page_classifications,
        "id_pages":id_pages,
        "discharge_page":discharge_pages,
        "bill_pages":bill_pages

    }