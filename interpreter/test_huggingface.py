# from interpreter import interpreter

from interpreter import interpreter

interpreter.auto_run = True

interpreter.system_message += """
IMPORTANT:
- Be extremely brief and concise.
- Write minimal Python code without any comments.
- Do not write verbose explanations or introductions.
- Keep output extremely short to prevent Hugging Face token limit truncation.
- Always implement the requested number of columns and data rows precisely.
"""


interpreter.auto_run = True
interpreter.display = False

# interpreter.llm.model = "gemini/gemini-1.5-flash"
interpreter.llm.model = "gemini/gemini-1.5-flash-latest"
interpreter.llm.api_key = ""

interpreter.context_window = 8192
interpreter.max_tokens = 1024

# interpreter.llm.model = "groq/llama-3.1-8b-instant"
# interpreter.llm.api_key = ""

# interpreter.llm.model = "huggingface/google/gemma-3-4b-it"
# model="mistralai/Mistral-7B-Instruct-v0.3"
# interpreter.llm.api_key = ""
# interpreter.llm.api_base = "https://api-inference.huggingface.co/models"

# interpreter.context_window = 8192
# interpreter.max_tokens = 2048

# interpreter.chat("""
# If math.csv does not exist, create it with columns A,B,C,D and 50 rows of random integers (1-100).

# Then read math.csv using pandas.

# For each row compute:

# Pair-wise:
# - Mean_AB = (A + B) / 2
# - Median_AB = median of A and B
# - Mode_CD = mode of C and D (if tie, take first value)
# - Average_CD = (C + D) / 2

# Full row stats (A,B,C,D):
# - Row_Mean = mean of A,B,C,D
# - Row_Median = median of A,B,C,D
# - Row_Mode = most frequent value in row (if tie, first)

# Add all columns to dataframe.

# Save as processed_data.csv.

# Finally print:
# - first 10 rows
# - number of rows
# - summary statistics
# """)


interpreter.chat("""
Read math.csv.

For each row compute:
- Sum_AB = A + B
- Diff_CD = C - D
- Product_AB = A * B

Add these columns to the dataframe.

Save as processed_data.csv.

Show first 5 rows only.
""")