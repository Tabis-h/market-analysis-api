import asyncio
import time
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .config import settings
from .models import (
    SectorAnalysisResponse, ErrorResponse, HealthCheck, ApiKeyInfo
)
from .rate_limiter import limiter, cleanup_rate_limit_storage
from .data_collector import DataCollector
from .ai_analyzer import AIAnalyzer
from .auth import cleanup_expired_sessions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Background task reference
cleanup_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events"""
    global cleanup_task
    
    # Startup
    logger.info("Starting Market Analysis API...")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Gemini API configured: {bool(settings.GEMINI_API_KEY)}")
    
    # Start background cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    yield
    
    # Shutdown
    logger.info("Shutting down Market Analysis API...")
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

# Initialize FastAPI app with lifespan
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

def verify_api_key(request: Request):
    """Simple API key verification - supports multiple valid keys from header or query param"""
    # Try to get API key from header first, then from query parameter
    api_key = request.headers.get("x-api-key") or request.query_params.get("api_key")
    
    # Allow multiple valid API keys
    valid_api_keys = [
        settings.API_KEY,
        "demo-key-123",
        "guest-access-456", 
        "public-api-789"
    ]
    
    if not api_key or api_key not in valid_api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid or missing API Key. Use header 'x-api-key' or query parameter '?api_key=your-key'."
        )


# Initialize components
ai_analyzer = AIAnalyzer()


# In-memory cache for analysis results (simple caching)
analysis_cache = {}

async def periodic_cleanup():
    """Background task for periodic cleanup"""
    while True:
        try:
            cleanup_expired_sessions()
            cleanup_rate_limit_storage()
            # Clear old cache entries (older than 1 hour)
            current_time = time.time()
            expired_keys = [
                key for key, data in analysis_cache.items()
                if current_time - data.get('timestamp', 0) > 3600
            ]
            for key in expired_keys:
                del analysis_cache[key]
            
            await asyncio.sleep(300)  # Run every 5 minutes
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {str(e)}")
            await asyncio.sleep(300)

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with API information"""
    return """
    <html>
        <head>
            <title>Market Analysis API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px; }
                .section { margin: 20px 0; }
                .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .method { color: #007acc; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1 class="header">Market Analysis API</h1>
            <div class="section">
                <h2>Welcome to the Market Analysis API</h2>
                <p>This API provides comprehensive market analysis for various sectors in India.</p>
            </div>
            
            <div class="section">
                <h2>Available Endpoints:</h2>
                
                <div class="endpoint">
                    <span class="method">GET</span> <strong>/analyze/{sector}</strong><br>
                    Get market analysis for a specific sector (requires API key)
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <strong>/health</strong><br>
                    Check API health status
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <strong>/docs</strong><br>
                    Interactive API documentation
                </div>
            </div>
            
            <div class="section">
                <h2>Authentication:</h2>
                <p>This API uses simple API key authentication. You can provide the API key in two ways:</p>
                <p><strong>Method 1: Request Header</strong></p>
                <code>x-api-key: your-api-key-here</code>
                <p><strong>Method 2: URL Query Parameter (for browser testing)</strong></p>
                <code>?api_key=your-api-key-here</code>
                <p><strong>Demo API Keys:</strong></p>
                <ul>
                    <li><code>demo-key-123</code></li>
                    <li><code>guest-access-456</code></li>
                    <li><code>public-api-789</code></li>
                </ul>
            </div>
            
            <div class="section">
                <h2>Try it in your browser:</h2>
                <p>Click these links to test the API directly:</p>
                <ul>
                    <li><a href="/analyze/technology?api_key=demo-key-123" target="_blank">Technology Sector Analysis</a></li>
                    <li><a href="/analyze/pharmaceuticals?api_key=demo-key-123" target="_blank">Pharmaceuticals Analysis</a></li>
                    <li><a href="/analyze/banking?api_key=demo-key-123" target="_blank">Banking Sector Analysis</a></li>
                    <li><a href="/analyze/energy?api_key=demo-key-123" target="_blank">Energy Sector Analysis</a></li>
                </ul>
            </div>
            
            <div class="section">
                <h2>Supported Sectors:</h2>
                <p>pharmaceuticals, technology, banking, automotive, agriculture, energy, steel, cement, fmcg, telecom, and more...</p>
            </div>
        </body>
    </html>
    """

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint - no authentication required"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version=settings.APP_VERSION,
        gemini_api_configured=bool(settings.GEMINI_API_KEY)
    )

@app.get("/analyze/{sector}", response_model=SectorAnalysisResponse)
@limiter.limit("10/minute")
async def analyze_sector(
    sector: str,
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """
    Analyze a specific market sector and return comprehensive insights
    """
    start_time = time.time()
    
    try:
        # Validate sector input
        if not sector or len(sector.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sector name cannot be empty"
            )
        
        sector = sector.strip().lower()
        
        # Check rate limits
        # Check cache first
        cache_key = f"{sector}_anonymous"
        current_time = time.time()
        
        if cache_key in analysis_cache:
            cached_data = analysis_cache[cache_key]
            # Use cache if less than 30 minutes old
            if current_time - cached_data['timestamp'] < 1800:
                logger.info(f"Returning cached analysis for {sector}")
                return SectorAnalysisResponse(
                    sector=sector,
                    analysis_report=cached_data['report'],
                    timestamp=cached_data['created_at'],
                    data_sources=cached_data['data_sources'],
                    session_id=cached_data['session_id']
                )
        
        # Collect market data
        logger.info(f"Collecting data for sector: {sector}")
        async with DataCollector() as collector:
            sector_data = await collector.collect_sector_data(sector)
        
        if 'error' in sector_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error collecting market data: {sector_data['error']}"
            )
        
        # Generate AI analysis
        logger.info(f"Generating AI analysis for sector: {sector}")
        analysis_report = await ai_analyzer.analyze_sector_data(sector_data)
        
        if not analysis_report:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate analysis report"
            )
        
        # Create session ID for this analysis
        session_id = f"anonymous_{int(current_time)}"
        
        # Save analysis to markdown file
        try:
            # Get the project root directory (parent of app directory)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            markdown_dir = os.path.join(project_root, "markdown analysis report")
            
            # Create markdown directory if it doesn't exist
            os.makedirs(markdown_dir, exist_ok=True)
            
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_{sector}_{timestamp_str}.md"
            filepath = os.path.join(markdown_dir, filename)
            
            # Create markdown content
            markdown_content = f"# Market Analysis Report: {sector.title()} Sector\n\n"
            markdown_content += f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            markdown_content += f"**Session ID:** {session_id}\n"
            markdown_content += f"**Data Sources:** {sector_data.get('data_points', 0)}\n\n"
            markdown_content += "---\n\n"
            markdown_content += analysis_report
            
            # Write to file in markdown directory
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logger.info(f"Analysis report saved to {filepath}")
            
        except Exception as file_error:
            logger.error(f"Failed to save analysis to file: {str(file_error)}")
            # Don't raise exception - file saving failure shouldn't break the API response
        
        # Cache the result
        analysis_cache[cache_key] = {
            'report': analysis_report,
            'timestamp': current_time,
            'created_at': datetime.now().isoformat(),
            'data_sources': sector_data.get('data_points', 0),
            'session_id': session_id
        }
        
        processing_time = time.time() - start_time
        logger.info(f"Analysis completed for {sector} in {processing_time:.2f}s")
        
        return SectorAnalysisResponse(
            sector=sector,
            analysis_report=analysis_report,
            timestamp=datetime.now().isoformat(),
            data_sources=sector_data.get('data_points', 0),
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_sector: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=f"Status code: {exc.status_code}",
            timestamp=datetime.now().isoformat()
        ).model_dump()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if settings.DEBUG else "An unexpected error occurred",
            timestamp=datetime.now().isoformat()
        ).model_dump()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

