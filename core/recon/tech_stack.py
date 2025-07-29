import requests
from Wappalyzer import Wappalyzer, WebPage
from urllib.parse import urlparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Wappalyzer with latest tech database
try:
    wappalyzer = Wappalyzer.latest()
except Exception as e:
    logger.warning(f"Couldn't fetch latest Wappalyzer data: {e}. Using default.")
    wappalyzer = Wappalyzer()

def detect_tech_stack(target):
    """
    Detect technology stack of a target domain/URL
    Returns: { "url": str, "technologies": list, "categories": dict }
    """
    try:
        # Normalize URL format
        if not target.startswith(('http://', 'https://')):
            target = 'https://' + target
        
        # Handle potential redirects
        response = requests.get(
            target, 
            timeout=15,
            allow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
        )
        final_url = response.url
        
        # Create WebPage object for analysis
        webpage = WebPage(
            url=final_url,
            html=response.text,
            headers=dict(response.headers)
        )
        
        # Analyze technologies
        technologies = wappalyzer.analyze(webpage)
        categorized = wappalyzer.analyze_with_categories(webpage)
        
        return {
            "url": final_url,
            "technologies": list(technologies),
            "categories": categorized
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during tech detection: {e}")
        return {"error": f"Network error: {str(e)}"}
    except Exception as e:
        logger.error(f"Tech detection failed: {e}")
        return {"error": f"Detection failed: {str(e)}"}
