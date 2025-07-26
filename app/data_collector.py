import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from duckduckgo_search import DDGS
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def search_market_news(self, sector: str, limit: int = 10) -> List[Dict]:
        """
        Search for recent market news related to the specified sector
        """
        try:
            with DDGS() as ddgs:
                # Search for recent news about the sector
                search_queries = [
                    f"{sector} sector India market news 2024",
                    f"{sector} industry India stock market",
                    f"{sector} companies India financial news"
                ]
                
                all_results = []
                
                for query in search_queries:
                    try:
                        results = list(ddgs.news(query, max_results=limit//len(search_queries)))
                        all_results.extend(results)
                    except Exception as e:
                        logger.warning(f"Error searching for {query}: {str(e)}")
                        continue
                
                # Remove duplicates based on URL
                seen_urls = set()
                unique_results = []
                for result in all_results:
                    if result.get('url') not in seen_urls:
                        seen_urls.add(result.get('url'))
                        unique_results.append(result)
                
                return unique_results[:limit]
                
        except Exception as e:
            logger.error(f"Error in search_market_news: {str(e)}")
            return []

    async def get_sector_companies(self, sector: str) -> List[str]:
        """
        Get a list of major companies in the specified sector
        """
        # Predefined mapping of sectors to major Indian companies
        sector_companies = {
            "pharmaceuticals": ["Sun Pharma", "Dr. Reddy's", "Cipla", "Lupin", "Aurobindo Pharma", "Divi's Labs"],
            "technology": ["TCS", "Infosys", "Wipro", "HCL Technologies", "Tech Mahindra", "Mindtree"],
            "banking": ["HDFC Bank", "ICICI Bank", "State Bank of India", "Kotak Mahindra", "Axis Bank"],
            "automotive": ["Tata Motors", "Mahindra", "Maruti Suzuki", "Bajaj Auto", "Hero MotoCorp"],
            "agriculture": ["UPL", "Godrej Agrovet", "Kaveri Seed", "Rallis India", "Coromandel International"],
            "energy": ["Reliance Industries", "ONGC", "Coal India", "NTPC", "Power Grid Corporation"],
            "steel": ["Tata Steel", "JSW Steel", "SAIL", "Jindal Steel", "JSPL"],
            "cement": ["UltraTech Cement", "Ambuja Cements", "ACC Limited", "Shree Cement", "JK Cement"],
            "fmcg": ["Hindustan Unilever", "ITC", "Nestle India", "Britannia", "Godrej Consumer"],
            "telecom": ["Bharti Airtel", "Reliance Jio", "Vodafone Idea", "BSNL"]
        }
        
        return sector_companies.get(sector.lower(), [])

    async def fetch_company_data(self, company: str) -> Dict:
        """
        Fetch basic information about a company
        """
        try:
            with DDGS() as ddgs:
                # Search for company financial information
                query = f"{company} India stock price financial results 2024"
                results = list(ddgs.news(query, max_results=3))
                
                return {
                    "company": company,
                    "news": results,
                    "search_query": query
                }
                
        except Exception as e:
            logger.error(f"Error fetching data for {company}: {str(e)}")
            return {"company": company, "news": [], "error": str(e)}

    async def get_market_indicators(self) -> Dict:
        """
        Get basic market indicators (simulated data for demo)
        """
        try:
            with DDGS() as ddgs:
                # Search for Indian market indices
                query = "Sensex Nifty Indian stock market today"
                results = list(ddgs.news(query, max_results=5))
                
                return {
                    "market_news": results,
                    "timestamp": datetime.now().isoformat(),
                    "indices": ["SENSEX", "NIFTY 50", "NIFTY BANK"]
                }
                
        except Exception as e:
            logger.error(f"Error fetching market indicators: {str(e)}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def collect_sector_data(self, sector: str) -> Dict:
        """
        Collect comprehensive data for a specific sector
        """
        try:
            # Get sector news
            sector_news = await self.search_market_news(sector)
            
            # Get major companies in the sector
            companies = await self.get_sector_companies(sector)
            
            # Get market indicators
            market_data = await self.get_market_indicators()
            
            # Collect data for top companies (limit to avoid rate limits)
            company_data = []
            for company in companies[:3]:  # Limit to top 3 companies
                data = await self.fetch_company_data(company)
                company_data.append(data)
                await asyncio.sleep(0.5)  # Small delay to avoid rate limits
            
            return {
                "sector": sector,
                "sector_news": sector_news,
                "companies": companies,
                "company_data": company_data,
                "market_indicators": market_data,
                "timestamp": datetime.now().isoformat(),
                "data_points": len(sector_news) + len(company_data)
            }
            
        except Exception as e:
            logger.error(f"Error collecting sector data for {sector}: {str(e)}")
            return {
                "sector": sector,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Standalone function for synchronous usage
def collect_sector_data_sync(sector: str) -> Dict:
    """
    Synchronous wrapper for collecting sector data
    """
    async def _collect():
        async with DataCollector() as collector:
            return await collector.collect_sector_data(sector)
    
    return asyncio.run(_collect())
