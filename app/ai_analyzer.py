import google.generativeai as genai
from typing import Dict, List
import logging
from datetime import datetime
from .config import settings

logger = logging.getLogger(__name__)

class AIAnalyzer:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Try different model names in order of preference
            model_names = [
                'gemini-1.5-flash',
                'gemini-1.5-pro', 
                'gemini-pro-latest',
                'gemini-pro'
            ]
            
            self.model = None
            for model_name in model_names:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    # Test the model with a simple prompt
                    test_response = self.model.generate_content("Hello")
                    if test_response and test_response.text:
                        logger.info(f"Successfully initialized Gemini model: {model_name}")
                        break
                except Exception as e:
                    logger.warning(f"Failed to initialize model {model_name}: {str(e)}")
                    continue
            
            if not self.model:
                logger.error("Failed to initialize any Gemini model. AI analysis will be simulated.")
        else:
            self.model = None
            logger.warning("Gemini API key not configured. AI analysis will be simulated.")

    def format_data_for_analysis(self, sector_data: Dict) -> str:
        """
        Format the collected data into a prompt for the AI model
        """
        prompt = f"""
# Market Analysis Request for {sector_data['sector'].upper()} Sector

## Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Sector Information:
- Sector: {sector_data['sector']}
- Data Collection Timestamp: {sector_data.get('timestamp', 'N/A')}
- Number of Data Points: {sector_data.get('data_points', 0)}

## Recent Sector News:
"""
        
        # Add sector news
        for i, news in enumerate(sector_data.get('sector_news', [])[:5]):
            prompt += f"\n### News {i+1}:\n"
            prompt += f"**Title:** {news.get('title', 'N/A')}\n"
            prompt += f"**Source:** {news.get('source', 'N/A')}\n"
            prompt += f"**Date:** {news.get('date', 'N/A')}\n"
            prompt += f"**Summary:** {news.get('body', 'N/A')[:200]}...\n"

        # Add major companies
        companies = sector_data.get('companies', [])
        if companies:
            prompt += f"\n## Major Companies in {sector_data['sector']} Sector:\n"
            for company in companies:
                prompt += f"- {company}\n"

        # Add company-specific data
        company_data = sector_data.get('company_data', [])
        if company_data:
            prompt += "\n## Company-Specific News:\n"
            for company_info in company_data[:3]:
                prompt += f"\n### {company_info['company']}:\n"
                for news in company_info.get('news', [])[:2]:
                    prompt += f"- **{news.get('title', 'N/A')}** ({news.get('date', 'N/A')})\n"

        # Add market indicators
        market_data = sector_data.get('market_indicators', {})
        if market_data.get('market_news'):
            prompt += "\n## Overall Market Context:\n"
            for news in market_data['market_news'][:3]:
                prompt += f"- **{news.get('title', 'N/A')}** - {news.get('body', 'N/A')[:100]}...\n"

        # Add analysis request
        prompt += f"""

## Analysis Requirements:

Please provide a comprehensive market analysis report for the {sector_data['sector']} sector in India with the following structure:

1. **Executive Summary**
   - Current market sentiment
   - Key trends and developments
   - Overall sector outlook

2. **Market Analysis**
   - Sector performance analysis
   - Key drivers and challenges
   - Regulatory environment impact
   - Competition landscape

3. **Trade Opportunities**
   - Investment opportunities (with specific company recommendations if applicable)
   - Short-term trading ideas
   - Long-term investment themes
   - Risk assessment

4. **Key Metrics & Indicators**
   - Important financial metrics to watch
   - Market indicators
   - Upcoming events/catalysts

5. **Risk Analysis**
   - Sector-specific risks
   - Market risks
   - Regulatory risks
   - Mitigation strategies

6. **Recommendations**
   - Investment recommendations (Buy/Hold/Sell)
   - Portfolio allocation suggestions
   - Time horizon considerations

Format the response as a well-structured markdown document that can be saved as a .md file.
Use bullet points, headers, and formatting to make it easily readable.
Base your analysis strictly on the provided data and current market conditions.
"""
        
        return prompt

    def generate_fallback_analysis(self, sector: str) -> str:
        """
        Generate a basic analysis when AI is not available
        """
        return f"""# Market Analysis Report: {sector.upper()} Sector

## Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
This is a simulated analysis report for the {sector} sector. To get AI-powered insights, please configure your Gemini API key in the .env file.

## Market Analysis
- **Sector Focus:** {sector}
- **Market:** Indian Stock Market
- **Analysis Type:** Basic Template

## Trade Opportunities
### Investment Themes
1. **Growth Opportunities:** Look for companies with strong fundamentals
2. **Value Plays:** Identify undervalued stocks in the sector
3. **Dividend Stocks:** Consider companies with consistent dividend history

### Key Companies to Watch
Based on the sector, major players typically include established market leaders and emerging growth companies.

## Risk Analysis
### Key Risks
- Market volatility
- Regulatory changes
- Economic conditions
- Sector-specific challenges

### Risk Mitigation
- Diversification across multiple stocks
- Regular portfolio review
- Stop-loss mechanisms
- Stay updated with market news

## Recommendations
- **Time Horizon:** Medium to long-term (1-3 years)
- **Risk Level:** Moderate
- **Portfolio Allocation:** Consider sector exposure within broader portfolio

---
*Note: This is a template analysis. For detailed AI-powered insights, please configure the Gemini API key.*
"""

    async def analyze_sector_data(self, sector_data: Dict) -> str:
        """
        Analyze the sector data and generate a markdown report
        """
        try:
            if not self.model:
                logger.warning("AI model not available, generating fallback analysis")
                return self.generate_fallback_analysis(sector_data['sector'])

            # Format data for analysis
            prompt = self.format_data_for_analysis(sector_data)
            
            # Generate analysis using Gemini
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                return response.text
            else:
                logger.error("Empty response from AI model")
                return self.generate_fallback_analysis(sector_data['sector'])
                
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            return f"""# Market Analysis Report: {sector_data['sector'].upper()} Sector

## Error in Analysis

An error occurred while generating the AI analysis: {str(e)}

Please check your Gemini API key configuration and try again.

---

{self.generate_fallback_analysis(sector_data['sector'])}
"""

    def validate_api_key(self) -> bool:
        """
        Validate if the Gemini API key is working
        """
        try:
            if not self.model:
                return False
            
            # Test with a simple prompt
            test_response = self.model.generate_content("Say 'API key is working' if you receive this message.")
            return test_response and test_response.text and "working" in test_response.text.lower()
            
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False
