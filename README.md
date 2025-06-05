# Purchasing Base Unit

A production‑ready web application for managing and semantically searching product datasheets.

[![Render](https://img.shields.io/badge/Deployed%20on-Render-46b1ff?logo=render\&logoColor=white)](https://purchasing-base-unit-deploy.onrender.com)

---

## 🚀 Live Demo

▶️ **Frontend + API**: [https://purchasing-base-unit-deploy.onrender.com](https://purchasing-base-unit-deploy.onrender.com)

> The Render instance runs the latest version from the `main` branch.

---

## 📖 Overview

Purchasing Base Unit (PBU) lets engineering and procurement teams upload PDF datasheets, extract their text, index the content with embeddings, and perform lightning‑fast semantic searches.  It combines a **FastAPI** backend, **Tailwind/JS** frontend, and **FAISS** similarity search to deliver an end‑to‑end datasheet experience.

---

## ✨ Features

| Category             | Details                                                                                              |
| -------------------- | ---------------------------------------------------------------------------------------------------- |
| **User Auth**        | Secure login with **JWT** (default `admin / admin123`)                                               |
| **Datasheet Upload** | • Drag‑and‑drop PDFs<br>• Text extraction via **PyMuPDF**<br>• Automatic OCR fallback with Tesseract |
| **Semantic Search**  | • **HuggingFace** `all‑MiniLM‑L6‑v2` embeddings<br>• **FAISS** vector index<br>• Keyword fallback    |
| **Product Mgmt**     | CRUD operations, download original PDFs                                                              |
| **UI/UX**            | Dark/light toggle, responsive layout, filtering, pagination                                          |

---

## 🛠️ Tech Stack

### Backend

* **Python 3.12**
* **FastAPI** & **Uvicorn**
* **SQLite** (simple demo DB — swap for Postgres in prod)
* **FAISS** + **sentence‑transformers**
* **PyMuPDF**, **pytesseract**
* **python‑jose**, **passlib / bcrypt** for JWT + hashing

### Frontend

* **HTML / JS** (no framework)
* **Tailwind CSS** (compiled with PostCSS)
* **Webpack** for bundling
* **serve** for the dev server

---

## 📂 Project Structure

```text
Purchasing-Base-Unit/
├── Client/                 # Built frontend assets
│   ├── dist/               # Webpack bundle
│   │   └── bundle.js
│   ├── index.html
│   ├── logo.png
│   ├── styles.css
│   └── main.js
├── DataSheets/
│   └── Uploaded/           # User PDFs
├── Server/
│   ├── database.sqlite
│   ├── faiss_index/
│   ├── logs/
│   │   └── extracted_text.log
│   ├── favicon.ico
│   └── main.py
├── src/                    # Tailwind source
│   └── input.css
├── package.json
├── postcss.config.js
├── webpack.config.js
├── requirements.txt
└── README.md
```

---

## 🖥️ Local Setup

> **Prerequisites**
> • Python ≥ 3.12  │  • Node.js ≥ 20  │  • Tesseract OCR  │  • (Optional) Git

### 1 ‒ Clone & create venv

```bash
git clone <repository‑url>
cd Purchasing-Base-Unit
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2 ‒ Install backend deps

```bash
pip install -r requirements.txt
```

### 3 ‒ Install frontend deps & build assets

```bash
npm install
npm run build:css   # Tailwind → CSS
npm run build:js    # Webpack  → bundle
```

### 4 ‒ Create folders

```bash
mkdir -p DataSheets/Uploaded Server/logs Server/faiss_index
```

### 5 ‒ Run dev servers

```bash
# backend (port 3000)
python Server/main.py

# frontend (port 8080)
npm start
```

Open [http://localhost:8080](http://localhost:8080) and log in with `admin / admin123`.

---

## 🏗️ Deploying to Render (✏️ already done)

The app is containerised via **Docker**; Render simply runs the image and injects `$PORT`.

1. Push code to GitHub.
2. Create a **Web Service → Docker** on Render.
3. Leave *Build* & *Start* commands empty (Dockerfile handles them).
4. Add environment vars (e.g. `SECRET_KEY`).
5. Deploy.  Logs will show `Listening at: 0.0.0.0:10000` when live.

---

## 📝 Development Notes

* **Formatting**: `black Server/main.py`
* **Rebuild CSS**: `npm run build:css`
* **Rebuild JS**:  `npm run build:js`
* **FAISS batch size**: tweak `faiss_batch_size` in `Server/main.py` if RAM spikes.

---

## 🔒 Security

| Practice       | Action                                                                    |
| -------------- | ------------------------------------------------------------------------- |
| **Secret Key** | Replace default in `main.py` or set `SECRET_KEY` env var.                 |
| **HTTPS**      | Terminate TLS at Render or use Nginx + Let’s Encrypt in self‑hosted prod. |
| **CORS**       | Update `allow_origins` in `main.py` for non‑localhost frontends.          |

---

## 🐞 Troubleshooting

| Problem              | Fix                                                                 |
| -------------------- | ------------------------------------------------------------------- |
| **401 Unauthorized** | `localStorage.removeItem("token");` then re‑login.                  |
| **CORS error**       | Ensure backend `allow_origins` matches frontend URL.                |
| **High memory**      | Lower `faiss_batch_size`; monitor `Server/logs/extracted_text.log`. |

---

## 🌱 Roadmap / Future Work

* Self‑service user registration & password reset
* Rate‑limiting on public APIs
* Advanced sort / filter in search UI
* Postgres support & Alembic migrations
* Additional file formats (DOCX, XLSX)
* Background job queue for heavy OCR

---

## ❤️ Acknowledgements

Built with **FastAPI**, **FAISS**, **HuggingFace** .



