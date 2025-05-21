class QueryExecutor:
    def execute(self, query: str) -> dict:
        print(f"Executing query: {query}")
        return {"result": f"Mock result of: {query}"}

query_executor = QueryExecutor()