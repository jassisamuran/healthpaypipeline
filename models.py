"""
models.py

shared srate TypeDict and Documenttype enum userd by every node in the graph.
LangGraph used ClaimState as the single shard object passed between ndoes.
"""

from typing import TypedDict,Optional,Any
from enum import Enum

class DocumentType(str,Enum):
    CLAIM_FORM='claim_forms'
    CHEQUE_OR_BANK='cheque_or_bank_details'
    IDENTITY_DOCUMENT='identity_document'
    ITEMIZED_DOCUMENT='itemized_bill'
    DISCHARGE_SUMMARY='discharge_summary'
    PRESCRIPTION='prescription'
    INVESTIGATION_REPORT='investigation_report'
    CASH_RECEIPT='cash_receipt'
    OTHER='other'


class PageDate(TypedDict):
    page_numer:int
    text:str
    image_b64:str


class ClaimedState(TypedDict):
    Claim_id:str
    pdf_path:str

    pages:dict
    page_classifications:dict
    id_pages:list
    discharge_page:list
    bill_pages:list

    id_result:dict
    discharge_result:dict
    bill_result:dict

    final_result:dict
    error:Optional[str]

