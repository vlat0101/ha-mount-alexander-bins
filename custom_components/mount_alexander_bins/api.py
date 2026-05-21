"""API client for Mount Alexander Shire waste collection."""
import logging
from datetime import datetime
from urllib.parse import urlencode

import aiohttp
from bs4 import BeautifulSoup

from .const import API_ADDRESS_SEARCH, API_WASTE_SERVICES

_LOGGER = logging.getLogger(__name__)


class MountAlexanderBinsAPI:
    """API client for Mount Alexander Bins.

    Uses the council's OpenCities/Granicus "My Neighbourhood" module API:
    1. Address search → geolocation ID
    2. Waste services lookup by geolocation ID
    """

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self.session = session
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        }

    async def search_address(self, query: str) -> list[dict]:
        """Search for addresses matching the query.

        Returns list of {address, geolocation_id} dicts.
        """
        try:
            params = {"keywords": query, "maxresults": 10}
            url = f"{API_ADDRESS_SEARCH}?{urlencode(params)}"

            _LOGGER.debug("Searching address: %s", query)

            async with self.session.get(
                url,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as response:
                response.raise_for_status()
                data = await response.json()

                items = data.get("Items", [])
                if not items:
                    _LOGGER.debug("No addresses found for: %s", query)
                    return []

                results = []
                for item in items:
                    results.append({
                        "address": item["AddressSingleLine"],
                        "geolocation_id": item["Id"],
                    })
                    _LOGGER.debug(
                        "Found: %s (ID: %s)",
                        item["AddressSingleLine"],
                        item["Id"],
                    )

                return results

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error searching address: %s", err)
            raise
        except Exception:
            _LOGGER.exception("Unexpected error searching address")
            raise

    async def get_collection_details(self, geolocation_id: str) -> dict:
        """Get bin collection details for a geolocation ID.

        Returns dict keyed by bin type (garbage, recycling) with next collection dates.
        """
        try:
            params = {
                "geolocationid": geolocation_id,
                "ocsvclang": "en-AU",
            }
            url = f"{API_WASTE_SERVICES}?{urlencode(params)}"

            _LOGGER.debug("Getting collection details for: %s", geolocation_id)

            async with self.session.get(
                url,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as response:
                response.raise_for_status()
                data = await response.json()
                html = data.get("responseContent", "")
                return self._parse_collection_html(html)

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error getting collection details: %s", err)
            raise
        except Exception:
            _LOGGER.exception("Error getting collection details")
            raise

    def _parse_collection_html(self, html: str) -> dict:
        """Parse the wasteservices HTML response.

        Expected HTML structure:
        <div class="waste-services-result {type} date-precise">
          <article>
            <h3>Bin Name</h3>
            <div class="next-service">Mon 25/5/2026</div>
          </article>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        bins: dict[str, dict[str, any]] = {}

        # Check for no-results
        if soup.select_one(".no-results"):
            _LOGGER.debug("No collection services for this address")
            return bins

        for result_div in soup.select(".waste-services-result"):
            if "no-results" in result_div.get("class", []):
                continue

            # Get bin name from <h3>
            name_elem = result_div.find("h3")
            if not name_elem:
                continue
            bin_name = name_elem.text.strip()

            # Get next collection date
            date_elem = result_div.select_one(".next-service")
            if not date_elem:
                continue
            date_text = date_elem.text.strip()
            # Format: "Mon 25/5/2026"
            try:
                next_date = datetime.strptime(date_text, "%a %d/%m/%Y").date()
            except ValueError:
                _LOGGER.warning("Could not parse date: %s", date_text)
                continue

            # Determine bin type
            if "general" in bin_name.lower() or "garbage" in bin_name.lower():
                bin_type = "garbage"
            elif "recycling" in bin_name.lower() or "yellow" in bin_name.lower():
                bin_type = "recycling"
            else:
                _LOGGER.debug("Unknown bin type: %s", bin_name)
                continue

            bins[bin_type] = {
                "name": bin_name,
                "next_collection": next_date,
            }
            _LOGGER.debug(
                "Found bin: %s, next collection: %s",
                bin_type,
                next_date,
            )

        _LOGGER.debug("Total bins found: %d", len(bins))
        return bins
