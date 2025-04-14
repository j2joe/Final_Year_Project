from dotenv import load_dotenv
import mysql.connector
import os

load_dotenv()  # Load environment variables from .env file

def database_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('mysql_host'),
            port=os.getenv('mysql_port'),
            user=os.getenv('mysql_user'),
            password=os.getenv('mysql_password'),
            database=os.getenv('mysql_database')
        )
        return connection
    except Exception as e:
        print("Database connection failed:", e)
        return None