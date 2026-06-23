# FinParse: Financial Statement Parser & Reconciliation Engine

FinParse is a hybrid local application built to solve layout misalignment, shifted data columns, and mathematical hallucinations in messy financial bank statements (PDFs and CSVs). It parses coordinate-aligned transaction lines, runs verification balance checks on every row, and outputs styled, executive-ready Excel files with KPI summaries and categorized dashboards.

---

## 📊 The Open-Source Benchmarks (For Financial Analysis)

| Tool | UI Style | Strengths for Messy Financials | Weaknesses | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **Open Interpreter** | Terminal / CLI | **Excellent**. It writes local Python code (`pandas`, `openpyxl`) to dynamically parse, shift columns, fix formats, and reconstruct clean Excel files. | Runs directly on your machine (can modify files outside your project if not careful). | Automating Excel data cleaning & immediate plotting. |
| **OpenHands** | Web Browser / GUI | **Heavy-duty**. Uses a sandboxed Docker container to execute code safely. Can run complex data pipelines. | Overkill for single files. It is designed more for building large multi-file apps than quickly editing a single spreadsheet. | Enterprise-grade, highly secure automated workflows. |
| **Aider** | Terminal / CLI | Best for writing clean code infrastructure, integrating with Git, and maintaining data-parsing scripts. | Not designed for "conversational data analysis." It won’t auto-view a PDF or chart it dynamically on screen for you. | Writing reusable scripts to format bank statements. |

---

## 🛠️ The Winning Architecture

To clean poorly formatted bank statements and export clean data to Excel, relying solely on text-prompt LLM generation is unreliable as language models frequently hallucinate arithmetic sums. This system implements a **hybrid code approach** combining code execution with local heuristics and manual UI editing:

```
[Messy Statement PDF/CSV] 
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ 1. Coordinate-Based Text Extraction & Column Alignment │ (parser.py)
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ 2. Mathematical Reconciliation Rule Checks             │ (reconciler.py)
│    Starting Balance - Debits + Credits == Balance      │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ 3. Interactive UI Cell Edits & Manual Auditing         │ (static dashboard)
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ 4. Executive-Grade Excel & Pivot Dashboards            │ (exporter.py)
└────────────────────────────────────────────────────────┘
```

1. **Extract Text & Auto-Align Columns:**
   Using `pdfplumber`, text segments are extracted from the document along with their horizontal and vertical boundaries. Words are grouped into lines and assigned to columns matching the spatial layout coordinates of the detected headers. Date formats are standardized and multi-line wrapped transaction descriptions are merged.
2. **Apply Financial Rules (Reconciliation):**
   The reconciler evaluates each row:
   $$\text{Expected Balance}_{i} = \text{Balance}_{i-1} - \text{Debit}_{i} + \text{Credit}_{i}$$
   (or signs reversed, auto-detected for credit card statements). Discrepancies are flagged line-by-line in red, allowing immediate visual debugging.
3. **Generate a Structured Excel File:**
   Outputs the validated dataframe into a styled spreadsheet:
   - Navy blue headers with white text, light gray alternating stripes, and active gridlines.
   - Float values formatted as currency symbols (`$#,##0.00`).
   - A secondary **Summary Dashboard** sheet containing KPIs (Starting/Ending Balances, Cash Flow) and a category-wise spend table.

---

## 💻 Local Setup & Execution Guide

### Prerequisites
- Python 3.10 to 3.14
- Operating System: Windows / macOS / Linux

### 1. Initialize the Environment
Clone or navigate to the workspace directory and set up a Python virtual environment:
```bash
# Navigate to project
cd e:\NCAI\open-interpreter

# Create a virtual environment
python -m venv venv

# Activate the virtual environment (Windows Powershell)
.\venv\Scripts\Activate.ps1

# Activate the virtual environment (macOS/Linux)
source venv/bin/activate
```

### 2. Install Project Dependencies
Install the required packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 3. Run the Verification Test Suite
Verify that the parsing heuristics and reconciliation algebra work correctly by running the simulator:
```bash
python verify_parsing.py
```
This generates a mock messy CSV file, parses the wrapped columns, verifies the math discrepancy on an `AMAZON` row, and exports a styled sheet to `reconciled_mock_statement.xlsx`.

### 4. Start the Web Server
Launch the FastAPI server:
```bash
python main.py
```
Uvicorn will start running locally at **`http://127.0.0.1:8080`**.

---

## 🖥️ Using the Web Interface

1. Open your browser and navigate to **`http://127.0.0.1:8080`**.
2. **Ingest Statement**: Drag and drop the generated `sample_statement.csv` file from your project folder (or upload any real bank statement PDF/CSV).
3. **Audit Results**: View the parsed transactions list. Cell items in the Date, Description, Debits, Credits, and Balance columns can be edited directly by clicking inside them.
4. **Reconcile**: Any rows that do not balance are highlighted in red. You can add missing rows or correct transaction values, then click **Re-Calculate Math** to execute on-the-fly reconciliation checks.
5. **Download Export**: Click **Export to Excel** to download the clean, styled workbook.

---

## 📁 Code Repository Map

- [requirements.txt](file:///e:/NCAI/open-interpreter/requirements.txt): Library dependencies.
- [parser.py](file:///e:/NCAI/open-interpreter/parser.py): PDF spatial word extraction and CSV schema classification.
- [reconciler.py](file:///e:/NCAI/open-interpreter/reconciler.py): Balance formula validation engine.
- [exporter.py](file:///e:/NCAI/open-interpreter/exporter.py): Styled Openpyxl sheet writer.
- [main.py](file:///e:/NCAI/open-interpreter/main.py): FastAPI backend routes.
- [static/index.html](file:///e:/NCAI/open-interpreter/static/index.html): HTML web template.
- [static/style.css](file:///e:/NCAI/open-interpreter/static/style.css): Dark glassmorphic aesthetic stylesheet.
- [static/app.js](file:///e:/NCAI/open-interpreter/static/app.js): SPA interactive state manager.
