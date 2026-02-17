from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import tempfile

# Local imports
from config import config
from rag_engine_simple import get_simple_rag_engine, QueryResult

# Initialize FastAPI app
app = FastAPI(
    title="ConstitutionBD API (Simple)",
    description="RAG-powered Bangladesh Constitution Query System (Simplified)",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class QueryRequest(BaseModel):
    question: str
    include_sources: bool = True

class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[Dict] = []
    verified_citations: List[str] = []
    cross_references: List[str] = []
    confidence: str

class SearchRequest(BaseModel):
    query: str
    k: int = 5

class HealthResponse(BaseModel):
    status: str
    documents_loaded: bool
    llm_available: bool
    message: Optional[str] = None

class IngestResponse(BaseModel):
    success: bool
    message: str
    documents_processed: Optional[int] = None

# Global RAG engine instance
rag = None

@app.on_event("startup")
async def startup_event():
    """Initialize RAG engine on server startup"""
    global rag
    try:
        rag = get_simple_rag_engine()
        print("✅ Simple RAG engine initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize RAG engine: {e}")
        rag = None

def get_rag():
    """Dependency to get RAG engine"""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    return rag

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "ConstitutionBD API (Simple) - RAG-powered Bangladesh Constitution Query System",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "query": "/query",
            "search": "/search",
            "ingest": "/ingest",
            "ingest_from_path": "/ingest-from-path"
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check(rag_engine=Depends(get_rag)):
    """Check system health and status"""
    try:
        documents_loaded = len(rag_engine.documents) > 0
        llm_available = rag_engine.llm_available
        
        if documents_loaded:
            message = "All systems operational"
        else:
            message = "Documents not loaded - need to ingest constitution"
        
        return HealthResponse(
            status="healthy" if documents_loaded else "degraded",
            documents_loaded=documents_loaded,
            llm_available=llm_available,
            message=message
        )
        
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            documents_loaded=False,
            llm_available=False,
            message=f"Health check failed: {str(e)}"
        )

@app.post("/query", response_model=QueryResponse)
async def query_constitution(request: QueryRequest, rag_engine=Depends(get_rag)):
    """Query the constitution with a natural language question"""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        result: QueryResult = rag_engine.query(request.question)
        
        response = QueryResponse(
            question=request.question,
            answer=result.answer,
            sources=result.sources if request.include_sources else [],
            verified_citations=result.verified_citations,
            cross_references=result.cross_references,
            confidence=result.confidence
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@app.post("/search")
async def search_articles(request: SearchRequest, rag_engine=Depends(get_rag)):
    """Search for similar articles using keyword search"""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    
    if request.k < 1 or request.k > 20:
        raise HTTPException(status_code=400, detail="k must be between 1 and 20")
    
    try:
        results = rag_engine.search_articles(request.query, k=request.k)
        return {
            "query": request.query,
            "k": request.k,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/ingest", response_model=IngestResponse)
async def ingest_constitution(file: UploadFile = File(...), rag_engine=Depends(get_rag)):
    """Ingest constitution from uploaded file"""
    # Validate file type
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.txt') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Ingest the file
            success = rag_engine.ingest_constitution(temp_file_path)
            
            if success:
                doc_count = len(rag_engine.documents)
                
                return IngestResponse(
                    success=True,
                    message="Constitution ingested successfully",
                    documents_processed=doc_count
                )
            else:
                return IngestResponse(
                    success=False,
                    message="Failed to ingest constitution"
                )
                
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/ingest-from-path", response_model=IngestResponse)
async def ingest_from_path(file_path: str, rag_engine=Depends(get_rag)):
    """Ingest constitution from file path"""
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    
    if not file_path.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")
    
    try:
        success = rag_engine.ingest_constitution(file_path)
        
        if success:
            doc_count = len(rag_engine.documents)
            
            return IngestResponse(
                success=True,
                message="Constitution ingested successfully from file path",
                documents_processed=doc_count
            )
        else:
            return IngestResponse(
                success=False,
                message="Failed to ingest constitution from file path"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.get("/stats")
async def get_system_stats(rag_engine=Depends(get_rag)):
    """Get system statistics"""
    try:
        stats = {
            "documents_loaded": len(rag_engine.documents),
            "articles_indexed": len(rag_engine.article_index),
            "llm_available": rag_engine.llm_available,
            "llm_provider": config.LLM_PROVIDER,
            "storage_type": "JSON file storage"
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "details": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
