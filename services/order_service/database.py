import mysql.connector

def init_db():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=""
    )
    cursor = conn.cursor()
    
    # Create DB
    cursor.execute("CREATE DATABASE IF NOT EXISTS orders")
    cursor.execute("USE orders")
    
    # Create orders table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id INT AUTO_INCREMENT PRIMARY KEY,
        restaurant_id INT NOT NULL,
        status ENUM('created','confirmed','cancelled') DEFAULT 'created',
        total DECIMAL(10,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create order_items table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        item_id INT AUTO_INCREMENT PRIMARY KEY,
        order_id INT NOT NULL,
        product_id INT NOT NULL,
        quantity INT NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        CONSTRAINT fk_order FOREIGN KEY (order_id)
            REFERENCES orders(order_id)
            ON DELETE CASCADE
            ON UPDATE CASCADE
    )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()



def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="orders"
    )


def create_order(restaurant_id, total):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO orders (restaurant_id, total) VALUES (%s, %s)",
        (restaurant_id, total)
    )
    order_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return order_id


def add_order_item(order_id, product_id, quantity, price):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s,%s,%s,%s)",
        (order_id, product_id, quantity, price)
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_order_by_id(order_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
    order = cursor.fetchone()
    
    if not order:
        cursor.close()
        conn.close()
        return None
    
    cursor.execute(
        "SELECT product_id, quantity, price FROM order_items WHERE order_id = %s",
        (order_id,)
    )
    order["items"] = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return order


def update_order_status(order_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE orders SET status = %s WHERE order_id = %s",
        (status, order_id)
    )
    conn.commit()
    updated = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return updated



if __name__ == "__main__":
    init_db()
