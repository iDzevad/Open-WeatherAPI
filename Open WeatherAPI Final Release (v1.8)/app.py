import os
import yaml
from flask import Flask, render_template, request, redirect, url_for, session, g, send_file, Response
import sqlite3
import uuid
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, Union, List, Any, Optional
import configparser
import base64
from hashlib import pbkdf2_hmac
from statistics import mean

app: Flask = Flask(__name__)

# Load configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

DATABASE: str = config['DATABASE']['path']

log_directory: str = config['LOGGING']['directory']
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

log_file: str = os.path.join(log_directory, config['LOGGING']['file'])
maxBytes: int = config.getint('LOGGING', 'maxBytes')
backupCount: int = config.getint('LOGGING', 'backupCount')

log_handler: RotatingFileHandler = RotatingFileHandler(log_file, maxBytes=maxBytes, backupCount=backupCount)
log_handler.setLevel(logging.INFO)
formatter: logging.Formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)

app.logger.addHandler(log_handler)
app.logger.setLevel(logging.INFO)

# Set Flask application's secret key
app.secret_key = config['FLASK']['secret_key']

# Constants for PBKDF2
salt_length = config.getint('PBKDF2', 'salt_length')
hash_name = config['PBKDF2']['hash_name']
iterations = config.getint('PBKDF2', 'iterations')
dk_length = config.getint('PBKDF2', 'dk_length')

def hash_password(password: str) -> str:
    # Generate a random salt
    salt = os.urandom(salt_length)
    # Generate the hash using PBKDF2
    hashed_password = pbkdf2_hmac(hash_name, password.encode(), salt, iterations, dklen=dk_length)
    # Combine the salt and the hash for storage
    stored_password = base64.b64encode(salt + hashed_password).decode('utf-8')
    return stored_password

def verify_password(stored_password: str, provided_password: str) -> bool:
    # Decode the stored password
    stored_password_bytes = base64.b64decode(stored_password)
    # Extract the salt from the stored password
    salt = stored_password_bytes[:salt_length]
    # Extract the stored hash from the stored password
    stored_hash = stored_password_bytes[salt_length:]
    # Hash the provided password using the same salt
    provided_hash = pbkdf2_hmac(hash_name, provided_password.encode(), salt, iterations, dklen=dk_length)
    # Compare the stored hash with the provided hash
    return stored_hash == provided_hash

@app.before_request
def log_request_info() -> None:
    """
    Logs information about incoming requests.
    """
    if request.method in ['GET', 'POST']:
        app.logger.info('Request: %s %s', request.method, request.url)

@app.after_request
def log_response_info(response: Response) -> Response:
    """
    Logs information about outgoing responses.
    """
    if request.method in ['GET', 'POST']:
        if response.direct_passthrough:
            response_info: str = '[direct passthrough]'
        else:
            response_info: str = '[data]'
        app.logger.info('Response: %s %s', response.status, response_info)
    return response

def get_db_connection() -> sqlite3.Connection:
    """
    Establishes a database connection if one does not exist.
    
    Returns:
        sqlite3.Connection: The database connection.
    """
    if 'db_connection' not in g:
        g.db_connection = sqlite3.connect(DATABASE)
        g.db_connection.row_factory = sqlite3.Row
    return g.db_connection

@app.route('/apiSpec')
def api_spec() -> Response:
    """
    Serves the OpenAPI YAML documentation.
    """
    return send_file('apiSpec.yaml', mimetype='text/yaml')

@app.teardown_appcontext
def close_db_connection(exception: Optional[Exception] = None) -> None:
    """
    Closes the database connection at the end of the request.
    """
    db_connection: Optional[sqlite3.Connection] = g.pop('db_connection', None)
    if db_connection is not None:
        db_connection.close()

def generate_routes_from_spec() -> None:
    """
    Generates routes from the OpenAPI specification.
    """
    with open('specifications/apiSpec.yaml', 'r') as file:
        spec: Dict[str, Any] = yaml.safe_load(file)
        paths: Dict[str, Dict[str, Any]] = spec.get('paths', {})
        for path, methods in paths.items():
            for method in methods.keys():
                # Use fixed endpoint names for specific routes
                if path == '/login':
                    endpoint_name: str = 'login'
                elif path == '/register':
                    endpoint_name: str = 'register'
                elif path == '/':
                    endpoint_name: str = 'index'
                elif path == '/sensor_graph':
                    endpoint_name: str = 'sensor_graph'
                elif path == '/sensor_data':
                    endpoint_name: str = 'get_sensor_data'
                else:
                    # Generate a unique name for other paths
                    endpoint_name: str = f"{method.lower()}_{path.replace('/', '').replace(' ', '_')}_{uuid.uuid4().hex}"

                if path == '/':
                    def route_handler_home() -> Any:
                        """
                        Renders the home page.
                        """
                        return render_template('index.html')
                    app.add_url_rule(path, view_func=route_handler_home, methods=[method], endpoint=endpoint_name)

                elif path == '/sensor_graph':
                    def route_handler_sensor_graph() -> Any:
                        """
                        Renders the sensor graph page with sensor data.
                        """
                        conn: sqlite3.Connection = get_db_connection()
                        cursor: sqlite3.Cursor = conn.cursor()
                        cursor.execute("SELECT timestamp, temperature, humidity, light_level FROM sensor_data")
                        rows: List[sqlite3.Row] = cursor.fetchall()
                        conn.close()
                        timestamps: List[str] = [row['timestamp'] for row in rows]
                        temperatures: List[float] = [row['temperature'] for row in rows]
                        humidity: List[float] = [row['humidity'] for row in rows]
                        light_level: List[float] = [row['light_level'] for row in rows]

                        # Calculate average temperature
                        avg_temperature = mean(temperatures)
                        avg_humidity = mean(humidity)
                        avg_light_level = mean(light_level)

                        avg_temperature = round(avg_temperature, 2)
                        avg_humidity = round(avg_humidity, 2)
                        avg_light_level = round(avg_light_level, 2)

                        return render_template('sensor_graph.html', 
                                                timestamps=timestamps, 
                                                temperatures=temperatures, 
                                                humidity=humidity, 
                                                light_level=light_level,
                                                avg_humidity=avg_humidity,
                                                avg_light_level=avg_light_level,
                                                avg_temperature=avg_temperature)  # Pass avg_temperature to the template
                    app.add_url_rule(path, view_func=route_handler_sensor_graph, methods=[method], endpoint=endpoint_name)

                elif path == '/login':
                    def route_handler_login() -> Any:
                        """
                        Handles user login.
                        """
                        error: Optional[str] = None
                        if request.method == 'POST':
                            username: str = request.form['username']
                            password: str = request.form['password']
                            conn: sqlite3.Connection = get_db_connection()
                            cursor: sqlite3.Cursor = conn.cursor()
                            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
                            user: Optional[sqlite3.Row] = cursor.fetchone()
                            conn.close()
                            if user is not None and verify_password(user['password'], password):
                                session['username'] = username
                                return redirect(url_for('get_sensor_data'))
                            else:
                                error = 'Invalid username or password.'
                        return render_template('login.html', error=error)
                    app.add_url_rule(path, view_func=route_handler_login, methods=['GET', 'POST'], endpoint=endpoint_name)

                elif path == '/register':
                    def route_handler_register() -> Any:
                        """
                        Handles user registration.
                        """
                        error: Optional[str] = None
                        if request.method == 'POST':
                            username: str = request.form['username']
                            password: str = request.form['password']
                            hashed_password = hash_password(password)
                            conn: sqlite3.Connection = get_db_connection()
                            cursor: sqlite3.Cursor = conn.cursor()
                            try:
                                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
                                conn.commit()
                                return redirect(url_for('login'))
                            except sqlite3.IntegrityError:
                                error = 'Username already exists. Please choose a different username.'
                            finally:
                                conn.close()
                        return render_template('register.html', error=error)
                    app.add_url_rule(path, view_func=route_handler_register, methods=['GET', 'POST'], endpoint=endpoint_name)

                elif path == '/sensor_data':
                    def route_handler_sensor_data() -> Any:
                        """
                        Fetches and displays the latest sensor data.
                        """
                        sensor_data: Optional[Dict[str, Union[int, str, float]]] = None
                        second_sensor_data: Optional[Dict[str, Union[int, str, float]]] = None
                        conn: sqlite3.Connection = get_db_connection()
                        cursor: sqlite3.Cursor = conn.cursor()
                        cursor.execute('SELECT id, timestamp, humidity, temperature, light_level FROM sensor_data ORDER BY id DESC LIMIT 1')
                        row: Optional[sqlite3.Row] = cursor.fetchone()
                        if row is not None:
                            sensor_data = {
                                'id': row['id'],
                                'timestamp': row['timestamp'],
                                'humidity': row['humidity'],
                                'temperature': row['temperature'],
                                'light_level': row['light_level']
                            }
                        cursor.execute('SELECT id, timestamp, humidity, temperature, light_level FROM second_sensor_data ORDER BY id DESC LIMIT 1')
                        row = cursor.fetchone()
                        if row is not None:
                            second_sensor_data = {
                                'id': row['id'],
                                'timestamp': row['timestamp'],
                                'humidity': row['humidity'],
                                'temperature': row['temperature'],
                                'light_level': row['light_level']
                            }
                        conn.close()
                        return render_template('sensor_data.html', sensor_data=sensor_data, second_sensor_data=second_sensor_data)
                    app.add_url_rule(path, view_func=route_handler_sensor_data, methods=[method], endpoint=endpoint_name)

# Call this function to generate routes from the OpenAPI spec
generate_routes_from_spec()

if __name__ == '__main__':
    app.run(debug=True)
