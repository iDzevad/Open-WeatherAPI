import socket
import sqlite3
from datetime import datetime
import configparser

# Load configurations from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# IP and port of server
SERVER_IP = config['SERVER']['IP']
SERVER_PORT = config.getint('SERVER', 'PORT')

# Connect to SQLite database
db_conn = sqlite3.connect('sensor_data.db')
cursor = db_conn.cursor()

# Create a new table called second_sensor_data if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS second_sensor_data (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    humidity REAL,
    temperature REAL,
    light_level REAL
    )
''')
db_conn.commit()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    """
    Sets up the server to listen for incoming connections and handle received data.
    """
    # Bind the socket to the IP address and port
    s.bind((SERVER_IP, SERVER_PORT))
    print(f"Socket bound to port {SERVER_PORT}")

    # Listen for incoming connections
    s.listen()
    print("Listening for incoming connections...")

    # Accept connection
    client_conn, addr = s.accept()
    print('Connected by', addr)

    while True:
        # Receive raw data from the client
        raw_data: str = client_conn.recv(1024).decode().strip()
        print("Received raw data:", raw_data)

        if not raw_data:
            break

        # Divide the received raw data into humidity, temperature, and light_level
        try:
            data_parts: list = raw_data.split(',')
            if len(data_parts) != 3:
                raise ValueError("Invalid data format")
            
            humidity: float = float(data_parts[0])
            temperature: float = float(data_parts[1])
            light_level: float = float(data_parts[2])
        except ValueError:
            print("Invalid data format:", raw_data)
            continue

        timestamp: str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Store the parsed data in the database along with the formatted timestamp
        cursor.execute("INSERT INTO second_sensor_data (timestamp, humidity, temperature, light_level) VALUES (?, ?, ?, ?)",
                        (timestamp, humidity, temperature, light_level))
        db_conn.commit()
        print("Data stored in database:", timestamp, humidity, temperature, light_level)
