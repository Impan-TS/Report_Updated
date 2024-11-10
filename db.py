import pyodbc

# Database configuration
DB_SERVER = 'DESKTOP-BSC7DMC\SQLEXPRESS'
DB_DATABASE = 'tse_data'
DB_USER = 'sa'
DB_PASSWORD = 'tiger'

# Connection string
connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_SERVER};DATABASE={DB_DATABASE};UID={DB_USER};PWD={DB_PASSWORD}'

# SQL commands to create tables
create_admins_table_query = '''
CREATE TABLE admins (
   id INT PRIMARY KEY IDENTITY(1,1),
   username VARCHAR(100) NOT NULL,
   password VARCHAR(100) NOT NULL
);

ALTER TABLE admins ADD CONSTRAINT unique_tseeeeee_new_admins_usernames UNIQUE (username);

'''

create_users_table_query = '''
CREATE TABLE users (
   id INT PRIMARY KEY IDENTITY(1,1),
   username VARCHAR(100) NOT NULL,
   password VARCHAR(100) NOT NULL
);

ALTER TABLE users ADD CONSTRAINT unique_tseeeeee_new_users_usernames UNIQUE (username);

'''

# Function to execute SQL queries
def execute_query(query, values=None):
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        if values:
            cursor.execute(query, values)
        else:
            cursor.execute(query)
        conn.commit()
        print("Query executed successfully.")
    except Exception as e:
        print(f"Error executing query: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# Create the admins table
execute_query(create_admins_table_query)

# Create the users table
execute_query(create_users_table_query)

# Insert data into the admins table
insert_admin_query = "INSERT INTO admins (username, password) VALUES (?, ?)"
admin_values = ('tseadmin', 'tseadmin@123')
execute_query(insert_admin_query, admin_values)

# Insert data into the users table
insert_user_query = "INSERT INTO users (username, password) VALUES (?, ?)"
user_values = ('tseuser', 'tseuser@123')
execute_query(insert_user_query, user_values)
