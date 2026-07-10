import sys
import json
from app.mastra.rag import rag_manager

def run_test():
    qdrant = rag_manager.qdrant
    client = rag_manager.qdrant.client
    
    # 1. Collection stats
    collection_info = client.get_collection(rag_manager.qdrant.collection_name)
    points_count = collection_info.points_count
    
    print("--- QDRANT STATUS ---")
    print(f"Points Count: {points_count}")
    print(f"Vector Size: {collection_info.config.params.vectors.size}")
    
    queries = [
        "database timeout",
        "CrashLoopBackOff",
        "HTTP 500 payment API"
    ]
    
    for q in queries:
        print(f"\n--- QUERY: {q} ---")
        try:
            results = rag_manager.query_sop_runbooks(q, limit=3)
            for r in results:
                print(f"- Title/Service: {r.get('title') or r.get('service') or r.get('type')}")
                print(f"  Score: {r.get('score')}")
                print(f"  Source: {r.get('source', 'Unknown')}")
        except Exception as e:
            print(f"Error querying {q}: {str(e)}")

if __name__ == "__main__":
    run_test()
