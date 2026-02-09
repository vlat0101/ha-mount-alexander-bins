"""API client for Mount Alexander Shire waste collection."""
import logging
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup

from .const import API_AUTOCOMPLETE, API_GET_DETAILS

_LOGGER = logging.getLogger(__name__)


class MountAlexanderBinsAPI:
    """API client for Mount Alexander Bins."""

    def __init__(self, session: aiohttp.ClientSession):
        """Initialize the API client."""
        self.session = session

    async def search_address(self, query: str) -> list[dict]:
        """Search for addresses matching the query."""
        try:
            async with self.session.get(
                API_AUTOCOMPLETE, params={"q": query}
            ) as response:
                response.raise_for_status()
                results = await response.json()
                
                if not results:
                    return []
                
                return [
                    {
                        "address": item["suggestion"],
                        "property_id": item["data"],
                    }
                    for item in results
                ]
        except Exception as err:
            _LOGGER.error("Error searching address: %s", err)
            raise

    async def get_collection_details(self, property_id: str) -> dict:
        """Get bin collection details for a property."""
        try:
            async with self.session.post(
                API_GET_DETAILS, data={"ID": property_id}
            ) as response:
                response.raise_for_status()
                html = await response.text()
                
                return self._parse_collection_details(html)
        except Exception as err:
            _LOGGER.error("Error getting collection details: %s", err)
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
                except ValueError as err:
                    _LOGGER.warning("Could not parse date '%s': %s", date_text, err)

        return bins