import serial
import socket
import configparser

# Load configurations from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Serial port configuration
SERIAL_PORT = config['SERIAL_PORT']['port']
BAUD_RATE = config.getint('SERIAL_PORT', 'baudrate')

# IP and port of server
SERVER_IP = config['SERVER']['ip']
SERVER_PORT = config.getint('SERVER', 'port')

with serial.Serial(SERIAL_PORT, BAUD_RATE) as ser:
    """
    Connects to the server and sends sensor data read from the serial port.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Connect to the server
        s.connect((SERVER_IP, SERVER_PORT))
        print(f"Connected to server at {SERVER_IP}:{SERVER_PORT}")

        while True:
            # Read data from serial port
            raw_data: str = ser.readline().decode().strip()
            print("Raw data:", raw_data)
            
            # Send raw data to the server
            s.sendall(raw_data.encode())
            print("Sent raw data:", raw_data)
            
            # Skip lines that don't contain valid sensor data
            if not raw_data.startswith("Humidity:") or ',' not in raw_data:
                continue
            
            # Make the data
            try:
                _, humidity_str, _, temperature_str, _, light_level_str = raw_data.split(',')
                humidity: float = float(humidity_str.split(':')[1].strip())
                temperature: float = float(temperature_str.split(':')[1].strip())
                light_level: float = float(light_level_str.split(':')[1].strip())
            except ValueError:
                print("Invalid data format:", raw_data)
                continue
            
            # Send data to the server
            message: str = f"Humidity: {humidity}%, Temperature: {temperature}°C, Light Level: {light_level}"
            s.sendall(message.encode())
            print("Sent parsed data:", message)
