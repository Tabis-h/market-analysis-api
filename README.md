# Market Analysis API

A FastAPI service that analyzes market data and provides trade opportunity insights for specific sectors in India.

## Features

- **Sector Analysis**: Comprehensive market analysis for various Indian sectors
- **AI-Powered Insights**: Uses Google Gemini API for intelligent analysis
- **Real-time Data**: Collects current market data and news
- **Simple Authentication**: API key-based authentication (no login required)
- **Rate Limiting**: Prevents API abuse with per-IP rate limits
- **Caching**: In-memory caching for improved performance
- **Security**: Input validation and security best practices

## Quick Start

### Prerequisites

- Python 3.8+
- pip package manager

### Installation

1. **Clone or download the project**
   ```bash
   cd D:\market_analysis
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file and add your API keys:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   API_KEY=your_custom_api_key_here  # Optional, has default
   DEBUG=False  # Optional, set to True for development
   ```

   To get a free Gemini API key:
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Sign in with your Google account
   - Create a new API key
   - Copy the key to your `.env` file

4. **Run the application**
   
   **Method 1: Direct Python execution**
   ```bash
   python -m app.main
   ```
   
   **Method 2: Using uvicorn**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the API**
   - **Homepage with test links:** http://localhost:8000/
   - **API Documentation:** http://localhost:8000/docs
   - **Health Check:** http://localhost:8000/health
   - **Direct browser testing:** http://localhost:8000/analyze/technology?api_key=demo-key-123

## Usage

### Authentication

This API uses simple API key authentication. No login or user registration is required.

**Method 1: Request Header**
```
x-api-key: your-api-key-here
```

**Method 2: URL Query Parameter (for browser testing)**
```
?api_key=your-api-key-here
```

**Demo API Keys (for testing):**
- `demo-key-123`
- `guest-access-456`
- `public-api-789`

### Market Analysis

**Using Command Line (PowerShell):**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/analyze/pharmaceuticals" -Method GET -Headers @{"x-api-key"="demo-key-123"}
```

**Using Browser URL (easiest method):**
```
http://localhost:8000/analyze/pharmaceuticals?api_key=demo-key-123
```

**Using curl (Linux/Mac/WSL):**
```bash
curl -X GET "http://localhost:8000/analyze/pharmaceuticals" \
  -H "x-api-key: demo-key-123"
```

**Supported Sectors:**
- pharmaceuticals
- technology
- banking
- automotive
- agriculture
- energy
- steel
- cement
- fmcg
- telecom
- textiles
- aviation
- real_estate
- infrastructure
- chemicals
- mining
- oil_gas
- power
- retail
- media
- hospitality
- defense

## API Endpoints

### Core Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | API information page | No |
| GET | `/docs` | Interactive API documentation | No |
| GET | `/health` | Health check | No |
| GET | `/analyze/{sector}` | Sector analysis | Yes (API Key) |

### Sample Response

The analysis endpoint returns a structured markdown report:

```json
{
  "sector": "pharmaceuticals",
  "analysis_report": "# Market Analysis Report: PHARMACEUTICALS Sector\n\n## Executive Summary\n...",
  "timestamp": "2024-01-15T10:30:00",
  "data_sources": 15,
  "session_id": "guest_1642248600"
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `API_KEY` | Custom API key | `default-api-key-123` |
| `REQUESTS_PER_MINUTE` | Rate limit per minute | 10 |
| `REQUESTS_PER_HOUR` | Rate limit per hour | 100 |
| `DEBUG` | Debug mode | True |

### Rate Limiting

- **Per minute**: 10 requests
- **Per hour**: 100 requests  
- Limits are enforced per IP address
- Exceeded limits return HTTP 429 error

### Caching

- Analysis results are cached for 30 minutes
- Cache key includes sector name
- Automatic cleanup of expired entries

### Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│  Data Collector │────│  External APIs  │
│                 │    │                 │    │  (DuckDuckGo)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         │              ┌─────────────────┐
         │              │   AI Analyzer   │
         │              │  (Gemini API)   │
         │              └─────────────────┘
         │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Auth System    │    │ Rate Limiter    │    │  Cache System   │
│  (API Keys)     │    │ (Per IP)        │    │  (In-Memory)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Data Sources

1. **News Data**: DuckDuckGo Search API for recent sector news
2. **Company Data**: Pre-defined major companies by sector
3. **Market Context**: General market indicators and trends
4. **AI Analysis**: Google Gemini API for intelligent insights

## Security Features

- **API Key Authentication**: Simple and secure API key-based authentication
- **Rate Limiting**: Prevents API abuse
- **Input Validation**: All inputs are validated and sanitized
- **CORS Protection**: Configurable cross-origin resource sharing
- **Error Handling**: Comprehensive error handling and logging

## Development

### Project Structure

```
market_analysis/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── auth.py              # Simplified authentication
│   ├── models.py            # Pydantic models
│   ├── rate_limiter.py      # Rate limiting logic
│   ├── data_collector.py    # Data collection module
│   └── ai_analyzer.py       # AI analysis module
├── markdown analysis report/ # Generated analysis reports
│   ├── analysis_technology_20250726_133409.md
│   ├── analysis_pharmaceuticals_20250726_133425.md
│   └── ...
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
└── README.md               # This file
```



### File Storage

Generated analysis reports are automatically saved as markdown files in:
```
D:\market_analysis\markdown analysis report\
```

Each report includes:
- Timestamp of generation
- Session ID for tracking
- Complete market analysis in markdown format
- Data source count

### Adding New Sectors

To add support for new sectors:

1. Update the `sector_companies` dictionary in `data_collector.py`
2. Add the sector name to the supported sectors list in `models.py`
3. Test the analysis with the new sector

## Troubleshooting

### Common Issues

1. **"Gemini API key not configured"**
   - Add your Gemini API key to the `.env` file
   - Ensure the key is valid and has proper permissions

2. **Rate limit exceeded**
   - Wait for the rate limit window to reset
   - Reduce request frequency
   - Consider upgrading rate limits in production

3. **No data collected**
   - Check internet connectivity
   - Verify DuckDuckGo search is accessible
   - Check logs for specific error messages

4. **Authentication errors**
   - Use a valid API key in the x-api-key header
   - Check that the API key is not empty or malformed
   - Verify you're using one of the valid demo keys for testing

### Logs

The application logs important events including:
- Authentication attempts
- Data collection status
- Analysis processing time
- Error conditions

Check the console output for detailed information.

## Deployment

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/market-analysis-api.git
   cd market-analysis-api
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys
   ```

3. **Install and run**
   ```bash
   pip install -r requirements.txt
   python -m app.main
   ```

### Docker Deployment

1. **Build the image**
   ```bash
   docker build -t market-analysis-api .
   ```

2. **Run the container**
   ```bash
   docker run -d -p 8000:8000 \
     -e GEMINI_API_KEY=your_gemini_key \
     -e API_KEY=your_api_key \
     --name market-analysis-api \
     market-analysis-api
   ```

### Cloud Deployment Options

#### Railway
1. Fork this repository
2. Connect to Railway
3. Set environment variables in Railway dashboard
4. Deploy automatically

#### Render
1. Fork this repository
2. Create new Web Service on Render
3. Connect your GitHub repository
4. Set environment variables
5. Deploy with Docker

#### Heroku
1. Install Heroku CLI
2. ```bash
   heroku create your-app-name
   heroku config:set GEMINI_API_KEY=your_key
   git push heroku main
   ```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc


