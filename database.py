import logging
from pymongo import MongoClient

logger = logging.getLogger(__name__)


def connect_to_database():
    # Connect to the shared MongoDB cluster and return the collection
    uri = "mongodb+srv://ingredoai2:BXM6Hc1R57Hkiofy@cluster0.zimunh9.mongodb.net/"
    try:
        # Slightly longer timeout so it works on slower networks
        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        # Quick ping so we fail fast if something is wrong
        client.admin.command("ping")
        db = client["dev-sb1-sf"]
        return db["trending_products"]
    except Exception as e:
        logger.error(f"MongoDB connection error: {e}")
        return None


def search_by_barcode(collection, barcode):
    # Try to match a product using a barcode string
    # Either via `results.barcode` or product name containing the digits
    pipeline = [
        {"$unwind": "$results"},
        {
            "$match": {
                "$or": [
                    {"results.product": {"$regex": barcode, "$options": "i"}},
                    {"results.barcode": barcode},
                ]
            }
        },
        {
            "$project": {
                "category": 1,
                "product_name": "$results.product",
                "relative_count": "$results.relative_count",
            }
        },
    ]
    try:
        return list(collection.aggregate(pipeline))
    except Exception as e:
        logger.error(f"Search by barcode failed: {e}")
        return []


def search_by_text(collection, query):
    # Simple text search on `results.product`
    pipeline = [
        {"$unwind": "$results"},
        {"$match": {"results.product": {"$regex": query, "$options": "i"}}},
        {
            "$project": {
                "category": 1,
                "product_name": "$results.product",
                "relative_count": "$results.relative_count",
            }
        },
    ]
    try:
        return list(collection.aggregate(pipeline))
    except Exception as e:
        logger.error(f"Search by text failed: {e}")
        return []