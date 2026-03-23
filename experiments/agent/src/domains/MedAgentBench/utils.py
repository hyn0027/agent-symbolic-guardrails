import requests
from typing import Dict


def send_get_request(url, params=None, headers=None) -> Dict:
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # Raises an HTTPError if the response code is 4xx or 5xx
        return {
            "status_code": response.status_code,
            "data": (
                response.json()
                if response.headers.get("Content-Type") == "application/json"
                else response.text
            ),
        }
    except Exception as e:
        return {"error": str(e)}
