import mysql.connector

# -----------------------------
# INITIALIZATION (run once)
# -----------------------------
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password=""
)

cursor = conn.cursor()

# Create database
cursor.execute("CREATE DATABASE IF NOT EXISTS restaurants")
cursor.execute("USE restaurants")

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS restaurante (
    id_restaurante INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100),
    open BOOLEAN
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS menu (
    id_item INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255),
    price DECIMAL(10,2),
    disponible BOOLEAN,
    id_restaurante INT,
    CONSTRAINT fk_restaurante FOREIGN KEY (id_restaurante)
        REFERENCES restaurante(id_restaurante)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
""")

conn.commit()
cursor.close()
conn.close()


# -----------------------------
# RUNTIME FUNCTIONS
# -----------------------------

def get_connection():
    """Get a new connection to the restaurants DB"""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="restaurants"
    )


def get_menu(restaurant_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    # Pass restaurant_id as a tuple
    cursor.execute("SELECT * FROM menu WHERE id_restaurante = %s", (restaurant_id,))
    menu = cursor.fetchall()
    cursor.close()
    conn.close()
    return menu


def get_restaurant():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM restaurante")
    restaurants = cursor.fetchall()
    cursor.close()
    conn.close()
    return restaurants
