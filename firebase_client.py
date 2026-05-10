import requests
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Public config for OOTB functionality
FIREBASE_CONFIG = {
    "apiKey": os.getenv("FIREBASE_API_KEY", "AIzaSyDW9N8gbF7Lif236S4EavN3N1GiAIsS454"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID", "fbasepg"),
}

_PROJECT = FIREBASE_CONFIG["projectId"]
_API_KEY = FIREBASE_CONFIG["apiKey"]
_BASE = f"https://firestore.googleapis.com/v1/projects/{_PROJECT}/databases/(default)/documents"


def _params():
    return {"key": _API_KEY}


def _to_value(v):
    if v is None:
        return {"nullValue": None}
    if isinstance(v, bool):
        return {"booleanValue": v}
    if isinstance(v, int):
        return {"integerValue": str(v)}
    if isinstance(v, float):
        return {"doubleValue": v}
    if isinstance(v, str):
        return {"stringValue": v}
    if isinstance(v, datetime.datetime):
        return {"timestampValue": v.isoformat()}
    return {"nullValue": None}


def _to_fields(data: dict) -> dict:
    return {k: _to_value(v) for k, v in data.items()}


def _parse_value(val: dict):
    if "stringValue" in val:
        return val["stringValue"]
    if "integerValue" in val:
        return int(val["integerValue"])
    if "doubleValue" in val:
        return val["doubleValue"]
    if "booleanValue" in val:
        return val["booleanValue"]
    if "nullValue" in val:
        return None
    if "timestampValue" in val:
        ts = val["timestampValue"]
        try:
            return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return None
    if "mapValue" in val:
        return _parse_fields(val["mapValue"].get("fields", {}))
    return None


def _parse_fields(fields: dict) -> dict:
    return {k: _parse_value(v) for k, v in fields.items()}


def _doc_to_dict(doc: dict) -> dict:
    name = doc.get("name", "")
    doc_id = name.split("/")[-1]
    data = _parse_fields(doc.get("fields", {}))
    data["id"] = doc_id
    return data


def get_document(collection: str, doc_id: str) -> dict | None:
    url = f"{_BASE}/{collection}/{doc_id}"
    r = requests.get(url, params=_params())
    if r.status_code == 404:
        return None
    r.raise_for_status()
    doc = r.json()
    if "error" in doc:
        return None
    return _doc_to_dict(doc)


def set_document(collection: str, doc_id: str, data: dict):
    url = f"{_BASE}/{collection}/{doc_id}"
    body = {"fields": _to_fields(data)}
    r = requests.patch(url, json=body, params=_params())
    r.raise_for_status()


def create_document(collection: str, data: dict) -> str:
    url = f"{_BASE}/{collection}"
    body = {"fields": _to_fields(data)}
    r = requests.post(url, json=body, params=_params())
    r.raise_for_status()
    name = r.json().get("name", "")
    return name.split("/")[-1]


def delete_document(collection: str, doc_id: str):
    url = f"{_BASE}/{collection}/{doc_id}"
    r = requests.delete(url, params=_params())
    r.raise_for_status()


def query_collection(collection: str, parent_path: str = "", where_field: str = None,
                     where_value: str = None, order_by: str = None,
                     direction: str = "DESCENDING", limit: int = 50) -> list[dict]:
    base = _BASE if not parent_path else f"{_BASE}/{parent_path}"
    url = f"{base}:runQuery"
    structured = {
        "from": [{"collectionId": collection}],
        "limit": limit,
    }
    if where_field and where_value is not None:
        structured["where"] = {
            "fieldFilter": {
                "field": {"fieldPath": where_field},
                "op": "EQUAL",
                "value": {"stringValue": where_value},
            }
        }
    if order_by:
        structured["orderBy"] = [{"field": {"fieldPath": order_by}, "direction": direction}]
    r = requests.post(url, json={"structuredQuery": structured}, params=_params())
    r.raise_for_status()
    results = []
    for item in r.json():
        doc = item.get("document")
        if doc:
            results.append(_doc_to_dict(doc))
    return results


def increment_field(collection: str, doc_id: str, field: str, delta: int):
    full_doc_path = f"projects/{_PROJECT}/databases/(default)/documents/{collection}/{doc_id}"
    url = f"https://firestore.googleapis.com/v1/projects/{_PROJECT}/databases/(default)/documents:commit"
    body = {
        "writes": [{
            "transform": {
                "document": full_doc_path,
                "fieldTransforms": [{
                    "fieldPath": field,
                    "increment": {"integerValue": str(delta)},
                }],
            }
        }]
    }
    r = requests.post(url, json=body, params=_params())
    r.raise_for_status()


def add_to_subcollection(collection: str, doc_id: str, sub: str, data: dict) -> str:
    url = f"{_BASE}/{collection}/{doc_id}/{sub}"
    body = {"fields": _to_fields(data)}
    r = requests.post(url, json=body, params=_params())
    r.raise_for_status()
    name = r.json().get("name", "")
    return name.split("/")[-1]


def query_subcollection(collection: str, doc_id: str, sub: str,
                        order_by: str = None, direction: str = "ASCENDING") -> list[dict]:
    return query_collection(sub, parent_path=f"{collection}/{doc_id}",
                            order_by=order_by, direction=direction, limit=200)
