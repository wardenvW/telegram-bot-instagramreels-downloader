import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    database_url = os.getenv('DATABASE_URL')

    if(database_url):
        return psycopg2.connect(database_url, sslmode='require')
    


