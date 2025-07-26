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
    """Beautiful professional homepage for the Market Analysis API"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Market Analysis API - AI-Powered Market Intelligence</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            
            .header {
                text-align: center;
                color: white;
                margin-bottom: 50px;
                padding: 40px 0;
            }
            
            .header h1 {
                font-size: 3rem;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            
            .header p {
                font-size: 1.2rem;
                opacity: 0.9;
            }
            
            .main-content {
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                margin-bottom: 30px;
            }
            
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 30px;
                margin: 40px 0;
            }
            
            .feature-card {
                background: #f8f9ff;
                padding: 30px;
                border-radius: 15px;
                text-align: center;
                border: 2px solid #e1e5ff;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            
            .feature-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 30px rgba(0,0,0,0.1);
            }
            
            .feature-icon {
                font-size: 3rem;
                color: #667eea;
                margin-bottom: 20px;
            }
            
            .feature-card h3 {
                color: #333;
                margin-bottom: 15px;
                font-size: 1.3rem;
            }
            
            .cta-section {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                border-radius: 15px;
                text-align: center;
                margin: 40px 0;
            }
            
            .cta-buttons {
                display: flex;
                justify-content: center;
                gap: 20px;
                flex-wrap: wrap;
                margin-top: 30px;
            }
            
            .btn {
                padding: 15px 30px;
                border: none;
                border-radius: 8px;
                text-decoration: none;
                font-weight: bold;
                font-size: 1rem;
                transition: all 0.3s ease;
                display: inline-flex;
                align-items: center;
                gap: 10px;
            }
            
            .btn-primary {
                background: white;
                color: #667eea;
            }
            
            .btn-secondary {
                background: rgba(255,255,255,0.2);
                color: white;
                border: 2px solid white;
            }
            
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            }
            
            .demo-section {
                background: #f8f9ff;
                padding: 40px;
                border-radius: 15px;
                margin: 40px 0;
            }
            
            .demo-links {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            
            .demo-link {
                background: white;
                padding: 20px;
                border-radius: 10px;
                text-decoration: none;
                color: #333;
                border: 2px solid #e1e5ff;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .demo-link:hover {
                border-color: #667eea;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            
            .api-info {
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 10px;
                padding: 25px;
                margin: 30px 0;
            }
            
            .code-block {
                background: #2d3748;
                color: #e2e8f0;
                padding: 20px;
                border-radius: 8px;
                font-family: 'Courier New', monospace;
                font-size: 0.9rem;
                overflow-x: auto;
                margin: 15px 0;
            }
            
            .sectors-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }
            
            .sector-tag {
                background: #667eea;
                color: white;
                padding: 8px 15px;
                border-radius: 20px;
                text-align: center;
                font-size: 0.9rem;
                font-weight: 500;
            }
            
            @media (max-width: 768px) {
                .header h1 {
                    font-size: 2rem;
                }
                
                .main-content {
                    padding: 20px;
                }
                
                .cta-buttons {
                    flex-direction: column;
                    align-items: center;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1><i class="fas fa-chart-line"></i> Market Analysis API</h1>
                <p>AI-Powered Market Intelligence for Indian Sectors</p>
            </div>
            
            <div class="main-content">
                <div class="features">
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-robot"></i>
                        </div>
                        <h3>AI-Powered Analysis</h3>
                        <p>Advanced AI using Google Gemini to provide deep market insights and trends analysis</p>
                    </div>
                    
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-tachometer-alt"></i>
                        </div>
                        <h3>Real-time Data</h3>
                        <p>Live market data collection from multiple sources for up-to-date analysis</p>
                    </div>
                    
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-shield-alt"></i>
                        </div>
                        <h3>Secure & Rate Limited</h3>
                        <p>Built-in security with API key authentication and intelligent rate limiting</p>
                    </div>
                </div>
                
                <div class="cta-section">
                    <h2>🚀 Get Started in Seconds</h2>
                    <p>No registration required - start analyzing markets immediately!</p>
                    <div class="cta-buttons">
                        <a href="/docs" class="btn btn-primary">
                            <i class="fas fa-book"></i> Interactive Docs
                        </a>
                        <a href="/health" class="btn btn-secondary">
                            <i class="fas fa-heartbeat"></i> API Status
                        </a>
                    </div>
                </div>
                
                <div class="demo-section">
                    <h2><i class="fas fa-play-circle"></i> Try Live Demos</h2>
                    <p>Click any sector below to see instant AI analysis:</p>
                    <div class="demo-links">
                        <a href="/analyze/technology?api_key=demo-key-123" class="demo-link" target="_blank">
                            <i class="fas fa-microchip"></i>
                            <div>
                                <strong>Technology</strong><br>
                                <small>IT, Software, Hardware</small>
                            </div>
                        </a>
                        <a href="/analyze/pharmaceuticals?api_key=demo-key-123" class="demo-link" target="_blank">
                            <i class="fas fa-pills"></i>
                            <div>
                                <strong>Pharmaceuticals</strong><br>
                                <small>Healthcare, Drugs, Medical</small>
                            </div>
                        </a>
                        <a href="/analyze/banking?api_key=demo-key-123" class="demo-link" target="_blank">
                            <i class="fas fa-university"></i>
                            <div>
                                <strong>Banking</strong><br>
                                <small>Finance, Loans, Digital Banking</small>
                            </div>
                        </a>
                        <a href="/analyze/energy?api_key=demo-key-123" class="demo-link" target="_blank">
                            <i class="fas fa-bolt"></i>
                            <div>
                                <strong>Energy</strong><br>
                                <small>Renewable, Solar, Power</small>
                            </div>
                        </a>
                    </div>
                </div>
                
                <div class="api-info">
                    <h3><i class="fas fa-code"></i> Quick API Usage</h3>
                    <p><strong>Simple Browser Request:</strong></p>
                    <div class="code-block">
https://your-api-url.railway.app/analyze/technology?api_key=demo-key-123
                    </div>
                    
                    <p><strong>Python Example:</strong></p>
                    <div class="code-block">
import requests

response = requests.get(
    "https://your-api-url.railway.app/analyze/technology",
    headers={"x-api-key": "demo-key-123"}
)

analysis = response.json()
print(analysis['analysis_report'])
                    </div>
                </div>
                
                <div>
                    <h3><i class="fas fa-industry"></i> Supported Sectors</h3>
                    <div class="sectors-grid">
                        <div class="sector-tag">Technology</div>
                        <div class="sector-tag">Pharmaceuticals</div>
                        <div class="sector-tag">Banking</div>
                        <div class="sector-tag">Automotive</div>
                        <div class="sector-tag">Energy</div>
                        <div class="sector-tag">Agriculture</div>
                        <div class="sector-tag">Steel</div>
                        <div class="sector-tag">FMCG</div>
                        <div class="sector-tag">Telecom</div>
                        <div class="sector-tag">Real Estate</div>
                        <div class="sector-tag">Healthcare</div>
                        <div class="sector-tag">Infrastructure</div>
                    </div>
                    <p style="text-align: center; margin-top: 20px; color: #666;">
                        <i>...and many more sectors supported</i>
                    </p>
                </div>
            </div>
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

