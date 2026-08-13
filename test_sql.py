import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

server = os.getenv("SQLSERVER_SERVER")
database = os.getenv("SQLSERVER_DATABASE")
username = os.getenv("SQLSERVER_USERNAME")
password = os.getenv("SQLSERVER_PASSWORD")
driver = os.getenv("SQLSERVER_DRIVER")

connection_string = (
    f"DRIVER={{{driver}}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    f"TrustServerCertificate=yes;"
)

print("Connecting to:")
print(server)
print(database)
print(username)
print(driver)

try:

    conn = pyodbc.connect(
        connection_string
    )

    print(
        "✅ SQL Server connection successful!"
    )

    cursor = conn.cursor()

    cursor.execute(
        "SELECT @@VERSION"
    )

    row = cursor.fetchone()

    print(row[0])

    conn.close()

except Exception as e:

    print(
        "❌ SQL Server connection failed:"
    )

    print(e)