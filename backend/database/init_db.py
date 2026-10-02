from backend.database.database import get_connection


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS websites (
            id SERIAL PRIMARY KEY,
            url TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitoring_checks (
            id SERIAL PRIMARY KEY,
            website_id INTEGER NOT NULL,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status_code INTEGER,
            response_time_ms INTEGER,
            is_successful BOOLEAN NOT NULL,
            error_message TEXT,

            CONSTRAINT fk_website
                FOREIGN KEY (website_id)
                REFERENCES websites(id)
                ON DELETE CASCADE
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    initialize_database()
    print("CloudPulse database tables created successfully")
    