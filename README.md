CloudPulse
Website Intelligence & Monitoring Platform
CloudPulse is a Python-based website intelligence and monitoring platform that analyzes public websites, measures response performance, and continuously tracks website health over time.
Features
- Analyze any public website URL
- HTTP status detection
- Response-time measurement
- Page title detection
- HTTPS detection
- Content-type detection
- Add websites to monitoring
- Manual website health checks
- Automatic health checks every 60 seconds
- Monitoring history
- Uptime percentage
- Successful and failed check statistics
- Average, minimum, and maximum response time
- Healthy / Degraded / Down status classification
- Response-time history visualization
- PostgreSQL data persistence
- REST APIs using FastAPI
- Responsive browser dashboard
Tech Stack
Application
- Python
- FastAPI
- PostgreSQL
- HTTPX
- BeautifulSoup
- HTML
- CSS
- JavaScript
Development
- Docker
- Docker Compose
- Git
- GitHub
Architecture
                    USER
                      |
                      v
             +----------------+
             |  CloudPulse UI |
             +--------+-------+
                      |
                      v
             +----------------+
             | FastAPI Backend|
             +--------+-------+
                      |
          +-----------+-----------+
          |                       |
          v                       v
   +-------------+        +---------------+
   | PostgreSQL  |        | Website Check |
   +-------------+        +-------+-------+
                                  |
                                  v
                           Public Websites

How It Works
1. User enters a public website URL.
2. CloudPulse sends an HTTP request to analyze the website.
3. The backend collects HTTP status, response time, HTTPS status, page title, and content type.
4. The user can add the website to monitoring.
5. Website details and monitoring results are stored in PostgreSQL.
6. CloudPulse performs automatic health checks every 60 seconds.
7. Each check is stored as historical monitoring data.
8. The dashboard displays uptime, response-time statistics, website status, and response-time history.
Health Status Rules
CloudPulse uses a simple rule-based status classification:
Failed check
    → Down

Successful check + response time >= 1 second
    → Degraded

Successful check + response time < 1 second
    → Healthy

This classification is specific to CloudPulse and is not an industry-standard health score.
Local Setup
1. Create a virtual environment
python -m venv .venv

Activate it:
.venv\Scripts\activate

2. Install dependencies
python -m pip install -r requirements.txt

3. Configure environment variables
Create a .env file in the project root:
POSTGRES_DB=cloudpulse
POSTGRES_USER=cloudpulse
POSTGRES_PASSWORD=your_password

4. Start PostgreSQL
Make sure Docker Desktop is running:
docker compose up -d

5. Initialize the database
python -m backend.database.init_db

6. Start CloudPulse
uvicorn backend.main:app --reload

Open the application:
http://127.0.0.1:8000/

API documentation:
http://127.0.0.1:8000/docs

Environment Variables
Database credentials are stored in .env and excluded from Git through .gitignore.
Example:
POSTGRES_DB=cloudpulse
POSTGRES_USER=cloudpulse
POSTGRES_PASSWORD=your_password

Security Note
CloudPulse accepts user-supplied URLs, which introduces potential Server-Side Request Forgery (SSRF) risks.
The current implementation is intended for local development and portfolio demonstration. A production deployment should validate requested destinations and prevent access to localhost, private/internal networks, and other restricted destinations.
Screenshots
Screenshots of the CloudPulse dashboard and monitoring interface will be added here.
Author
Matinoddin Farooqui
GitHub: MatinFarooqui