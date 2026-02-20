import requests
from tabulate import tabulate  

URL_RESTAURANTS = "http://localhost:5001"
URL_ORDERS = "http://localhost:5002"
URL_DELIVERY = "http://localhost:5003"


TOKEN = None

def print_table(data, headers):
    print("\n" + tabulate(data, headers=headers, tablefmt="grid"))

while True:
    print("\n" + "="*50)
    print("  FOOD DELIVERY SYSTEM")
    print("="*50)
    print("0) Ver restaurantes")
    print("1) Ver menú de restaurante")
    print("2) Crear orden")
    print("3) Confirmar orden")
    print("4) Crear delivery")
    print("5) Ver orden")
    print("6) Salir")
    print("="*50)

    c = input("> ")

    if c == "0":
        try:
            response = requests.get(f"{URL_RESTAURANTS}/restaurants", timeout=5)
            if response.status_code == 200:
                restaurants = response.json()
                table_data = []
                for restaurant in restaurants:
                    table_data.append([
                        restaurant.get("id_restaurante"),
                        restaurant.get("nombre"),
                        " Abierto" if restaurant.get("open") else " Cerrado"
                    ])
                print_table(table_data, ["ID", "Nombre", "Estado"])
            else:
                print(f" Error: {response.json()}")
        except requests.exceptions.RequestException as e:
            print(f" Error conectando con el servicio de restaurantes: {e}")

    # Ver menu de restaurante
    elif c == "1":
        restaurant_id = int(input("restaurant_id: "))
        try:
            response = requests.get(
                f"{URL_RESTAURANTS}/restaurants/{restaurant_id}/menu",timeout=5
            )
            if response.status_code == 200:
                menu = response.json()
                # Format as table
                table_data = []
                for item in menu:
                    table_data.append([
                        item["product_id"],
                        item["name"],
                        f"gs {float(item['price']):,.3f}",
                        "Disponible" if item["disponible"] else "No disponible"
                    ])
                print_table(table_data, ["ID", "Producto", "Precio", "Estado"])
            else:
                print(f" Error: {response.json()}")
                
        except requests.exceptions.RequestException as e:
            print(f" Error conectando con el servicio de restaurantes: {e}")

    # crear orden 
    elif c == "2":
        restaurant_id = int(input("\nrestaurant_id: "))
        
        
        try:
            response = requests.get(
                f"{URL_RESTAURANTS}/restaurants/{restaurant_id}/menu",
                timeout=5
            )
            if response.status_code == 200:
                menu = response.json()
                
                table_data = []
                for item in menu:
                    if item["disponible"]:
                        table_data.append([
                            item["product_id"],
                            item["name"],
                            f"gs {float(item['price']):,.3f}"
                        ])
                print("\n MENÚ DISPONIBLE:")
                print_table(table_data, ["ID", "Producto", "Precio"])
                
                
                items = []
                while True:
                    print("\n--- Agregar item ---")
                    product_id = input("product_id (exit para terminar): ")
                    if product_id.lower() == 'exit':
                        break
                    try:
                        product_id = int(product_id)
                        quantity = int(input("quantity: "))
                        items.append({"product_id": product_id, "quantity": quantity})
                        print(f"✓ Agregado: {quantity}x producto #{product_id}")
                    except ValueError:
                        print(" Entrada inválida")
                
                if not items:
                    print(" No se agregaron items")
                    continue
                
                
                print("\n RESUMEN DE ORDEN:")
                summary_data = []
                for item in items:
                    
                    menu_item = None

                    for m in menu:
                        if m["product_id"] == item["product_id"]:
                            menu_item = m
                            break
                    if menu_item:
                        price = float(menu_item["price"])
                        subtotal = price * item["quantity"]
                        summary_data.append([
                            item["quantity"],
                            menu_item["name"],
                            f"gs {price:,.3f}",
                            f"gs {subtotal:,.3f}"
                        ])
                print_table(summary_data, ["Cant.", "Producto", "Precio Unit.", "Subtotal"])
                
                confirm = input("\n¿Confirmar orden? (y/n): ")
                if confirm.lower() != 'y':
                    print(" Orden cancelada")
                    continue
                
                # Create order
                try:
                    response = requests.post(f"{URL_ORDERS}/orders",json={"restaurant_id": restaurant_id,"items": items},timeout=10
                    )
                    if response.status_code == 201:
                        order_data = response.json()
                        TOKEN = order_data.get("token")# SAVE TOKEN
                        
                        print("\n ORDEN CREADA EXITOSAMENTE")
                        print(f"Order ID: {order_data['order_id']}")
                        print(f"Total: gs {float(order_data['total']):,.3f}")
                        print(f"Status: {order_data['status']}")
                    
                    else:
                        print(f" Error: {response.json()}")
                except requests.exceptions.RequestException as e:
                    print(f" Error conectando con el servicio de órdenes: {e}")
            else:
                print(f" Error obteniendo menú: {response.json()}")
        except requests.exceptions.RequestException as e:
            print(f" Error conectando con el servicio de restaurantes: {e}")

    # confirmar orden 
    elif c == "3":
        if not TOKEN:
            print("  Error: No hay token disponible. Primero crea una orden.")
            continue
            
        order_id = int(input("order_id: "))
        response = requests.put(
            f"{URL_ORDERS}/orders/{order_id}",json={"status": "confirmed"},headers={"Authorization": TOKEN} 
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n Orden #{result['order_id']} confirmada")
            print(f"Nuevo status: {result['status']}")
        else:
            print(f" Error: {response.json()}")

    # ver orden 
    elif c == "5":
        if not TOKEN:
            print("  Error: No hay token disponible. Primero crea una orden.")
            continue
            
        order_id = int(input("order_id: "))
        response = requests.get(
            f"{URL_ORDERS}/orders/{order_id}",
            headers={"Authorization": TOKEN}  # ← ADD TOKEN HERE
        )
        
        if response.status_code == 200:
            order = response.json()
            
            print("\n" + "="*50)
            print(f"  ORDEN #{order['order_id']}")
            print("="*50)
            print(f"Restaurant ID: {order['restaurant_id']}")
            print(f"Status: {order['status'].upper()}")
            print(f"Total: gs {float(order['total']):,.3f}")
            print(f"Fecha: {order.get('created_at', 'N/A')}")
            
            # mostrar items en la tabla
            if order.get('items'):
                print("\nITEMS:")
                items_data = []
                for item in order['items']:
                    price = float(item['price'])
                    subtotal = price * item['quantity']
                    items_data.append([
                        item['product_id'],
                        item['quantity'],
                        f"gs {price:,.3f}",
                        f"gs {subtotal:,.3f}"
                    ])
                
                print_table(items_data, ["Producto ID", "Cantidad", "Precio", "Subtotal"])
            print("="*50)
        else:
            print(f" Error: {response.json()}")

    #crear delivery 
    elif c == "4":
        if not TOKEN:
            print("  Error: No hay token disponible. Primero crea una orden.")
            continue
            
        order_id = int(input("order_id: "))
        addr = input("direccion: ")

        response = requests.post(
            f"{URL_DELIVERY}/delivery",
            json={"order_id": order_id, "address": addr},
            headers={"Authorization": TOKEN}
        )
        
        if response.status_code == 201:
            delivery = response.json()
            print("\n DELIVERY CREADO")
            print(f"Delivery ID: {delivery['delivery_id']}")
            print(f"Order ID: {delivery['order_id']}")
            print(f"Status: {delivery['status']}")
        else:
            print(f" Error: {response.json()}")
    # closing the loop
    elif c == "6":
        print("\nthx <3")
        break