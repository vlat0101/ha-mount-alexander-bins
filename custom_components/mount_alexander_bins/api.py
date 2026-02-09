"""API client for Mount Alexander Shire waste collection."""
import json
import logging
from datetime import datetime
from urllib.parse import urlencode
import aiohttp
from bs4 import BeautifulSoup

from .const import API_AUTOCOMPLETE, API_GET_DETAILS

_LOGGER = logging.getLogger(__name__)


class MountAlexanderBinsAPI:
    """API client for Mount Alexander Bins."""

    def __init__(self, session: aiohttp.ClientSession):
        """Initialize the API client."""
        self.session = session
        self.headers = {
            "User-Agent": "HomeAssistant",
            "Accept": "application/json, text/html, */*",
        }

    async def search_address(self, query: str) -> list[dict]:
        """Search for addresses matching the query."""
        try:
            # Manually construct URL to avoid any URL encoding issues
            url = f"{API_AUTOCOMPLETE}?{urlencode({'q': query})}"
            
            _LOGGER.debug("Searching URL: %s", url)
            
            async with self.session.get(
                url,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                _LOGGER.debug("Response status: %s", response.status)
                _LOGGER.debug("Response URL: %s", response.url)
                response.raise_for_status()
                
                # Get text first, then parse as JSON manually
                # because the API returns JSON with wrong Content-Type header
                text = await response.text()
                
                _LOGGER.debug("API raw response (first 200 chars): %s", text[:200])
                
                # Handle empty response
                if not text or text.strip() == "":
                    _LOGGER.warning("Empty response from API for query: %s", query)
                    return []
                
                # Check if we got HTML instead of JSON (API error)
                if text.strip().startswith("<!DOCTYPE") or text.strip().startswith("<html"):
                    _LOGGER.error("Received HTML instead of JSON. API may be down or URL is wrong. URL: %s", url)
                    return []
                
                try:
                    results = json.loads(text)
                except json.JSONDecodeError as json_err:
                    _LOGGER.error(
                        "Failed to parse JSON. Response: %s, Error: %s",
                        text[:500],
                        json_err
                    )
                    return []
                
                _LOGGER.debug("Parsed results: %s", results)
                
                if not results:
                    return []
                
                return [
                    {
                        "address": item["suggestion"],
                        "property_id": item["data"],
                    }
                    for item in results
                ]
        except aiohttp.ClientError as err:
            _LOGGER.error("Network error searching address: %s", err)
            raise
        except Exception as err:
            _LOGGER.exception("Unexpected error searching address")
            raise

    async def get_collection_details(self, property_id: str) -> dict:
        """Get bin collection details for a property."""
        try:
            _LOGGER.debug("Getting details for property: %s", property_id)
            
            async with self.session.post(
                API_GET_DETAILS,
                data={"ID": property_id},
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response.raise_for_status()
                html = await response.text()
                
                _LOGGER.debug("Got HTML response, length: %d", len(html))
                
                return self._parse_collection_details(html)
        except Exception as err:
            _LOGGER.exception("Error getting collection details")
            raise

    def _parse_collection_details(self, html: str) -> dict:
        """Parse HTML response to extract bin collection information."""
        soup = BeautifulSoup(html, "html.parser")
        bins = {}

        # Find all bin collection divs
        for bin_div in soup.find_all("div", class_="mt-1"):
            bin_name_elem = bin_div.find("h6")
            if not bin_name_elem:
                continue

            bin_name = bin_name_elem.text.strip()
            
            # Extract next collection date
            date_elem = bin_div.find("p", class_="mb-0")
            if date_elem:
                date_text = date_elem.text.strip()
                
                # Parse date (format: "Monday, 10 February 2025")
                try:
                    next_date = datetime.strptime(date_text, "%A, %d %B %Y").date()
                    
                    # Determine bin type
                    bin_type = None
                    if "garbage" in bin_name.lower() or "red" in bin_name.lower():
                        bin_type = "garbage"
                    elif "recycling" in bin_name.lower() or "yellow" in bin_name.lower():
                        bin_type = "recycling"
                    elif "organics" in bin_name.lower() or "green" in bin_name.lower():
                        bin_type = "organics"
                    
                    if bin_type:
                        bins[bin_type] = {
                            "name": bin_name,
                            "next_collection": next_date,
                        }
                        _LOGGER.debug("Found bin: %s, next collection: %s", bin_type, next_date)
                        
                except ValueError as err:
                    _LOGGER.warning("Could not parse date '%s': %s", date_text, err)

        _LOGGER.debug("Total bins found: %d", len(bins))
        return bins