import pyodbc
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash, make_response
from datetime import datetime, timedelta
from werkzeug.utils import redirect
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, ValidationError
import bcrypt

app = Flask(__name__)
app.secret_key = 'xyzsdfg'

# Database configuration
DB_SERVER = 'DESKTOP-BSC7DMC\SQLEXPRESS'
DB_DATABASE = 'tse_data'
DB_USER = 'sa'
DB_PASSWORD = 'tiger'

# Connection string
connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_SERVER};DATABASE={DB_DATABASE};UID={DB_USER};PWD={DB_PASSWORD}'


# # Function to create a connection
# def create_connection():
#     return pyodbc.connect(connection_string)

# Function to create a connection
def create_connection():
    while True:
        try:
            conn = pyodbc.connect(connection_string)
            return conn
        except pyodbc.Error as e:
            print(f"Error connecting to database: {e}")
            # Handle specific error cases if needed, or retry
            # Example: Handle specific error codes or types of errors
            # Check documentation for pyodbc for specific error handling

        except Exception as e:
            print(f"Unexpected error during connection: {e}")
            return None  # Handle other exceptions as needed

# Connect to the database
def connect_to_db():
    # conn_str = 'ODBC Driver 17 for SQL Server={SQL Server};SERVER=' + DESKTOP-BSC7DMCSQLEXPRESS + ';DATABASE=' + tse_data + ';UID=' + sa + ';PWD=' + tiger
    conn_str = 'DRIVER={SQL Server};SERVER=' + DB_SERVER + ';DATABASE=' + DB_DATABASE + ';UID=' + DB_USER + ';PWD=' + DB_PASSWORD
    return pyodbc.connect(conn_str)

# Fetch all table names from the database
def fetch_table_names(department):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_NAME LIKE ?", (department + '%',))
    table_names = [row.TABLE_NAME for row in cursor.fetchall()]
    conn.close()
    return table_names
    
# Fetch column names of the selected table
def fetch_column_names(table_name):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'")
    column_names = [row.COLUMN_NAME for row in cursor.fetchall()]
    conn.close()
    return column_names

@app.route('/')
def user_login():
    # Prevent caching of the userlogin.html page
    response = make_response(render_template('userlogin.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


# Fetch data based on department
def fetch_data_by_department(department, from_date, to_date, time_difference):
    table_prefixes = {
        'Blowroom': {'rh': 'br_rh', 'temp': 'br_temp'},
        'Preparatory': {'rh': 'prep_rh', 'temp': 'prep_temp'},
        'Spinning1': {'rh': 'spg1_rh', 'temp': 'spg1_temp'},
        'Spinning2': {'rh': 'spg2_rh', 'temp': 'spg2_temp'},
        'Winding': {'rh': 'wdg_rh', 'temp': 'wdg_temp'}
    }
    
    rh_table = table_prefixes[department]['rh']
    temp_table = table_prefixes[department]['temp']

    rh_columns = fetch_column_names(rh_table)
    temp_columns = fetch_column_names(temp_table)
    
    data = {
        'rh_columns': rh_columns,
        'temp_columns': temp_columns,
        'rh_data': fetch_data(rh_table, from_date, to_date, time_difference),
        'temp_data': fetch_data(temp_table, from_date, to_date, time_difference)
    }

    return data

# Fetch data from a specific table with time filtering
def fetch_data(table_name, from_date, to_date, time_difference):
    conn = connect_to_db()
    cursor = conn.cursor()

    # Parse input dates and adjust format
    from_date = datetime.strptime(from_date, "%Y-%m-%d").strftime("%Y/%m/%d")
    to_date = datetime.strptime(to_date, "%Y-%m-%d").strftime("%Y/%m/%d") + " 23:59:59"  # Set to the end of the selected day

    # Calculate time difference in minutes
    if time_difference == '10 minutes':
        time_difference_minutes = 10
    elif time_difference == '30 minutes':
        time_difference_minutes = 30
    elif time_difference == '1 hour':
        time_difference_minutes = 60
    elif time_difference == '2 hours':
        time_difference_minutes = 120
    elif time_difference == '5 hours':
        time_difference_minutes = 300
    elif time_difference == '1 Day':
        time_difference_minutes = 1440
    else:
        time_difference_minutes = 0  # Default to no time difference
    
    # Construct SQL query with proper date and time filtering
    query = f"SELECT * FROM {table_name} WHERE date >= ? AND date <= ? AND DATEDIFF(MINUTE, CAST('00:00:00' AS TIME), CAST(time AS TIME)) % ? = 0"
    cursor.execute(query, (from_date, to_date, time_difference_minutes))
    rows = cursor.fetchall()
    conn.close()

    data = []
    for row in rows:
        row_dict = dict(zip([column[0] for column in cursor.description], row))

        if 'time' in row_dict:
            # Convert time from string to datetime object
            row_dict['time'] = datetime.strptime(row_dict['time'], "%H:%M:%S").strftime("%H:%M:%S")
            
        for key, value in row_dict.items():
            if isinstance(value, float):
                row_dict[key]=round(value,2)

        data.append(row_dict)

    return data


@app.route('/report', methods=['GET', 'POST'])
def reportpage():
    # Check if the user is logged in
    if 'userloggedin' not in session:
        # If not logged in, redirect to the user login page
        return redirect(url_for('user_login'))

    if request.method == 'POST':
        # Handle the form submission
        department = request.form.get('department')
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')
        time_difference = request.form.get('time_difference')
        # You can perform any necessary processing here
        return redirect(url_for('user_login'))  # Redirect to the report page after form submission
    else:
        # Render the initial report page
        department_options = [' ', 'Blowroom', 'Preparatory', 'Spinning1', 'Spinning2', 'Winding']
        response = make_response(render_template('report.html', department_options=department_options))
        # Add cache-control header to prevent caching
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response


@app.route('/userlogin', methods=['GET', 'POST'])
def userlogin():
    # Check if the user is already logged in
    if 'userloggedin' in session:
        # If already logged in, redirect to the report page
        return redirect(url_for('reportpage'))

    # Your existing login code
    message = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        
        # Establish a database connection
        conn = create_connection()
        cursor = conn.cursor()
        
        # Use a case-sensitive collation for comparison
        cursor.execute("SELECT * FROM users WHERE username = ? COLLATE Latin1_General_CS_AS AND password = ?", (username, password,))
        user = cursor.fetchone()
        
        if user:
            session['userloggedin'] = True
            session['userid'] = user.id  # Assuming 'id' is the column name for the user ID
            session['username'] = user.username  # Assuming 'username' is the column name for the username
            message = 'Logged in successfully!'
            conn.close()  # Close the connection after use
            return redirect(url_for('reportpage'))
        else:
            # Close the connection in case of failure
            conn.close()
            # Display error message only when login attempt fails
            message = 'Invalid username or password'
            return render_template('userlogin.html', message=message)
    else:
        # Clear message variable when rendering login page without any error message
        message = ''
        # Prevent caching of the userlogin page
        response = make_response(render_template('userlogin.html', message=message))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response


@app.route('/data', methods=['POST'])
def get_data():
    department = request.form.get('department')
    if department not in ['Blowroom', 'Preparatory', 'Spinning1', 'Spinning2', 'Winding']:
        return jsonify({'error': 'Invalid department selected'})

    # Handle potential missing form data using get() with a default value
    from_date = request.form.get('from_date')
    to_date = request.form.get('to_date')
    time_difference = request.form.get('time_difference')

    if not from_date or not to_date:
        # Handle case where from_date or to_date is missing (e.g., display error message)
        return jsonify({'error': 'From date and To date are required'})

    # Retrieve selected fields
    selected_fields = request.form.get('selected_fields').split(',') if 'selected_fields' in request.form else []

    # Fetch data based on department, date range, and selected columns
    data = fetch_data_by_department(department, from_date, to_date, time_difference)

    # Filter data based on selected fields
    filtered_data = {}
    for key, value in data.items():
        if key.endswith('_columns'):
            filtered_data[key] = value
        elif key.endswith('_data'):
            filtered_data[key] = []
            for row in value:
                filtered_row = {}
                for column in selected_fields:
                    if column in row:
                        filtered_row[column] = row[column]
                filtered_data[key].append(filtered_row)

    return jsonify(data)


@app.route('/time-differences')
def get_time_differences():
    time_differences = ['10 minutes', '30 minutes', '1 hour', '2 hours', '5 hours', '1 Day']
    return jsonify({'time_differences': time_differences})


# Route to display users
@app.route('/users')
def index():
    # Check if the admin is logged in
    if 'loggedin' not in session:
        # If not logged in, redirect to the admin login page
        return redirect(url_for('login'))
    else:
        # If logged in, proceed to display users
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users")
        data = cursor.fetchall()
        cursor.close()
        connection.close()
        # Prevent caching of the /users route
        response = make_response(render_template('index.html', users=data))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    

@app.route('/addadmin')
def addadmin():
    # Check if the admin is logged in
    if 'loggedin' not in session:
        # If not logged in, redirect to the admin login page
        return redirect(url_for('login'))
    else:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM admins")
        data = cursor.fetchall()
        cursor.close()
        connection.close()
        # Prevent caching of the /addadmin route
        response = make_response(render_template('admin.html', admins=data))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # Check if the admin is logged in
    if 'loggedin' not in session:
        # If not logged in, redirect to the admin login page
        return redirect(url_for('login'))
    else:
        message = 'Welcome to the admin page!'
        response = make_response(render_template('adminpage.html', message=message))
        # Add cache-control header to prevent caching
        response.headers['Cache-Control'] = 'no-store'
        return response




# Route to insert a new user
@app.route('/insert', methods=['POST'])
def insert():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            connection.commit()
            flash("Data Inserted Successfully")
        except pyodbc.IntegrityError:
            flash("Username already exists. Please choose a different username.")
        finally:
            cursor.close()
            connection.close()
        return redirect(url_for('index'))


# Route to delete a user
@app.route('/delete/<string:id_data>', methods=['GET'])
def delete(id_data):
    flash("Record Has Been Deleted Successfully")
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM users WHERE id=?", (id_data,))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('index'))

@app.route('/update/<int:id_data>', methods=['POST'])
def update(id_data):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the new username already exists in the database
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND id != ?", (username, id_data))
        existing_user = cursor.fetchone()
        cursor.close()

        if existing_user:
            flash("Username already exists. Please choose a different username.", "error")
            return redirect(url_for('index'))

        # Perform the update operation
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE users SET username=?, password=?
        WHERE id=?
        """, (username, password, id_data))
        conn.commit()
        flash("Data Updated Successfully")
        conn.close()  # Close the connection after use
        return redirect(url_for('index'))
    
    
# Route to insert a new user
@app.route('/admininsert', methods=['POST'])
def admininsert():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute("INSERT INTO admins (username, password) VALUES (?, ?)", (username, password))
            connection.commit()
            flash("Data Inserted Successfully")
        except pyodbc.IntegrityError:
            flash("Username already exists. Please choose a different username.")
        finally:
            cursor.close()
            connection.close()
        return redirect(url_for('addadmin'))


# Route to delete a user
@app.route('/admindelete/<string:id_data>', methods=['GET'])
def admindelete(id_data):
    flash("Record Has Been Deleted Successfully")
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM admins WHERE id=?", (id_data,))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('addadmin'))


@app.route('/adminupdate/<int:id_data>', methods=['POST'])
def adminupdate(id_data):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the new username already exists in the database
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE username = ? AND id != ?", (username, id_data))
        existing_user = cursor.fetchone()
        cursor.close()

        if existing_user:
            flash("Username already exists. Please choose a different username.", "error")
            return redirect(url_for('addadmin'))

        # Perform the update operation
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE admins SET username=?, password=?
        WHERE id=?
        """, (username, password, id_data))
        conn.commit()
        flash("Data Updated Successfully")
        conn.close()  # Close the connection after use
        return redirect(url_for('addadmin'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        
        # Establish a database connection
        conn = create_connection()
        cursor = conn.cursor()
        
        # Use a case-sensitive collation for comparison
        cursor.execute("SELECT * FROM admins WHERE username = ? COLLATE Latin1_General_CS_AS AND password = ?", (username, password,))
        user = cursor.fetchone()
        
        if user:
            session['loggedin'] = True
            session['userid'] = user.id  # Assuming 'id' is the column name for the user ID
            session['username'] = user.username  # Assuming 'username' is the column name for the username
            message = 'Logged in successfully!'
            conn.close()  # Close the connection after use
            return redirect(url_for('admin'))
        
        else:
            # Close the connection in case of failure
            conn.close()
            # Display error message only when login attempt fails
            message = 'Invalid username or password'
            return render_template('login.html', message=message)
    else:
        # Clear message variable when rendering login page without any error message
        message = ''
        # Prevent caching of the login page
        response = make_response(render_template('login.html', message=message))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('username', None)
    
    # Create a response to prevent caching of the /admin page after logout
    response = make_response(redirect(url_for('login')))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/userlogout')
def userlogout():
    # Clear user session data
    session.pop('userloggedin', None)
    session.pop('userid', None)
    session.pop('username', None)

    response = make_response(redirect(url_for('userlogin')))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5001)
    
    
    


