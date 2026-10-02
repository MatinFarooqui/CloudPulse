import time
import threading
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.database.database import get_connection

from fastapi.responses import FileResponse

app = FastAPI()


class AnalyzeRequest(BaseModel):
    url: str


class MonitorRequest(BaseModel):
    url: str


@app.get("/")
def home():
    return FileResponse("frontend/index.html")


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.post("/analyze")
def analyze_website(request: AnalyzeRequest):

    url = request.url.strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed_url = urlparse(url)

    if not parsed_url.netloc:
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid website URL."
        )

    try:
        start_time = time.perf_counter()

        response = httpx.get(
            url,
            follow_redirects=True,
            timeout=10
        )

        end_time = time.perf_counter()

        response_time = round(
            end_time - start_time,
            3
        )

        content_type = response.headers.get(
            "content-type",
            "Unknown"
        )

        page_title = "Not available"

        if "text/html" in content_type.lower():

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            if soup.title:
                page_title = soup.title.get_text(
                    strip=True
                )

        return {
            "url": url,
            "status_code": response.status_code,
            "response_time_seconds": response_time,
            "page_title": page_title,
            "content_type": content_type,
            "https": parsed_url.scheme == "https"
        }

    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Could not reach the website."
        )


@app.post("/monitor")
def add_to_monitor(request: MonitorRequest):

    url = request.url.strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed_url = urlparse(url)

    if not parsed_url.netloc:
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid website URL."
        )

    conn = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO websites (url)
            VALUES (%s)
            ON CONFLICT (url) DO NOTHING
            RETURNING id, url, created_at, is_active;
            """,
            (url,)
        )

        result = cursor.fetchone()

        conn.commit()
        cursor.close()

        if result is None:
            return {
                "message": "Website is already being monitored",
                "url": url
            }

        return {
            "message": "Website added to monitoring",
            "id": result[0],
            "url": result[1],
            "created_at": result[2],
            "is_active": result[3]
        }

    except Exception:
        if conn:
            conn.rollback()

        raise HTTPException(
            status_code=500,
            detail="Could not add website to monitoring."
        )

    finally:
        if conn:
            conn.close()


@app.get("/monitors")
def get_monitors():

    conn = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, url, created_at, is_active
            FROM websites
            ORDER BY created_at DESC;
            """
        )

        rows = cursor.fetchall()

        cursor.close()

        monitors = []

        for row in rows:
            monitors.append({
                "id": row[0],
                "url": row[1],
                "created_at": row[2],
                "is_active": row[3]
            })

        return {
            "monitors": monitors
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve monitored websites."
        )

    finally:
        if conn:
            conn.close()


@app.post("/monitors/{website_id}/check")
def check_website(website_id: int):

    conn = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, url
            FROM websites
            WHERE id = %s AND is_active = TRUE;
            """,
            (website_id,)
        )

        website = cursor.fetchone()

        if website is None:
            raise HTTPException(
                status_code=404,
                detail="Website not found."
            )

        url = website[1]

        start_time = time.perf_counter()

        try:
            response = httpx.get(
                url,
                follow_redirects=True,
                timeout=10
            )

            end_time = time.perf_counter()

            response_time_ms = round(
                (end_time - start_time) * 1000
            )

            is_successful = response.status_code < 400
            status_code = response.status_code
            error_message = None

        except httpx.RequestError as error:
            end_time = time.perf_counter()

            response_time_ms = round(
                (end_time - start_time) * 1000
            )

            is_successful = False
            status_code = None
            error_message = str(error)

        cursor.execute(
            """
            INSERT INTO monitoring_checks (
                website_id,
                status_code,
                response_time_ms,
                is_successful,
                error_message
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, checked_at;
            """,
            (
                website_id,
                status_code,
                response_time_ms,
                is_successful,
                error_message
            )
        )

        check = cursor.fetchone()

        conn.commit()
        cursor.close()

        return {
            "website_id": website_id,
            "url": url,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "is_successful": is_successful,
            "checked_at": check[1],
            "error_message": error_message
        }

    except HTTPException:
        raise

    except Exception:
        if conn:
            conn.rollback()

        raise HTTPException(
            status_code=500,
            detail="Could not complete website check."
        )

    finally:
        if conn:
            conn.close()

@app.get("/monitors/{website_id}/checks")
def get_monitoring_history(website_id: int):

    conn = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, checked_at, status_code,
                   response_time_ms, is_successful, error_message
            FROM monitoring_checks
            WHERE website_id = %s
            ORDER BY checked_at DESC;
            """,
            (website_id,)
        )

        rows = cursor.fetchall()

        cursor.close()

        checks = []

        for row in rows:
            checks.append({
                "id": row[0],
                "checked_at": row[1],
                "status_code": row[2],
                "response_time_ms": row[3],
                "is_successful": row[4],
                "error_message": row[5]
            })

        return {
            "website_id": website_id,
            "checks": checks
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve monitoring history."
        )

    finally:
        if conn:
            conn.close()

@app.get("/monitors/{website_id}/stats")
def get_monitoring_stats(website_id: int):

    conn = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT url
            FROM websites
            WHERE id = %s;
            """,
            (website_id,)
        )

        website = cursor.fetchone()

        if website is None:
            raise HTTPException(
                status_code=404,
                detail="Website not found."
            )

        cursor.execute(
            """
            SELECT
                COUNT(*),
                COUNT(*) FILTER (WHERE is_successful = TRUE),
                COUNT(*) FILTER (WHERE is_successful = FALSE),
                AVG(response_time_ms),
                MIN(response_time_ms),
                MAX(response_time_ms)
            FROM monitoring_checks
            WHERE website_id = %s;
            """,
            (website_id,)
        )

        stats = cursor.fetchone()

        total_checks = stats[0] or 0
        successful_checks = stats[1] or 0
        failed_checks = stats[2] or 0

        average_response_time = round(
            float(stats[3]), 2
        ) if stats[3] is not None else 0

        minimum_response_time = stats[4] or 0
        maximum_response_time = stats[5] or 0

        uptime_percentage = round(
            (successful_checks / total_checks) * 100,
            2
        ) if total_checks > 0 else 0

        cursor.execute(
            """
            SELECT
                status_code,
                response_time_ms,
                is_successful,
                checked_at
            FROM monitoring_checks
            WHERE website_id = %s
            ORDER BY checked_at DESC
            LIMIT 1;
            """,
            (website_id,)
        )

        last_check = cursor.fetchone()

        current_status = "Unknown"

        if last_check:
            if not last_check[2]:
                current_status = "Down"
            elif last_check[1] >= 1000:
                current_status = "Degraded"
            else:
                current_status = "Healthy"

        cursor.close()

        return {
            "website_id": website_id,
            "url": website[0],
            "current_status": current_status,
            "uptime_percentage": uptime_percentage,
            "total_checks": total_checks,
            "successful_checks": successful_checks,
            "failed_checks": failed_checks,
            "average_response_time_ms": average_response_time,
            "minimum_response_time_ms": minimum_response_time,
            "maximum_response_time_ms": maximum_response_time,
            "last_check": (
                {
                    "status_code": last_check[0],
                    "response_time_ms": last_check[1],
                    "is_successful": last_check[2],
                    "checked_at": last_check[3]
                }
                if last_check else None
            )
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve monitoring statistics."
        )

    finally:
        if conn:
            conn.close()

def automatic_monitoring():
    while True:

        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, url
                FROM websites
                WHERE is_active = TRUE;
                """
            )

            websites = cursor.fetchall()

            cursor.close()
            conn.close()

            for website_id, url in websites:

                try:
                    start_time = time.perf_counter()

                    response = httpx.get(
                        url,
                        follow_redirects=True,
                        timeout=10
                    )

                    end_time = time.perf_counter()

                    response_time_ms = round(
                        (end_time - start_time) * 1000
                    )

                    status_code = response.status_code
                    is_successful = status_code < 400
                    error_message = None

                except httpx.RequestError as error:

                    end_time = time.perf_counter()

                    response_time_ms = round(
                        (end_time - start_time) * 1000
                    )

                    status_code = None
                    is_successful = False
                    error_message = str(error)

                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO monitoring_checks (
                        website_id,
                        status_code,
                        response_time_ms,
                        is_successful,
                        error_message
                    )
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (
                        website_id,
                        status_code,
                        response_time_ms,
                        is_successful,
                        error_message
                    )
                )

                conn.commit()
                cursor.close()
                conn.close()

        except Exception as error:
            print("Automatic monitoring:", error)

        time.sleep(60)


monitor_thread = threading.Thread(
    target=automatic_monitoring,
    daemon=True
)

monitor_thread.start()