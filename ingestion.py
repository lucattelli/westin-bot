from dataclasses import dataclass

import pymupdf


@dataclass
class DocPage:
    file_name: str
    file_descr: str
    page_number: int
    page_text: str


def get_doc_pages_from_pdf(file_name: str, file_descr: str) -> list[DocPage]:
    doc_pages: list[DocPage] = []
    doc = pymupdf.open(f"data/{file_name}")
    for num, page in enumerate(doc, 1):
        text = page.get_text()
        doc_pages.append(
            DocPage(
                file_name=file_name,
                file_descr=file_descr,
                page_number=num,
                page_text=text,
            )
        )
    return doc_pages


if __name__ == "__main__":
    dp = get_doc_pages_from_pdf(
        file_name="regulamento-interno.pdf",
        file_descr="Regulamento Interno",
    )

    print(len(dp))
    print(dp[0])
