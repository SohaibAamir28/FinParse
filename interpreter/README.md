# Open Interpreter Setup & Run Guide

This project contains test configurations and scripts for running Open Interpreter with different LLM backends (Ollama, Gemini, Hugging Face Serverless API) and virtual environment setups.

## 🛠️ Prerequisites

*   Python 3.12 (installed on your system path)
*   Access to terminal (PowerShell or CMD)

---

## ⚙️ Setup Instructions

Follow these steps to set up the Python virtual environment and install the correct dependencies.

### 1. Create & Activate Virtual Environment
Open your terminal in the `interpreter` directory and run:

```powershell
# Create the virtual environment
python -m venv myenv

# Activate it (PowerShell)
.\myenv\Scripts\Activate.ps1

# Activate it (CMD)
.\myenv\Scripts\activate.bat
```

### 2. Fix Dependency Conflicts (CRITICAL)
Older installations of `open-interpreter` or Python 3.12 environments can suffer from broken vendorized packages inside `setuptools`. Run this command to install the correct stable version of `setuptools` to fix `ImportError: cannot import name 'six' from 'pkg_resources.extern'`:

```powershell
pip install setuptools==69.5.1
```

### 3. Install Open Interpreter & Libraries
Install the core packages inside the virtual environment:

```powershell
pip install open-interpreter pandas numpy
```

### 4. Setup Jupyter Kernel Dependencies (For Code Execution)
Open Interpreter runs code blocks inside a Jupyter Python kernel. By default, it falls back to the system's global Python kernel. To ensure it has access to data processing packages like `pandas` and `numpy` during code execution, install them in the global Python environment:

```powershell
# Run this outside the virtual environment, or specify the global python path
python -m pip install pandas numpy
```

---

## 🚀 Running the Project

### A. Run Open Interpreter CLI
To run Open Interpreter locally in interactive mode:

```powershell
# Run the local interpreter CLI
interpreter --local
```

### B. Run Test Scripts
You can run the pre-configured scripts inside `myenv` to execute specific prompts:

#### 1. Gemini / Hugging Face Test (`test_huggingface.py`)
This script executes custom prompts to load, calculate, and save CSV statistics using Gemini/Hugging Face:

```powershell
python test_huggingface.py
```

#### 2. Local Ollama Test (`check.py`)
This script is pre-configured to run with local models running on Ollama:

```powershell
python check.py
```
*(Make sure Ollama is running locally on port `11434` before executing)*
