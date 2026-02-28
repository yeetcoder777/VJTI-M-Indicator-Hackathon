import os
import base64
import fitz  # PyMuPDF
import chromadb
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ---------- CONFIG ----------
PDF_DIR = r"C:\M_Indicator_Hackathon\VJTI-M-Indicator-Hackathon\data_sources"
CHROMA_DB_PATH = r"C:\M_Indicator_Hackathon\VJTI-M-Indicator-Hackathon\scripts\chroma_db"
COLLECTION_NAME = "farmer_schemes"
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 250
MIN_CHARS_PER_PAGE = 50


# ---------- GROQ OCR ----------
groq_client = Groq()


def ocr_page(pdf_path: str, page_number: int) -> str:
    """
    Convert a single PDF page to image using PyMuPDF
    and extract text via Groq Vision.
    page_number is 0-indexed.
    """
    doc = fitz.open(pdf_path)
    page = doc[page_number]

    # Render page to PNG at 150 DPI to reduce payload size
    pix = page.get_pixmap(dpi=150)
    
    # If the image is still massive, resize it to a max dimension
    max_dim = 1024
    if pix.width > max_dim or pix.height > max_dim:
        scale = max_dim / max(pix.width, pix.height)
        matrix = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=matrix, dpi=150)

    image_bytes = pix.tobytes("png")
    image_base64 = base64.b64encode(image_bytes).decode()
    doc.close()

    # Send to Groq Vision
    response = groq_client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract ALL text from this document image. Return only the extracted text, nothing else. Preserve the structure and formatting.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        },
                    },
                ],
            }
        ],
        temperature=0.1,
        max_completion_tokens=2048,
    )

    return response.choices[0].message.content


# ---------- PDF EXTRACTION ----------
def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """
    Extract text from a PDF.
    Auto-detects scanned vs text-based pages.
    """
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    filename = os.path.basename(pdf_path)
    scheme_name = os.path.splitext(filename)[0]

    results = []

    for i, doc in enumerate(docs):
        page_text = doc.page_content.strip()

        if len(page_text) >= MIN_CHARS_PER_PAGE:
            # Text-based page
            print(f"  Page {i+1}: text-based ({len(page_text)} chars)")
            results.append({
                "page_content": page_text,
                "metadata": {
                    "source": pdf_path,
                    "scheme_name": scheme_name,
                    "page": i + 1,
                    "extraction_method": "text",
                },
            })
        else:
            # Scanned page — run OCR via Groq
            print(f"  Page {i+1}: scanned, running Groq OCR...")
            try:
                ocr_text = ocr_page(pdf_path, page_number=i)
                if ocr_text and ocr_text.strip():
                    results.append({
                        "page_content": ocr_text,
                        "metadata": {
                            "source": pdf_path,
                            "scheme_name": scheme_name,
                            "page": i + 1,
                            "extraction_method": "ocr_groq",
                        },
                    })
                else:
                    print(f"  Page {i+1}: OCR returned empty, skipping")
            except Exception as e:
                print(f"  Page {i+1}: Groq API error ({e}), skipping to save progress")

    return results


# ---------- CHUNKING ----------
def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Split documents into smaller chunks for embedding.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    all_chunks = []

    for doc in documents:
        text_chunks = splitter.split_text(doc["page_content"])

        for chunk_text in text_chunks:
            all_chunks.append({
                "page_content": chunk_text,
                "metadata": doc["metadata"],
            })

    return all_chunks


# ---------- EMBED & STORE ----------
def embed_and_store(chunks: list[dict], collection, embedding_model):
    """
    Embed chunks and add to ChromaDB in batches.
    """
    documents = [chunk["page_content"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    ids = [f"chunk_{i}" for i in range(len(chunks))]

    print(f"\nEmbedding {len(documents)} chunks...")
    embeddings = embedding_model.encode(documents, show_progress_bar=True)
    embeddings_list = embeddings.tolist()

    BATCH_SIZE = 100
    for start in range(0, len(documents), BATCH_SIZE):
        end = min(start + BATCH_SIZE, len(documents))
        collection.add(
            documents=documents[start:end],
            embeddings=embeddings_list[start:end],
            metadatas=metadatas[start:end],
            ids=ids[start:end],
        )
        print(f"  Added batch {start}-{end}")


# ---------- MAIN ----------
def main():
    # 1. Load embedding model once
    print("Loading embedding model...")
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    # 2. Setup persistent ChromaDB
    print("Setting up ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    # # Delete old collection if re-ingesting
    # try:
    #     client.delete_collection(COLLECTION_NAME)
    #     print(f"Deleted existing collection '{COLLECTION_NAME}'")
    # except ValueError:
    #     pass

    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    # 3. Process all PDFs
    all_documents = []

    for filename in sorted(os.listdir(PDF_DIR)):
        if not filename.endswith(".pdf"):
            continue

        pdf_path = os.path.join(PDF_DIR, filename)
        print(f"\nProcessing: {filename}")

        docs = extract_text_from_pdf(pdf_path)
        all_documents.extend(docs)
        print(f"  Extracted {len(docs)} pages")

    print(f"\nTotal pages extracted: {len(all_documents)}")

    # 4. Chunk
    chunks = chunk_documents(all_documents)
    print(f"Total chunks after splitting: {len(chunks)}")

    # 5. Embed and store
    embed_and_store(chunks, collection, embedding_model)

    print(f"\nDone! {len(chunks)} chunks stored in ChromaDB at '{CHROMA_DB_PATH}'")
    print(f"Collection: '{COLLECTION_NAME}'")


if __name__ == "__main__":
    main()
