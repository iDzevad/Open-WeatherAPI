import sqlite3
import time
import logging
from datetime import datetime
import os

# Ensure the logging directory exists
LOGGING_DIR = 'logging'
os.makedirs(LOGGING_DIR, exist_ok=True)

# Configure logging
LOG_FILE = os.path.join(LOGGING_DIR, 'cleanup.log')
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Path to the database
DB_PATH = 'sensor_data.db'

def delete_oldest_records(cursor: sqlite3.Cursor, table_name: str, record_limit: int = 100) -> None:
    """
    Deletes the oldest records from the specified table.
    
    Parameters:
    cursor (sqlite3.Cursor): The cursor object.
    table_name (str): The name of the table from which to delete records.
    record_limit (int): The number of oldest records to delete.
    """
    cursor.execute(f'''
        DELETE FROM {table_name} WHERE id IN (
        SELECT id 
        FROM {table_name} 
        ORDER BY timestamp 
        LIMIT ?
        )
    ''', (record_limit,))
    logging.info(f'Deleted {record_limit} oldest records from {table_name}')

def main() -> None:
    """
    Main function to periodically delete the oldest records from the database tables.
    """
    while True:
        try:
            conn: sqlite3.Connection = sqlite3.connect(DB_PATH)
            cursor: sqlite3.Cursor = conn.cursor()

            # Delete oldest records from sensor_data table
            delete_oldest_records(cursor, 'sensor_data')

            # Delete oldest records from second_sensor_data table
            delete_oldest_records(cursor, 'second_sensor_data')

            # Commit changes
            conn.commit()
            logging.info('Oldest records deleted successfully')

        except sqlite3.Error as e:
            logging.error(f"SQLite error: {e}")
        finally:
            conn.close()

        # Wait for 1 hour
        time.sleep(3600)

if __name__ == "__main__":
    logging.info('Cleanup script started')
    main()
