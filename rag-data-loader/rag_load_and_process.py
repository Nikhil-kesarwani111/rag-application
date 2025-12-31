import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
from dotenv import load_dotenv

from langchain_community.document_loaders import DirectoryLoader, UnstructuredPDFLoader
from langchain_community.vectorstores.pgvector import PGVector
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_google_genai import GoogleGenerativeAIEmbeddings



load_dotenv()
print("\nStarting PDF ingestion script...\n")

# -----------------------------------------
# 1. ABSOLUTE PATHS (WORKS EVERYWHERE)
# -----------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
PDF_DIR = os.path.join(PROJECT_ROOT, "pdf-documents")

print(f" Looking for PDFs in: {PDF_DIR}")

if not os.path.exists(PDF_DIR):
    raise FileNotFoundError(f" PDF folder not found: {PDF_DIR}")

# -----------------------------------------
# 2. LOAD PDF FILES
# -----------------------------------------
loader = DirectoryLoader(
    PDF_DIR,
    glob="**/*.pdf",
    use_multithreading=True,
    show_progress=True,
    max_concurrency=20,
    loader_cls=UnstructuredPDFLoader,
)

docs = loader.load()
print(f" PDFs detected: {len(docs)}")

if not docs:
    print("No PDF files found. Exiting.")
    exit(0)

# -----------------------------------------
# 3. EMBEDDINGS (GEMINI)
# -----------------------------------------
embeddings = GoogleGenerativeAIEmbeddings(
    model="text-embedding-004",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

print("Using Gemini embeddings: text-embedding-004")

# -----------------------------------------
# 4. CHUNKING
# -----------------------------------------
print(" Attempting semantic chunking...")

try:
    text_splitter = SemanticChunker(embeddings=embeddings)
    chunks = text_splitter.split_documents(docs)
    print(" SemanticChunker successfully used")
except Exception as e:
    print("SemanticChunker FAILED, switching to RecursiveCharacterTextSplitter")
    print("   Error:", e)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )
    chunks = splitter.split_documents(docs)

print(f" Total chunks produced: {len(chunks)}")

# -----------------------------------------
# 5. STORE IN PGVECTOR
# -----------------------------------------
print(" Storing chunks in PGVector...")

store = PGVector.from_documents(
    documents=chunks,
    embedding=embeddings,
    collection_name="collection164",
    connection_string="postgresql+psycopg://postgres:postgres@localhost:5432/rag_app",
    pre_delete_collection=True,
)

print(" Ingestion completed! Embeddings stored in PostgreSQL PGVector.")
