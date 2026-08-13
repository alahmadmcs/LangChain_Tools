from sqlserver_tool import sqlserver_search


result = sqlserver_search.invoke(
    {
        "query": "SELECT TOP 5 * FROM [SalesLT].[Customer]"
    }
)

print(result)