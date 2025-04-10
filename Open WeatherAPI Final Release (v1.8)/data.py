import serial
import sqlite3
from typing import Any
import configparser
from datetime import datetime

def create_table(cursor: sqlite3.Cursor) -> None:
    """
    Creates sensor_data and users tables if they do not exist.
    Also creates the average_data table to store calculated averages.
    """
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
        id INTEGER PRIMARY KEY,
        timestamp TEXT,
        humidity REAL,
        temperature REAL,
        light_level REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS average_data (
        id INTEGER PRIMARY KEY,
        average_humidity REAL,
        average_temperature REAL,
        average_light_level REAL
        )
    ''')

    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_average_data
        AFTER INSERT ON sensor_data
        BEGIN
            DELETE FROM average_data;
            INSERT INTO average_data (average_humidity, average_temperature, average_light_level)
            SELECT ROUND(AVG(humidity), 2), ROUND(AVG(temperature), 2), ROUND(AVG(light_level), 2)
            FROM sensor_data;
        END;
    ''')

def insert_data(cursor: sqlite3.Cursor, humidity: float, temperature: float, light_level: float) -> None:
    """
    Inserts data into the sensor_data table.
    """
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO sensor_data (timestamp, humidity, temperature, light_level) VALUES (?, ?, ?, ?)
    ''', 
        (current_time, humidity, temperature, light_level))

def insert_user(cursor: sqlite3.Cursor, username: str, password: str) -> None:
    """
    Inserts user data into the users table.
    """
    cursor.execute('''
        INSERT INTO users (username, password) VALUES (?, ?)
    ''', 
        (username, password))

def main() -> None:
    """
    Main function to create tables and read data from the serial port.
    """
    # Load configurations from config.ini
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Connect to SQLite database
    db_path: str = config['DATABASE']['path']
    conn: sqlite3.Connection = sqlite3.connect(db_path)
    cursor: sqlite3.Cursor = conn.cursor()
    
    # Create tables
    create_table(cursor)
    conn.commit()

    try:
        # Attempt to open serial port
        serial_port: str = config['SERIAL_PORT']['port']
        baudrate: int = config.getint('SERIAL_PORT', 'baudrate')
        ser: Any = serial.Serial(serial_port, baudrate)
    except serial.SerialException:
        print("Failed to open serial port. Continuing without it...")
        ser = None

    if ser:
        try:
            while True:
                data: str = ser.readline().decode('latin-1').strip()
                print("Received at", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ":", data)

                if 'Loading measurements...' in data:
                    continue
                
                humidity, temperature, light_level = map(float, data.split(','))
                
                # Insert data into the sensor_data table
                insert_data(cursor, humidity, temperature, light_level)
                conn.commit()
        
        except KeyboardInterrupt:
            print("Stopping...")
        
        finally:
            conn.close()
    else:
        # If serial port is not available just exit
        conn.close()

if __name__ == "__main__":
    main()
