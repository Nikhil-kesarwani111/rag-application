import os
import asyncio
from operator import itemgetter
from typing_extensions import TypedDict
from dotenv import load_dotenv
from sqlalchemy import text

from langchain_community.vectorstores.pgvector import PGVector
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    RunnableLambda,
    RunnableParallel,
)

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)

load_dotenv()
print("🚀 Loading RAG chain...")

# ============================================================
# 1. VECTOR STORE
# ============================================================
    
vector_store = PGVector(
    collection_name="collection164",
    connection_string="postgresql+psycopg://postgres:postgres@localhost:5432/rag_app",
    embedding_function=GoogleGenerativeAIEmbeddings(
        model="text-embedding-004",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    ),
)

print("📦 Vector store loaded")


# ============================================================
# Optional: Count vectors
# ============================================================

def get_vector_count(store: PGVector):
    try:
        with store._bind.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM langchain_pg_embedding"))
            return result.scalar()
    except Exception as e:
        print("⚠️ Error counting vectors:", e)
        return 0

print("🔢 Vector count:", get_vector_count(vector_store))


# ============================================================
# 2. PROMPT TEMPLATE
# ============================================================

template = """
Use ONLY the context provided.
If the answer is missing, say "I don't know".

Context:
{context}

Question:
{question}
"""

ANSWER_PROMPT = ChatPromptTemplate.from_template(template)


# ============================================================
# 3. GEMINI MODEL
# ============================================================

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    streaming=False,
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

print("🧠 Gemini LLM loaded")


# ============================================================
# 4. INPUT TYPE
# ============================================================

class RagInput(TypedDict):
    question: str


# ============================================================
# 5. CREATE CLEAN DOCS PROCESSOR
# Only keep filename in metadata.source
# ============================================================

def clean_docs(docs):
    cleaned = []
    for d in docs:
        meta = dict(d.metadata)

        if "source" in meta:
            meta["source"] = os.path.basename(meta["source"])  # <--- FIX HERE

        cleaned.append({
            "page_content": d.page_content,
            "metadata": meta
        })

    return cleaned

clean_docs_runnable = RunnableLambda(clean_docs)


# ============================================================
# 6. DEBUG RETRIEVER (OPTIONAL)
# ============================================================

async def debug_retriever(question: str):
    print("\n❓ Query:", question)

    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4},
    )

    docs = await asyncio.get_running_loop().run_in_executor(
        None, retriever.invoke, question
    )

    print(f"📄 Retrieved {len(docs)} documents")
    for idx, d in enumerate(docs[:3]):
        print(f"\n--- Doc {idx+1} ---")
        print(d.page_content[:200], "...\n")
        print("📁 Source:", d.metadata.get("source"))

    return docs

debug_runnable = RunnableLambda(debug_retriever)


# ============================================================
# 7. FINAL PROFESSIONAL RAG CHAIN
# ============================================================

final_chain = (
    RunnableParallel(
        context=itemgetter("question") | vector_store.as_retriever(),
        question=itemgetter("question")
    )
    |
    RunnableParallel(
        answer=(ANSWER_PROMPT | llm),
        docs=itemgetter("context") | clean_docs_runnable
    )
).with_types(input_type=RagInput)

print("🎉 RAG chain ready!")
