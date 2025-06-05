import io
import os
import re
import shutil
import sqlite3
import time
import traceback
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

import faiss
import fitz  # PyMuPDF
import numpy as np
import psutil
import pytesseract
import uvicorn
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS as LangChainFAISS
from passlib.context import CryptContext
from PIL import Image
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

import logging

log_dir = Path("Server/logs")
log_file = log_dir / "extracted_text.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Product(BaseModel):
    company_name: str
    product_name: str
    product_type: str
    datasheet_path: str
    specs: str


class SearchQuery(BaseModel):
    requirements: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_dir.mkdir(parents=True, exist_ok=True)
    init_db()
    await populate_database()
    yield
    logger.info("Application shutdown")


app = FastAPI(lifespan=lifespan)

# Mount the Client directory to serve static files using pathlib for robust path resolution
client_dir = Path(__file__).parent.parent / "Client"
app.mount("/static", StaticFiles(directory=str(client_dir)), name="static")


@app.get("/")
async def serve_frontend():
    return FileResponse(str(client_dir / "index.html"))


# Add health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# CORS settings with placeholder for Heroku app URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://purchasing-base-unit-deploy.onrender.com",  # Placeholder
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://192.168.1.117:8080",
        "http://192.168.1.109:8080",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "HEAD", "OPTIONS"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = os.getenv(
    "SECRET_KEY", "e076b3ebc22000ea628b8526b552e7dd838c757d6e46d27978920eebd383431b"
)
ALGORITHM = "HS256"

users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("admin123"),
    },
}


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        logger.info(f"Received token: {token}")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"Decoded token payload: {payload}")
        username: str = payload.get("sub")
        if username not in users_db:
            logger.error(f"Invalid authentication credentials for username: {username}")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
            )
        return username
    except JWTError as e:
        logger.error(f"Invalid token: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")


db_path = Path("Server/database.sqlite")
index_path = Path("Server/faiss_index")


def init_db():
    conn = sqlite3.connect(db_path, timeout=30)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT,
            name TEXT,
            product_type TEXT,
            datasheet_path TEXT UNIQUE,
            directory TEXT,
            specs TEXT
        )
    """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS extracted_texts (
            datasheet_path TEXT PRIMARY KEY,
            extracted_text TEXT
        )
    """
    )
    conn.commit()
    conn.close()


embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def extract_page(page):
    text = page.get_text("text") + "\n"
    blocks = page.get_text("blocks")
    for block in blocks:
        if block[4].startswith("<table"):
            text += block[4] + "\n"
    return text


def extract_text_from_pdf_sync(pdf_path, conn):
    if not Path(pdf_path).exists():
        logger.error(f"PDF file does not exist: {pdf_path}")
        return ""

    c = conn.cursor()
    retries = 5
    for attempt in range(retries):
        try:
            c.execute(
                "SELECT extracted_text FROM extracted_texts WHERE datasheet_path = ?",
                (pdf_path,),
            )
            row = c.fetchone()
            if row:
                logger.info(f"Retrieved cached text for {pdf_path}")
                return row[0]

            text = ""
            with fitz.open(pdf_path) as pdf:
                if pdf.page_count == 0:
                    logger.warning(f"PDF {pdf_path} has no pages")
                    return text
                for page in pdf:
                    text += extract_page(page)

            text = re.sub(r"\n\s*\n", "\n", text).replace("\t", " ").strip()
            if len(text.strip()) < 50:
                logger.warning(
                    f"Text extraction yielded insufficient content "
                    f"({len(text)} chars) from {pdf_path}, using OCR fallback"
                )
                text = ""
                with fitz.open(pdf_path) as pdf:
                    for page in pdf:
                        pix = page.get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72))
                        img = Image.frombytes(
                            "RGB", [pix.width, pix.height], pix.samples
                        )
                        ocr_text = pytesseract.image_to_string(img, config="--psm 6")
                        text += ocr_text + "\n"
                text = re.sub(r"\n\s*\n", "\n", text).replace("\t", " ").strip()

            if not text.strip():
                logger.warning(f"No text extracted from {pdf_path} even after OCR")
            else:
                logger.info(f"Extracted {len(text)} chars from {pdf_path}")

            c.execute(
                "INSERT OR REPLACE INTO extracted_texts "
                "(datasheet_path, extracted_text) VALUES (?, ?)",
                (pdf_path, text),
            )
            conn.commit()
            return text

        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                if attempt < retries - 1:
                    logger.warning(
                        f"Database locked on attempt {attempt + 1} for {pdf_path}, "
                        "retrying..."
                    )
                    time.sleep(1)
                    continue
                else:
                    logger.error(
                        f"Failed to extract text from {pdf_path} after "
                        f"{retries} attempts: {e}"
                    )
                    raise
            else:
                logger.error(f"Failed to extract text from {pdf_path}: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path}: {e}")
            raise


async def extract_text_from_pdf(pdf_path, conn=None):
    if conn is None:
        conn = sqlite3.connect(db_path)
        own_connection = True
    else:
        own_connection = False
    try:
        text = extract_text_from_pdf_sync(pdf_path, conn)
        return text
    finally:
        if own_connection:
            conn.close()


async def scan_directories(base_dir):
    results = []
    base_path = Path(base_dir)
    for pdf_path in base_path.rglob("*.pdf"):
        if not pdf_path.exists():
            logger.warning(
                f"PDF path not found: {pdf_path} (absolute path: {pdf_path.resolve()})"
            )
            continue
        relative_path = str(pdf_path.relative_to(base_path))
        directory = str(pdf_path.parent.relative_to(base_path))
        results.append(
            {
                "pdf_path": str(pdf_path),
                "relative_path": relative_path,
                "directory": directory,
            }
        )

    logger.info(f"Scanned {base_dir}, found {len(results)} PDFs")
    return results


async def initialize_empty_vector_store():
    dummy_text = ["Initialize empty FAISS index"]
    vector_store = LangChainFAISS.from_texts(
        texts=dummy_text,
        embedding=embeddings,
        metadatas=[{"product_id": -1}],
    )
    vector_store.save_local("Server/faiss_index")
    logger.info("Initialized empty FAISS index to prevent loading errors")


async def populate_database():
    try:
        if not index_path.exists():
            index_path.mkdir(parents=True, exist_ok=True)

        faiss_file = index_path / "index.faiss"
        pkl_file = index_path / "index.pkl"
        if (faiss_file.exists() and faiss_file.stat().st_size == 0) or (
            pkl_file.exists() and pkl_file.stat().st_size == 0
        ):
            logger.warning("Empty FAISS index files detected, removing them")
            if faiss_file.exists():
                faiss_file.unlink()
            if pkl_file.exists():
                pkl_file.unlink()

        if not (faiss_file.exists() and pkl_file.exists()):
            await initialize_empty_vector_store()

        datasheets_dir = Path("DataSheets")
        if not datasheets_dir.exists():
            logger.error(f"Directory not found: {datasheets_dir}")
            return

        pdf_files = await scan_directories(datasheets_dir)
        if not pdf_files:
            logger.warning("No PDF files found in DataSheets/")
            return

        conn = sqlite3.connect(db_path, timeout=30)
        c = conn.cursor()
        c.execute("SELECT datasheet_path FROM products")
        existing_paths = {row[0] for row in c.fetchall()}

        texts = []
        metadatas = []
        product_ids = []
        new_pdfs = []
        for pdf in pdf_files:
            pdf_path = pdf["pdf_path"]
            if pdf_path in existing_paths:
                logger.info(f"Skipping already processed PDF: {pdf_path}")
                continue
            if not Path(pdf_path).exists():
                logger.warning(f"Datasheet not found: {pdf_path}")
                continue
            new_pdfs.append(pdf)

        logger.info(f"Found {len(new_pdfs)} new PDFs to process")
        batch_size = 50
        for i in range(0, len(new_pdfs), batch_size):
            batch = new_pdfs[i : i + batch_size]
            logger.info(
                f"Processing batch {i // batch_size + 1} with {len(batch)} PDFs"
            )
            for pdf in batch:
                pdf_path = pdf["pdf_path"]
                relative_path = pdf["relative_path"]
                directory = pdf["directory"]
                path_parts = relative_path.split(os.sep)
                company = path_parts[0] or "Unknown"
                product_type = path_parts[-2] if len(path_parts) > 2 else "Unknown"
                product_name = Path(pdf_path).stem.replace("-spec-sheet", "")
                specs = await extract_text_from_pdf(pdf_path, conn)
                if not specs:
                    logger.warning(
                        f"Skipping product insertion for {pdf_path} due to no text"
                    )
                    continue

                c.execute(
                    "INSERT OR IGNORE INTO products "
                    "(company, name, product_type, datasheet_path, directory, specs) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (company, product_name, product_type, pdf_path, directory, specs),
                )
                if c.rowcount > 0:
                    product_id = c.lastrowid
                    texts.append(specs)
                    metadatas.append({"product_id": product_id})
                    product_ids.append(product_id)
                    logger.info(
                        f"Inserted product: {company}/{product_type}/{product_name} "
                        f"with product_id {product_id}"
                    )
            conn.commit()

        conn.close()
        if texts:
            try:
                vector_store = LangChainFAISS.load_local(
                    "Server/faiss_index",
                    embeddings,
                    allow_dangerous_deserialization=True,
                )
                faiss_batch_size = 50  # Reduced to mitigate memory issues
                for i in range(0, len(texts), faiss_batch_size):
                    batch_texts = texts[i : i + faiss_batch_size]
                    batch_metadatas = metadatas[i : i + faiss_batch_size]
                    process = psutil.Process()
                    mem_usage = process.memory_info().rss / 1024 / 1024
                    logger.info(
                        f"Adding FAISS batch {i // faiss_batch_size + 1} with "
                        f"{len(batch_texts)} texts, memory usage: {mem_usage:.2f} MB"
                    )
                    vector_store.add_texts(batch_texts, metadatas=batch_metadatas)
                    logger.info(f"Completed FAISS batch {i // faiss_batch_size + 1}")
                vector_store.save_local("Server/faiss_index")
                logger.info(f"Updated FAISS index with {len(texts)} new embeddings")
            except Exception as e:
                logger.error(f"Failed to update FAISS index: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                try:
                    logger.info("Attempting to reinitialize FAISS index")
                    vector_store = LangChainFAISS.from_texts(
                        texts[:100],
                        embeddings,
                        metadatas=metadatas[:100],
                    )
                    for i in range(100, len(texts), faiss_batch_size):
                        batch_texts = texts[i : i + faiss_batch_size]
                        batch_metadatas = metadatas[i : i + faiss_batch_size]
                        process = psutil.Process()
                        mem_usage = process.memory_info().rss / 1024 / 1024
                        logger.info(
                            f"Adding FAISS batch {i // faiss_batch_size + 1} with "
                            f"{len(batch_texts)} texts, memory usage: {mem_usage:.2f} MB"
                        )
                        vector_store.add_texts(batch_texts, metadatas=batch_metadatas)
                        logger.info(
                            f"Completed FAISS batch {i // faiss_batch_size + 1}"
                        )
                    vector_store.save_local("Server/faiss_index")
                    logger.info(
                        f"Reinitialized FAISS index with {len(texts)} embeddings"
                    )
                except Exception as e:
                    logger.error(f"Failed to reinitialize FAISS index: {str(e)}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    raise
        else:
            logger.info("No new products added, FAISS index unchanged")

        conn = sqlite3.connect(db_path, timeout=30)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM products")
        total_products = c.fetchone()[0]
        logger.info(f"Total products in database after population: {total_products}")
        conn.close()
        logger.info("Database populated.")

    except Exception as e:
        logger.error(f"Error populating database: {e}")
        raise


@app.get("/api/products", dependencies=[Depends(get_current_user)])
async def get_products():
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = [dict(row) for row in c.fetchall()]
    conn.close()
    logger.info(f"Retrieved {len(products)} products from database")
    return {"products": products}


@app.post("/api/products", dependencies=[Depends(get_current_user)])
async def add_product(product: Product):
    try:
        datasheet_path = product.datasheet_path
        if (
            datasheet_path
            and datasheet_path != "N/A"
            and not Path(datasheet_path).exists()
        ):
            logger.warning(f"Datasheet path not found: {datasheet_path}")
            datasheet_path = "N/A"

        conn = sqlite3.connect(db_path, timeout=30)
        c = conn.cursor()
        c.execute(
            "INSERT INTO products "
            "(company, name, product_type, datasheet_path, directory, specs) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                product.company_name,
                product.product_name,
                product.product_type,
                datasheet_path,
                "",
                product.specs,
            ),
        )
        product_id = c.lastrowid
        conn.commit()
        conn.close()

        if product.specs:
            try:
                vector_store = LangChainFAISS.load_local(
                    "Server/faiss_index",
                    embeddings,
                    allow_dangerous_deserialization=True,
                )
                vector_store.add_texts(
                    [product.specs],
                    metadatas=[{"product_id": product_id}],
                )
                vector_store.save_local("Server/faiss_index")
                logger.info(f"Added product {product_id} to FAISS index")
            except Exception as e:
                logger.error(f"Failed to update FAISS index for new product: {e}")
                vector_store = LangChainFAISS.from_texts(
                    [product.specs],
                    embeddings,
                    metadatas=[{"product_id": product_id}],
                )
                vector_store.save_local("Server/faiss_index")
                logger.info(f"Reinitialized FAISS index with new product {product_id}")

        return {"product_id": product_id}

    except Exception as e:
        logger.error(f"Error adding product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload", dependencies=[Depends(get_current_user)])
async def upload_datasheet(file: UploadFile = File(...)):
    try:
        datasheets_dir = Path("DataSheets/Uploaded")
        datasheets_dir.mkdir(parents=True, exist_ok=True)
        file_path = datasheets_dir / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if not file_path.exists():
            logger.error(f"Uploaded file not saved: {file_path}")
            raise HTTPException(
                status_code=500,
                detail="Failed to save uploaded file",
            )

        specs = await extract_text_from_pdf(str(file_path))
        if not specs:
            raise HTTPException(
                status_code=400,
                detail="No text extracted from uploaded PDF",
            )

        file_name = file.filename.replace("-spec-sheet", "").replace(".pdf", "")
        conn = sqlite3.connect(db_path, timeout=30)
        c = conn.cursor()
        c.execute(
            "INSERT INTO products "
            "(company, name, product_type, datasheet_path, directory, specs) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("Uploaded", file_name, "Unknown", str(file_path), "Uploaded", specs),
        )
        product_id = c.lastrowid
        conn.commit()
        conn.close()

        try:
            vector_store = LangChainFAISS.load_local(
                "Server/faiss_index",
                embeddings,
                allow_dangerous_deserialization=True,
            )
            vector_store.add_texts([specs], metadatas=[{"product_id": product_id}])
            vector_store.save_local("Server/faiss_index")
            logger.info(f"Added uploaded datasheet {file_path} to FAISS index")
        except Exception as e:
            logger.error(f"Failed to update FAISS index for uploaded datasheet: {e}")
            vector_store = LangChainFAISS.from_texts(
                [specs],
                embeddings,
                metadatas=[{"product_id": product_id}],
            )
            vector_store.save_local("Server/faiss_index")
            logger.info(
                f"Reinitialized FAISS index with uploaded datasheet {file_path}"
            )

        logger.info(f"Uploaded and processed datasheet: {file_path}")
        return {"product_id": product_id, "datasheet_path": str(file_path)}

    except Exception as e:
        logger.error(f"Error uploading datasheet: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/datasheet/{product_id}", dependencies=[Depends(get_current_user)])
@app.head("/api/datasheet/{product_id}")
async def get_datasheet(product_id: int):
    try:
        conn = sqlite3.connect(db_path, timeout=30)
        c = conn.cursor()
        c.execute(
            "SELECT datasheet_path FROM products WHERE product_id = ?",
            (product_id,),
        )
        row = c.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Datasheet not found")

        datasheet_path = row[0]
        if datasheet_path == "N/A" or not Path(datasheet_path).exists():
            raise HTTPException(status_code=404, detail="Datasheet file not found")

        return FileResponse(
            datasheet_path,
            media_type="application/pdf",
            filename=Path(datasheet_path).name,
        )

    except Exception as e:
        logger.error(f"Error retrieving datasheet: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/favicon.ico")
async def get_favicon():
    favicon_path = Path("Server/favicon.ico")
    if not favicon_path.exists():
        raise HTTPException(status_code=404, detail="Favicon not found")
    return FileResponse(favicon_path, media_type="image/x-icon")


@app.options("/api/semantic_search")
async def options_semantic_search(request: Request):
    logger.info(f"OPTIONS request headers: {request.headers}")
    return JSONResponse(content={}, status_code=200)


@app.post("/api/semantic_search", dependencies=[Depends(get_current_user)])
async def semantic_search_products(query: SearchQuery):
    try:
        logger.info(f"Received semantic search query: {query.requirements}")
        conn = sqlite3.connect(db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        output = []

        # Step 1: Try semantic search with FAISS
        try:
            vector_store = LangChainFAISS.load_local(
                "Server/faiss_index",
                embeddings,
                allow_dangerous_deserialization=True,
            )
            faiss_index = vector_store.index
            metadata = vector_store.docstore._dict
            query_embedding = embeddings.embed_query(query.requirements)
            query_vector = np.array([query_embedding], dtype=np.float32)
            k = 10
            distances, indices = faiss_index.search(query_vector, k)
            logger.info(f"FAISS search returned {len(indices[0])} results")

            for idx, distance in zip(indices[0], distances[0]):
                if idx == -1:
                    continue
                doc_id = vector_store.index_to_docstore_id[idx]
                doc = metadata[doc_id]
                product_id = doc.metadata["product_id"]
                if product_id == -1:
                    continue

                c.execute(
                    "SELECT * FROM products WHERE product_id = ?",
                    (product_id,),
                )
                row = c.fetchone()
                if row:
                    similarity_score = 1 / (1 + distance) * 100
                    match_score = min(max(similarity_score, 0), 100)
                    output.append(
                        {
                            "product_id": row["product_id"],
                            "company": row["company"],
                            "name": row["name"],
                            "product_type": row["product_type"],
                            "datasheet_path": row["datasheet_path"],
                            "directory": row["directory"],
                            "specs": (
                                row["specs"][:100] + "..."
                                if row["specs"]
                                else "No specs"
                            ),
                            "match_score": round(match_score, 2),
                        }
                    )

        except Exception as e:
            logger.error(f"Semantic search with FAISS failed: {e}")

        # Step 2: Fallback to keyword search if semantic search yields no results
        if not output:
            logger.info("Falling back to keyword search")
            query_terms = query.requirements.lower().split()
            like_conditions = " OR ".join(
                [
                    "specs LIKE ?",
                    "name LIKE ?",
                    "company LIKE ?",
                    "product_type LIKE ?",
                ]
                * len(query_terms)
            )
            params = []
            for term in query_terms:
                pattern = f"%{term}%"
                params.extend([pattern, pattern, pattern, pattern])

            c.execute(
                f"SELECT * FROM products WHERE {like_conditions} LIMIT 10",
                params,
            )
            rows = c.fetchall()

            for row in rows:
                specs = (row["specs"] or "").lower()
                name = (row["name"] or "").lower()
                company = (row["company"] or "").lower()
                product_type = (row["product_type"] or "").lower()
                matched_terms = sum(
                    1
                    for term in query_terms
                    if term in specs
                    or term in name
                    or term in company
                    or term in product_type
                )
                match_score = min((matched_terms / len(query_terms)) * 100, 75.0)
                output.append(
                    {
                        "product_id": row["product_id"],
                        "company": row["company"],
                        "name": row["name"],
                        "product_type": row["product_type"],
                        "datasheet_path": row["datasheet_path"],
                        "directory": row["directory"],
                        "specs": (
                            row["specs"][:100] + "..." if row["specs"] else "No specs"
                        ),
                        "match_score": round(match_score, 2),
                    }
                )
            logger.info(f"Keyword search returned {len(output)} results")

        conn.close()
        if not output:
            logger.info("No matching products found for query")
            return {"products": []}

        logger.info(f"Returning {len(output)} matching products")
        return {
            "products": sorted(
                output,
                key=lambda x: x["match_score"],
                reverse=True,
            ),
        }

    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password",
        )

    expiration = datetime.now(timezone.utc) + timedelta(hours=1)
    to_encode = {"sub": form_data.username, "exp": expiration}
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    response = JSONResponse(content={"access_token": token, "token_type": "bearer"})
    logger.info(f"Token endpoint response headers: {response.headers}")
    return response


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)
