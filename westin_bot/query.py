import sqlite3

import numpy as np
import sqlite_vec
from openai import OpenAI

client = OpenAI()


def ask_question(question: str):
    response = client.embeddings.create(input=question, model="text-embedding-3-small")
    query_embedding = np.array(response.data[0].embedding, dtype=np.float32).tobytes()

    conn = sqlite3.connect("db/embeddings.db")
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)

    cursor = conn.execute(
        f"""
        SELECT document_id, embedding, doc_name, chunk_text
        FROM vec_chunks
        WHERE embedding match ?
        LIMIT ?
    """,
        (query_embedding, 5),
    )

    results = cursor.fetchall()

    for i, (document_id, embedding, doc_name, chunk_text) in enumerate(results):
        print(i, ") CHUNK:\n", chunk_text, "\n-----\n")

if __name__ == "__main__":
    ask_question("Qual o horário da academia?")
