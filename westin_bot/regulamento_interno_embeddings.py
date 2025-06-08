import pymupdf


def get_regulamento_interno_embeddings():
    file_name = "regulamento-interno.pdf"
    doc = pymupdf.open(f"data/{file_name}")

    first_page = doc[0].get_text()[46:].lstrip()
    chapter_index = first_page[first_page.index("ÍNDICE") + 6 :].strip().split("\n")

    chapters = []

    for chapter in chapter_index:
        chapter_words = chapter.split(" ")
        if chapter_words[0] == "CAPÍTULO":
            chapters.append(
                {"name": f"{chapter_words[0]} {chapter_words[1]}".replace("–", "")}
            )

    document_text = ""
    for i, p in enumerate(doc):
        if i > 0:
            document_text += p.get_text()[46:].lstrip()

    for idx, chapter in enumerate(chapters):
        chapter["start_index"] = document_text.index(chapter["name"])
        if len(chapters) == idx + 1:
            chapter["end_index"] = len(document_text)
        else:
            chapter["end_index"] = document_text.index(chapters[idx+1]["name"])
        chapter["text"] = document_text[chapter["start_index"]:chapter["end_index"]]


    for chapter in chapters:
        print(chapter["text"])
        print("\n\n-------------\n\n")

if __name__ == "__main__":
    get_regulamento_interno_embeddings()
