import sys
from app.mastra.rag import rag_manager

print("Testing RAG Query...")
results = rag_manager.query_sop_runbooks('database timeout')
print(f"Got {len(results)} results")
for r in results:
    print(f"Title: {r.get('title')}")
    print(f"Service: {r.get('service')}")
    print(f"Score: {r.get('score')}")
    print("-" * 20)
