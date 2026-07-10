"""API client for Mount Alexander Shire Council bin collection.

Uses the council's own website API:
  1. /api/v1/myarea/search?keywords=...  → address search (JSON)
  2. /ocapi/Public/myarea/wasteservices?geolocationid=GUID  → bin schedule (JSON with HTML payload)

Auto-recovery: if the stored property ID returns "no results", the client
re-runs the address search to find the current ID and retries once.
"""
import logging
import re
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup

from .const import API_SEARCH, API_WASTE_SERVICES, BIN_NAME_MAPPING

_LOGGER = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=15)

# Headers the council site expects (same-origin XHR)
_HEADERS = {
    "x-requested-with": "XMLHttpRequest",
}


class MountAlexanderBinsAPI:
    """API client for Mount Alexander Bins."""

    def __init__(self, session: aiohttp.ClientSession, property_id: str | None = None) -> None:
        """Initialize the API client."""
        self.session = session
        self.property_id = property_id
        self.address: str | None = None

    # ── Config-flow: address search ──────────────────────────────

    async def search_addresses(self, query: str) -> list[dict]:
        """Search for addresses matching the query.

        Returns list of dicts with 'Id' and 'AddressSingleLine' keys.
        """
        try:
            async with self.session.get(
                API_SEARCH,
                params={"keywords": query},
                headers=_HEADERS,
                timeout=_TIMEOUT,
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("Items", [])
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.error("Error searching addresses: %s", err)
            raise

    # ── Data fetching (for coordinator) ──────────────────────────

    async def get_collection_schedule(self) -> dict[str, str]:
        """Get upcoming bin collection dates for the configured property.

        Returns dict mapping bin type keys (e.g. 'garbage') to ISO date
        strings (e.g. '2026-02-11').

        Auto-recovery: if the stored property ID returns no results, the
        address search is re-run to find the current ID and the request
        is retried once.
        """
        if not self.property_id:
            raise ValueError("property_id is required")

        result = await self._fetch_schedule(self.property_id)

        # Auto-recovery: empty result + we have an address to search
        if not result and self.address:
            _LOGGER.warning(
                "No collection data for property %s, re-resolving address '%s'",
                self.property_id,
                self.address,
            )
            new_id = await self._resolve_property_id(self.address)
            if new_id and new_id != self.property_id:
                _LOGGER.info(
                    "Property ID changed: %s → %s, retrying",
                    self.property_id,
                    new_id,
                )
                self.property_id = new_id
                result = await self._fetch_schedule(new_id)
                if result:
                    _LOGGER.info(
                        "Auto-recovery succeeded with new property ID %s",
                        new_id,
                    )

        return result

    async def _fetch_schedule(self, property_id: str) -> dict[str, str]:
        """Fetch and parse the waste services HTML for a property ID."""
        try:
            async with self.session.get(
                API_WASTE_SERVICES,
                params={
                    "geolocationid": property_id,
                    "ocsvclang": "en-AU",
                },
                headers=_HEADERS,
                timeout=_TIMEOUT,
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.error("Error fetching collection schedule: %s", err)
            raise

        if not data.get("success"):
            _LOGGER.error("API returned success=false")
            return {}

        html = data.get("responseContent", "")
        return self._parse_waste_html(html)

    async def _resolve_property_id(self, address: str) -> str | None:
        """Search for an address and return the current property ID."""
        try:
            items = await self.search_addresses(address)
            if items:
                return items[0].get("Id")
        except Exception:
            _LOGGER.exception("Error re-resolving address '%s'", address)
        return None

    def _parse_waste_html(self, html: str) -> dict[str, str]:
        """Parse the waste services HTML into a bin schedule dict."""
        soup = BeautifulSoup(html, "html.parser")
        result: dict[str, str] = {}

        # Check for no-results
        if soup.select_one(".no-results"):
            _LOGGER.debug("No collection services for this address")
            return result

        for service_div in soup.find_all("div", class_="waste-services-result"):
            # Get bin type from the <h3> heading
            h3 = service_div.find("h3")
            if not h3:
                continue
            bin_name = h3.get_text(strip=True)

            bin_key = self._match_bin_type(bin_name)
            if not bin_key:
                _LOGGER.debug("Unknown bin type: '%s'", bin_name)
                continue

            # Get next collection date from <div class="next-service">
            date_div = service_div.find("div", class_="next-service")
            if not date_div:
                continue
            date_text = date_div.get_text(strip=True)

            parsed_date = self._parse_date(date_text)
            if parsed_date:
                result[bin_key] = parsed_date
            else:
                _LOGGER.warning("Could not parse date '%s' for %s", date_text, bin_name)

        _LOGGER.debug("Parsed collection schedule: %s", result)
        return result

    @staticmethod
    def _match_bin_type(name: str) -> str | None:
        """Match an HTML heading to a bin type key."""
        name_lower = name.lower().strip()
        for keyword, bin_key in BIN_NAME_MAPPING.items():
            if keyword in name_lower:
                return bin_key
        return None

    @staticmethod
    def _parse_date(text: str) -> str | None:
        """Parse a date like 'Wed 11/2/2026' or 'Mon 16/2/2026' to 'YYYY-MM-DD'."""
        # Strip optional day name prefix (e.g. "Wed ", "Mon ")
        cleaned = re.sub(r"^[A-Za-z]+\s+", "", text.strip())

        # Try D/M/YYYY and DD/MM/YYYY
        for fmt in ("%d/%m/%Y", "%d/%m/%y"):
            try:
                return datetime.strptime(cleaned, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue

        # Fallback: try full text with day name
        for fmt in ("%a %d/%m/%Y", "%A %d/%m/%Y"):
            try:
                return datetime.strptime(text.strip(), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue

        return None

    async def test_connection(self) -> bool:
        """Test if we can fetch data for the configured property."""
        try:
            schedule = await self.get_collection_schedule()
            return isinstance(schedule, dict) and len(schedule) > 0
        except Exception:
            _LOGGER.exception("Connection test failed")
            return False
