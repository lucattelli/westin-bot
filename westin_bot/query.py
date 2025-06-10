import sqlite3
import sys

import numpy as np
import sqlite_vec
from openai import OpenAI

SYSTEM_MESSAGE = """
Você é o **Westin Bot**, um assistente virtual especializado em administração condominial.

OBJETIVO
• Ajudar proprietários a encontrar informações nos documentos oficiais do Condomínio (Regulamento Interno, Convenção de Condomínio, Guia do Proprietário, Manual de Reformas, comunicados, atas etc.).
• Explicar regras, prazos e procedimentos de forma clara, objetiva e educada, sempre em português.
• Ser educado, mas sem ser muito prolixo nas respostas.

REGRAS DE RESPOSTA
1. **Use apenas o “Contexto” fornecido**. Não consulte conhecimento externo nem “improvise” informações.
2. Se a resposta não estiver no contexto, diga de forma breve:
   > “Desculpe, não encontrei essa informação nos documentos disponíveis.”
3. Priorize trechos exatos dos documentos; cite artigo, página ou seção quando possível.
4. Estruture a resposta com títulos, listas ou passos numerados quando ajudar na clareza.
5. Mantenha tom cordial e profissional; evite jargões jurídicos desnecessários.
6. Se a pergunta for ampla ou ambígua, peça detalhes ao usuário antes de responder.

FORMATOS
- Para procedimentos: use “Passo 1, Passo 2…”.
- Para regras ou proibições: use bullet points.
- Para prazos: escreva as datas completas (ex.: “até 15/07/2025”).
"""

USER_MESSAGE = """
**Contexto**
{context}

**Pergunta do proprietário**
{question}

**Instruções**
Responda em português seguindo as REGRAS DE RESPOSTA do Westin Bot.
"""

CHAT_MODEL = "gpt-4o-mini-2024-07-18"
CHAT_TEMP = 0


def ask_question(question: str) -> str:
    client = OpenAI()

    response = client.embeddings.create(input=question, model="text-embedding-3-small")
    query_embedding = np.array(response.data[0].embedding, dtype=np.float32).tobytes()

    conn = sqlite3.connect("db/embeddings.db")
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)

    cursor = conn.execute(
        f"""
        SELECT doc_name, chunk_text
        FROM vec_chunks
        WHERE embedding match ?
        ORDER BY distance
        LIMIT ?
    """,
        (query_embedding, 5),
    )

    results = cursor.fetchall()

    context = ""
    for doc_name, chunk_text in results:
        context += f"**Documento: {doc_name}**\n\n{chunk_text}\n\n"

    answer_response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_MESSAGE},
            {
                "role": "user",
                "content": USER_MESSAGE.format(context=context, question=question),
            },
        ],
        model=CHAT_MODEL,
        temperature=CHAT_TEMP,
    )

    return answer_response.choices[0].message.content


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Use uv run python westin_bot/query.py 'question text?'")
        sys.exit(1)

    answer = ask_question(" ".join(sys.argv[1:]))

    print("Resposta:", answer)
