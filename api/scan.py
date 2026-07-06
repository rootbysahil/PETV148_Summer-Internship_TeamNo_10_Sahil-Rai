import asyncio
import json
import time
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx

# Resolve signature path relative to function environment (api/ folder)
PLATFORMS_PATH = Path(__file__).parent / "platforms.json"


async def check_platform(client: httpx.AsyncClient, name: str, info: dict, username: str) -> dict:
    url = info["url"].format(username)
    error_type = info.get("errorType", "status_code")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    start = time.perf_counter()
    try:
        response = await client.get(url, headers=headers, timeout=6.0, follow_redirects=True)
        duration_ms = (time.perf_counter() - start) * 1000.0
        http_status = response.status_code
        status = "FOUND"

        if error_type == "status_code":
            err_status = info.get("errorStatus", 404)
            if http_status == err_status or http_status >= 400:
                status = "NOT_FOUND"
        elif error_type == "message":
            err_msg = info.get("errorMsg")
            if err_msg and err_msg in response.text:
                status = "NOT_FOUND"
        elif error_type == "response_url":
            main_url = info.get("urlMain", "")
            if main_url and str(response.url).rstrip("/") == main_url.rstrip("/"):
                status = "NOT_FOUND"

        return {
            "platform_name": name,
            "category": info.get("category", "other"),
            "profile_url": url,
            "status": status,
            "http_status": http_status,
            "response_time_ms": round(duration_ms, 2),
        }
    except Exception as e:
        duration_ms = (time.perf_counter() - start) * 1000.0
        return {
            "platform_name": name,
            "category": info.get("category", "other"),
            "profile_url": url,
            "status": "ERROR",
            "error_message": str(e),
            "response_time_ms": round(duration_ms, 2),
        }


async def run_scan(username: str):
    # Load signature definitions
    with open(PLATFORMS_PATH, encoding="utf-8") as f:
        platforms = json.load(f)

    # Set limited concurrency to avoid exceeding server memory or triggering remote shields
    semaphore = asyncio.Semaphore(15)

    async def bounded_check(client, name, info):
        async with semaphore:
            return await check_platform(client, name, info, username)

    async with httpx.AsyncClient() as client:
        tasks = [bounded_check(client, name, info) for name, info in platforms.items()]
        results = await asyncio.gather(*tasks)

    return results


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        username = query.get("username", [None])[0]

        if not username:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing 'username' parameter."}).encode("utf-8"))
            return

        try:
            # Execute async lookup chain
            results = asyncio.run(run_scan(username))

            # Statistics compilation
            total_checked = len(results)
            found = [r for r in results if r["status"] == "FOUND"]
            errors = [r for r in results if r["status"] in ("ERROR", "UNKNOWN")]

            category_breakdown = {}
            for r in found:
                cat = r["category"]
                category_breakdown[cat] = category_breakdown.get(cat, 0) + 1

            summary = {
                "username": username,
                "total_checked": total_checked,
                "total_found": len(found),
                "total_not_found": total_checked - len(found) - len(errors),
                "total_errors": len(errors),
                "success_rate_pct": round(
                    (len(found) / total_checked * 100.0) if total_checked > 0 else 0, 2
                ),
                "category_breakdown": category_breakdown,
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")  # Enable CORS
            self.end_headers()
            self.wfile.write(json.dumps({"summary": summary, "hits": results}).encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(
                json.dumps({"error": f"Internal scan error: {str(e)}"}).encode("utf-8")
            )
