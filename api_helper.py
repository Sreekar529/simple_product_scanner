import logging
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://world.openfoodfacts.net"


def _safe_get(url, params=None, timeout=5):
    # Small helper around requests.get so we don't repeat error handling
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        if resp.status_code != 200:
            logger.warning(f"API returned non-200 status code: {resp.status_code} for {url}")
            return None
        return resp.json()
    except requests.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error when fetching API: {e}")
        return None

def _normalize_product(product):
    # Keep only the fields we care about in the UI
    if not product:
        return None

    return {
        "ingredients": product.get("ingredients_text", "Information not available."),
        "nutrition": product.get("nutriments", {}),
        "brand": product.get("brands", "Generic"),
        "nutrition_grade": product.get("nutrition_grades"),
        "name": product.get("product_name"),
    }


def fetch_food_details(query):
    # Given a barcode string, ask Open Food Facts for product details

    if not query:
        return None

    query = str(query).strip()

    # Only accept barcode-like numeric strings (EAN/UPC style)
    if query.isdigit() and 8 <= len(query) <= 14:
        fields = [
            "product_name",
            "nutriscore_data",
            "nutriments",
            "nutrition_grades",
            "brands",
            "ingredients_text",
        ]
        url = f"{BASE_URL}/api/v2/product/{query}"
        data = _safe_get(url, params={"fields": ",".join(fields)})

        if data and data.get("status") == 1 and data.get("product"):
            return _normalize_product(data["product"])

    return None