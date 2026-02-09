"""API client for Mount Alexander Shire waste collection."""
import json
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
                # Get text first, then parse as JSON manually
                # because the API returns JSON with wrong Content-Type header
                text = await response.text()
                results = json.loads(text)
                
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

            bin_name = bin_nam