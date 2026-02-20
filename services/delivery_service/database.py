import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password=""
)

cursor = conn.cursor()

cursor.execute("CREATE DATABASE IF NOT EXISTS delivery")
cursor.execute("USE delivery")



cursor.execute("""
CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    status ENUM('assigned','picked_up','on_the_way','delivered') DEFAULT 'assigned',
    address VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

""")

conn.commit()
cursor.close()
conn.close()
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="delivery"
    )


def create_delivery(order_id, address):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO deliveries (order_id, address)
        VALUES (%s, %s)
        """,
        (order_id, address)
    )

    delivery_id = cursor.lastrowid
    conn.commit()

    cursor.close()
    conn.close()
    return delivery_id


def get_delivery(delivery_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM deliveries WHERE delivery_id = %s",
        (delivery_id,)
    )

    delivery = cursor.fetchone()

    cursor.close()
    conn.close()
    return delivery


def update_delivery_status(delivery_id, status):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE deliveries SET status = %s WHERE delivery_id = %s",
        (status, delivery_id)
    )

    conn.commit()
    updated = cursor.rowcount > 0

    cursor.close()
    conn.close()
    return updated
