Purchasing Base Unit
Overview
Purchasing Base Unit is a web application designed to manage and search product datasheets. It allows users to upload PDF datasheets, extract text, store product information in a SQLite database, and perform semantic searches using FAISS and HuggingFace embeddings. The application features user authentication, a responsive frontend, and a FastAPI backend.
Features

User Authentication: Secure login using JWT tokens (default credentials: admin/admin123).
Datasheet Upload: Upload PDF datasheets, extract text using PyMuPDF and OCR (via Tesseract), and store them in a database.
Semantic Search: Search products based on requirements using FAISS and HuggingFace embeddings, with a fallback to keyword search.
Product Management: Add, view, and download product datasheets.
Responsive UI: A clean, dark/light theme toggle interface built with HTML, Tailwind CSS, and JavaScript.
Filtering and Pagination: Filter search results by company, product type, and match score, with paginated results.

Tech Stack
Backend

Python 3.12: Programming language.
FastAPI: Web framework for the API.
SQLite: Database for storing product information.
FAISS: For vector-based semantic search.
HuggingFace Embeddings: all-MiniLM-L6-v2 model for text embeddings.
PyMuPDF (fitz): For PDF text extraction.
Tesseract OCR: Fallback for scanned PDFs.
passlib & bcrypt: For password hashing.
jose (PyJWT): For JWT token generation and validation.
Uvicorn: ASGI server for running FastAPI.

Frontend

HTML5 & JavaScript: For the client-side interface and logic.
Tailwind CSS: For styling (via PostCSS).
Webpack: For bundling JavaScript.
serve: For serving the frontend.

Prerequisites
Before setting up the project, ensure you have the following installed:

Python 3.12 (or higher): Download Python
Node.js 20.x (or higher) and npm: Download Node.js
Tesseract OCR: Required for scanned PDF text extraction.
Windows: Download and install from Tesseract at UB Mannheim. Add Tesseract to your PATH (e.g., C:\Program Files\Tesseract-OCR).


Git: For cloning the repository (optional).

Project Structure
Purchasing-Base-Unit/
├── Client/                     # Frontend files
│   ├── dist/                   # Bundled JavaScript (generated)
│   │   └── bundle.js
│   ├── index.html              # Main HTML file
│   ├── logo.png                # Logo image
│   ├── styles.css              # Compiled CSS (generated)
│   └── main.js                 # JavaScript logic
├── DataSheets/                 # Directory for storing PDF datasheets
│   └── Uploaded/               # Subdirectory for uploaded PDFs
├── Server/                     # Backend files
│   ├── database.sqlite         # SQLite database (generated)
│   ├── faiss_index/            # FAISS index files (generated)
│   ├── logs/                   # Log files
│   │   └── extracted_text.log
│   ├── favicon.ico             # Favicon for the backend
│   └── main.py                 # FastAPI backend
├── src/                        # Source files for frontend assets
│   └── input.css               # Tailwind CSS input file
├── package.json                # Node.js dependencies and scripts
├── postcss.config.js           # PostCSS configuration
├── webpack.config.js           # Webpack configuration
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation (this file)

Setup Instructions
Step 1: Clone the Repository (Optional)
If you’re starting fresh, clone the repository (or skip this if you already have the project files):
git clone <repository-url>
cd Purchasing-Base-Unit

Step 2: Set Up the Backend

Create a Virtual Environment:
python -m venv venv


On Windows, activate the virtual environment:venv\Scripts\activate


On macOS/Linux:source venv/bin/activate




Install Python Dependencies:Create a requirements.txt file with the following content (or use the one provided if it exists):
fastapi==0.115.2
uvicorn==0.32.0
sqlite3
faiss-cpu==1.9.0
pymupdf==1.24.11
numpy==1.26.4
psutil==6.1.0
pytesseract==0.3.13
pillow==11.0.0
python-jose==3.3.0
passlib==1.7.4
bcrypt==4.0.1
langchain-community==0.3.3
huggingface_hub==0.26.1
sentence-transformers==3.2.0
black==25.1.0

Install the dependencies:
pip install -r requirements.txt


Install Tesseract OCR (if not already installed):

Ensure Tesseract is installed and added to your PATH (see Prerequisites).
Verify installation:tesseract --version




Format the Backend Code with black:Run black to format the Python code for consistency:
black Server/main.py


Expected output:reformatted Server\main.py
All done! ✨ 🍰 ✨
1 file reformatted.


If the file is already formatted, it will show:All done! ✨ 🍰 ✨
1 file left unchanged.




Create Necessary Directories:Ensure the following directories exist:
mkdir DataSheets\Uploaded
mkdir Server\logs
mkdir Server\faiss_index



Step 3: Set Up the Frontend

Install Node.js Dependencies:Navigate to the project root and install the required npm packages:
npm install

Ensure package.json includes the following dependencies and scripts (create or update if necessary):
{
  "name": "purchasing-base-unit",
  "version": "1.0.0",
  "scripts": {
    "start": "serve Client -p 8080",
    "build:css": "postcss src/input.css -o Client/styles.css",
    "watch:css": "postcss src/input.css -o Client/styles.css --watch",
    "build:js": "webpack --config webpack.config.js"
  },
  "devDependencies": {
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.47",
    "postcss-cli": "^11.0.0",
    "serve": "^14.2.3",
    "tailwindcss": "^3.4.14",
    "webpack": "^5.95.0",
    "webpack-cli": "^5.1.4"
  }
}


Build the CSS:Compile the Tailwind CSS:
npm run build:css


This generates Client/styles.css.


Build the JavaScript:Bundle the JavaScript using Webpack:
npm run build:js


This generates Client/dist/bundle.js.


Create a Dummy File to Silence Chrome DevTools Warning (Optional):To prevent a harmless 404 error for /.well-known/appspecific/com.chrome.devtools.json:
mkdir Client\.well-known\appspecific
echo {} > Client\.well-known\appspecific\com.chrome.devtools.json



Step 4: Run the Development Servers

Start the Backend Server:In the activated virtual environment:
python Server\main.py


Expected output:INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:3000 (Press CTRL+C to quit)


The backend will run on http://localhost:3000.


Start the Frontend Server:In a new terminal (or after opening a new command prompt in the project directory):
npm start


Expected output:Serving!
├─ Local:    http://localhost:8080
├─ Network:  http://192.168.x.x:8080
└ Copied local address to clipboard!


The frontend will run on http://localhost:8080.



Step 5: Test the Application

Access the App:

Open your browser and go to http://localhost:8080.


Log In:

Use the default credentials:Username: admin
Password: admin123


After logging in, you’ll see the main interface.


Test Features:

Search Products: Enter a query (e.g., “camera”) in the search bar and click “Search”.
Upload a Datasheet: Upload a PDF datasheet using the upload form.
Add a Product: Fill out the form to add a new product manually.
Download a Datasheet: Click “Download Datasheet” on a search result.
Apply Filters: Toggle the theme, apply filters, and test pagination.



Development Notes

Formatting Code:
Always run black on main.py after making changes to ensure consistent formatting:black Server/main.py




Rebuilding Frontend Assets:
After modifying main.js, rebuild the bundle:npm run build:js


After modifying src/input.css, rebuild the CSS:npm run build:css





Security Recommendations

Change the SECRET_KEY:

The default SECRET_KEY in Server/main.py is insecure:SECRET_KEY = "your-secret-key-please-change-this"


Generate a secure key:python -c "import secrets; print(secrets.token_hex(32))"


Replace the SECRET_KEY value in main.py with the generated key. After changing it, all existing tokens will be invalid, so users will need to log in again.


HTTPS in Production:

For production, configure HTTPS using a reverse proxy like Nginx and obtain an SSL certificate (e.g., via Let’s Encrypt).


Environment Variables:

Store sensitive data like SECRET_KEY in environment variables instead of hardcoding them in main.py.



Troubleshooting

CORS Errors:
Ensure the allow_origins list in main.py includes your frontend URL (http://localhost:8080).


401 Unauthorized Errors:
If you encounter session expired errors, log out, clear localStorage in your browser, and log in again:localStorage.removeItem("token");




Memory Issues with FAISS:
Monitor memory usage in the logs (Server/logs/extracted_text.log). Adjust the FAISS batch size in main.py (faiss_batch_size = 100) if needed.



Future Improvements

Add user registration and password reset functionality.
Implement rate limiting on API endpoints.
Add more advanced search filters and sorting options.
Optimize FAISS indexing for larger datasets.
Add support for other file formats (e.g., DOCX).

Acknowledgments

Built with ❤️ using FastAPI, FAISS, and HuggingFace libraries.

