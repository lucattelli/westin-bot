import sqlite3
from datetime import datetime

import numpy as np
import pymupdf
import sqlite_vec
from openai import OpenAI


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
    for i, art in enumerate(doc):
        if i > 0:
            document_text += art.get_text()[46:].lstrip()

    for idx, chapter in enumerate(chapters):
        chapter["start_index"] = document_text.index(chapter["name"])
        if len(chapters) == idx + 1:
            chapter["end_index"] = len(document_text)
        else:
            chapter["end_index"] = document_text.index(chapters[idx + 1]["name"])
        ch_text = document_text[chapter["start_index"] : chapter["end_index"]]
        chapter["chunks"] = ch_text.split("\nArt.")

        for idx, chunk in enumerate(chapter["chunks"]):
            if idx > 0:
                chapter["chunks"][idx] = f"{chapter['chunks'][0]}\n\nArt. {chunk}"
        del chapter["chunks"][0]

    conn = sqlite3.connect("db/embeddings.db")
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)  # Load the vector extension

    conn.execute(
        """
        CREATE VIRTUAL TABLE vec_chunks USING vec0(
            document_id INTEGER PARTITION KEY,
            embedding FLOAT[1536],
            doc_name TEXT,
            chunk_text TEXT
        );
    """
    )

    conn.commit()

    doc_name = "Regulamento Interno"

    client = OpenAI()
    for chapter in chapters:
        for chunk in chapter["chunks"]:
            print("Creating embedding for:\n", chunk, "\n---")
            response = client.embeddings.create(
                input=chunk,
                model="text-embedding-3-small",
            )
            embedding = response.data[0].embedding
            embedding_array = np.array(embedding, dtype=np.float32).tobytes()
            row_id = int(datetime.now().timestamp())
            conn.execute(
                "INSERT INTO vec_chunks (document_id, embedding, doc_name, chunk_text) VALUES (?, ?, ?, ?)",
                (
                    hash(doc_name),
                    embedding_array,
                    doc_name,
                    chunk,
                ),
            )
            conn.commit()


if __name__ == "__main__":
    get_regulamento_interno_embeddings()
