from interpreter import interpreter

interpreter.offline = True
interpreter.llm.model = "ollama/codestral"
interpreter.llm.api_base = "http://localhost:11434"

interpreter.chat("write a python code to make a calculator that add, subtract, multiply and divide and run it")

# from groq import Groq
# import os

# client = Groq(
#     api_key=os.environ.get("GROQ_API_KEY")
# )

# response = client.chat.completions.create(
#     model="llama3-70b-8192",
#     messages=[
#         {"role": "user", "content": "Hello, explain AI in simple words"}
#     ]
# )

# print(response.choices[0].message.content)