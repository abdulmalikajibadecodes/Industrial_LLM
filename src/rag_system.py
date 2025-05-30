import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from transformers import pipeline
import torch
from typing import List, Dict
import json

class IndustrialRAGSystem:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """Initialize RAG system with embedding model and LLM"""
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer(model_name)
        
        print("Initializing vector database...")
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.create_collection(
            name="industrial_logs",
            metadata={"hnsw:space": "cosine"}
        )
        
        print("Loading LLM for generation...")
        # Use a lightweight model for local testing
        self.llm = pipeline(
            "text-generation",
            model="microsoft/DialoGPT-medium",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device=0 if torch.cuda.is_available() else -1
        )
        
    def load_and_index_logs(self, csv_path: str):
        """Load logs and create embeddings"""
        print(f"Loading logs from {csv_path}...")
        df = pd.read_csv(csv_path)
        
        # Create searchable text combining relevant fields
        df['searchable_text'] = df.apply(
            lambda row: f"{row['equipment_id']} {row['equipment_type']} {row['severity']} {row['message']}", 
            axis=1
        )
        
        print("Creating embeddings...")
        embeddings = self.embedding_model.encode(df['searchable_text'].tolist())
        
        print("Storing in vector database...")
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=df['searchable_text'].tolist(),
            metadatas=df.to_dict('records'),
            ids=[str(i) for i in range(len(df))]
        )
        
        print(f"Indexed {len(df)} log entries")
        
    def retrieve_relevant_logs(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve most relevant logs for a query"""
        query_embedding = self.embedding_model.encode([query])
        
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=top_k
        )
        
        return results['metadatas'][0] if results['metadatas'] else []
    
    def generate_insight(self, query: str, context_logs: List[Dict]) -> str:
        """Generate insight based on query and retrieved logs"""
        
        # Format context
        context = "\n".join([
            f"- {log['timestamp']}: {log['message']}" 
            for log in context_logs[:3]  # Use top 3 most relevant
        ])
        
        prompt = f"""Based on the following industrial equipment logs, provide a concise analysis:

Query: {query}

Relevant Log Entries:
{context}

Analysis:"""
        
        # For demo purposes, create a simple rule-based response
        # In production, you'd use a more sophisticated LLM
        if any('temperature' in log['message'].lower() for log in context_logs):
            analysis = "Temperature anomaly detected. Recommend immediate inspection of cooling systems and thermal sensors."
        elif any('vibration' in log['message'].lower() for log in context_logs):
            analysis = "Vibration patterns suggest mechanical wear. Schedule bearing inspection and lubrication check."
        elif any('pressure' in log['message'].lower() for log in context_logs):
            analysis = "Pressure variations detected. Check for leaks, blockages, or pump performance issues."
        else:
            analysis = "Multiple equipment events detected. Recommend comprehensive system review."
            
        return analysis
    
    def query_system(self, query: str) -> Dict:
        """Main query interface"""
        print(f"Processing query: {query}")
        
        # Retrieve relevant logs
        relevant_logs = self.retrieve_relevant_logs(query)
        
        if not relevant_logs:
            return {
                "query": query,
                "relevant_logs": [],
                "insight": "No relevant logs found for this query."
            }
        
        # Generate insight
        insight = self.generate_insight(query, relevant_logs)
        
        return {
            "query": query,
            "relevant_logs": relevant_logs,
            "insight": insight,
            "timestamp": pd.Timestamp.now().isoformat()
        }

# Test the system
if __name__ == "__main__":
    rag = IndustrialRAGSystem()
    rag.load_and_index_logs(r"C:\Users\USER\Desktop\DATA SCIENCE\Industrial_llm\data\industrial_logs.csv")
    
    # Test queries
    test_queries = [
        "What's wrong with pump_01?",
        "Recent temperature issues",
        "Bearing problems in motors",
        "pump_03 performance"
    ]
    
    for query in test_queries:
        result = rag.query_system(query)
        print(f"\nQuery: {result['query']}")
        print(f"Insight: {result['insight']}")
        print("-" * 50)