import mysql.connector
import pandas as pd
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# MySQL database configuration - now using environment variables
MYSQL_CONFIG = {
    "host": os.getenv("DB_HOST", ""),
    "port": int(os.getenv("DB_PORT", "")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

def fetch_data_from_mysql(table_name="order_details"):
    """
    Fetch data from MySQL database and return as pandas DataFrame
    
    Args:
        table_name (str): Name of table to query
        
    Returns:
        pd.DataFrame: DataFrame containing table data or None if error occurs
    """
    try:
        # Establish connection using context manager
        with mysql.connector.connect(**MYSQL_CONFIG) as connection:
            with connection.cursor() as cursor:
                # Get column names
                cursor.execute(f"DESCRIBE {table_name}")
                columns = [column[0] for column in cursor.fetchall()]

                # Fetch data with parameterized query
                cursor.execute(f"SELECT * FROM {table_name}")
                data = cursor.fetchall()
                
                return pd.DataFrame(data, columns=columns)

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

if __name__ == "__main__":
    # Example usage
    df = fetch_data_from_mysql()
    if df is not None:
        print("Data fetched successfully:")
        print(df.head())
    else:
        print("Failed to fetch data")