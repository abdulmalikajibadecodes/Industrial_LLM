from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import uvicorn
from rag_system import IndustrialRAGSystem
import os
import logging
import pandas as pd


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Industrial LLM Insight API",
    description="RAG-powered insights for industrial equipment maintenance",
    version="1.0.0"
)

# Request/Response models
class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

class AnomalyRequest(BaseModel):
    equipment_id: str
    anomaly_type: str
    severity: Optional[str] = "WARNING"

class InsightResponse(BaseModel):
    query: str
    insight: str
    relevant_logs: List[Dict]
    timestamp: str

# Global RAG system instance
rag_system = None

@app.on_event("startup")
async def startup_event():
    """Initialize RAG system on startup"""
    global rag_system
    logger.info("Initializing RAG system...")
    
    try:
        rag_system = IndustrialRAGSystem()
        
        # Load data (check multiple possible locations)
        data_paths = [r'C:\Users\USER\Desktop\DATA SCIENCE\Industrial_llm\data\industrial_logs.csv', 
                      "industrial_logs.csv","data\industrial_logs.csv",
                      "/app/data/industrial_logs.csv", 
                      "./data/industrial_logs.csv"                      
                       ]
        data_loaded = False
        
        for path in data_paths:
            if os.path.exists(path):
                rag_system.load_and_index_logs(path)
                logger.info(f"Data loaded from {path}")
                data_loaded = True
                break
        
        if not data_loaded:
            logger.warning("No data file found. System will run with empty index.")
            
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {str(e)}")
        raise

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Industrial LLM Insight API",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "rag_system_initialized": rag_system is not None,
        "timestamp": pd.Timestamp.now().isoformat()
    }

@app.post("/query", response_model=InsightResponse)
async def query_logs(request: QueryRequest):
    """Query industrial logs for insights"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        result = rag_system.query_system(request.query)
        return InsightResponse(**result)
    
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@app.post("/analyze_anomaly", response_model=InsightResponse)
async def analyze_anomaly(request: AnomalyRequest):
    """Analyze specific equipment anomaly"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    # Convert anomaly to natural language query
    query = f"{request.equipment_id} {request.anomaly_type} {request.severity}"
    
    try:
        result = rag_system.query_system(query)
        result['query'] = f"Anomaly analysis for {request.equipment_id}: {request.anomaly_type}"
        return InsightResponse(**result)
    
    except Exception as e:
        logger.error(f"Anomaly analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Anomaly analysis failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)