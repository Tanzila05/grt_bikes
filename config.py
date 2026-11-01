
import os

MYSQL_HOST = os.getenv(
    "MYSQL_HOST",
    "gateway01.us-west-2.prod.aws.tidbcloud.com"
)

MYSQL_USER = os.getenv("MYSQL_USER")

MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")

# Use the database where you imported your three tables
MYSQL_DB = os.getenv("MYSQL_DB", "grt_bikes_erp")

MYSQL_PORT = int(os.getenv("MYSQL_PORT", "4000"))

MYSQL_SSL_CA = os.getenv("MYSQL_SSL_CA", "")
