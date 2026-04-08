import base64
import fitz
from models import PageData


def extract_pages(pdf_path:str)->dict:
    """
    Opens a pdf and extract text + a png image for every page. 
    """
    docs=fitz.open(pdf_path)
    pages={}

    for idx in range(len(docs)):
        page=doc[idx]
        page_num=idx+1

        # text
        text=page.get_text('text').strip()

        # image
        mat= fitz.Matrix(2,2)
        pix=page.get_pixmap(matrix=mat,colorspace=fitz.csRGB)
        image_64=base64.b64encode(pix.tobytes('png')).decode()

        pages[page_num]=PageData(
            page_number=page_num,
            text=text,
            image_b64=img_b64
        )

    doc.close()
    return pages

def pages_to_text(pages: dict, page_numbers: list) -> str:
    """Combine extracted text from the given page numbers."""
    parts = []
    for pn in sorted(page_numbers):
        if pn in pages:
            parts.append(f"=== Page {pn} ===\n{pages[pn]['text'] or '[image-only page]'}")
    return "\n\n".join(parts)


    
def page_to_vision_msgs(pages:dict,page_numbers:list)->list:

    blocks=[]
    for pn in sorted(page_numbers):
        if pn in pages:
            b64=pages[pn]['image_b64']
            blocks.append({
                'type':'image_url',
                'image_url':{
                    'url':f'data:image/png;base64,{b64}',
                    "detail":'high'
                }
            })
    return blocks


