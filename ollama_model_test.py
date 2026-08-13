from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="mistralai:latest",
    base_url="http://localhost:11434",
    temperature=0,
)

response = llm.invoke("Write a SQL query to find absent employees.")
print(response.content)