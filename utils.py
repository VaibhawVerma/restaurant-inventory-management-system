import pymysql
import pymysql.cursors
import hashlib
from datetime import date

# --- Database Connection ---
def connect_db():
    """Establishes a connection to the database."""
    try:
        return pymysql.connect(
            host='localhost',
            user='root',
            password='java0603', 
            database='restaurant-inventory-db',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False 
        )
    except pymysql.Error:
        return None

# --- Employee Management Functions ---

def get_all_employees():
    conn = connect_db()
    if not conn: return []
    try:
        with conn.cursor() as cursor:
            sql = "SELECT e.id, e.fname, e.lname, e.role, e.email, u.username FROM employee e LEFT JOIN user_account u ON e.uid = u.uid ORDER BY e.id"
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        if conn: conn.close()

def add_employee(details):
    conn = connect_db()
    if not conn: return "Database connection failed."
    try:
        with conn.cursor() as cursor:
            password_hash = hashlib.sha256(details['password'].encode()).hexdigest()
            sql_user = "INSERT INTO user_account (username, password_hash) VALUES (%s, %s)"
            cursor.execute(sql_user, (details['username'], password_hash))
            user_id = cursor.lastrowid
            sql_employee = "INSERT INTO employee (fname, lname, email, role, uid) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql_employee, (details['fname'], details['lname'], details['email'], details['role'], user_id))
            conn.commit()
        return "Employee added successfully!"
    except pymysql.IntegrityError as e:
        conn.rollback()
        if 'username' in str(e): return "Error: This username is already taken."
        if 'email' in str(e): return "Error: This email address is already in use."
        return f"Database Error: {e}"
    finally:
        if conn: conn.close()

def update_employee(emp_id, details):
    conn = connect_db()
    if not conn: return "Database connection failed."
    try:
        with conn.cursor() as cursor:
            sql = "UPDATE employee SET fname = %s, lname = %s, email = %s, role = %s WHERE id = %s"
            cursor.execute(sql, (details['fname'], details['lname'], details['email'], details['role'], emp_id))
            conn.commit()
        return "Employee updated successfully!"
    except pymysql.IntegrityError:
        conn.rollback()
        return "Error: The email address may already be in use by another employee."
    finally:
        if conn: conn.close()

def delete_employee(emp_id):
    conn = connect_db()
    if not conn: return "Database connection failed."
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT uid FROM employee WHERE id = %s", (emp_id,))
            result = cursor.fetchone()
            if not result: return "Error: Employee not found."
            user_id = result['uid']
            cursor.execute("DELETE FROM employee WHERE id = %s", (emp_id,))
            if user_id:
                cursor.execute("DELETE FROM user_account WHERE uid = %s", (user_id,))
            conn.commit()
        return "Employee deleted successfully!"
    except Exception as e:
        conn.rollback()
        return f"An error occurred: {e}"
    finally:
        if conn: conn.close()

# --- Inventory & Supplier Management Functions ---

def get_all_ingredient_types():
    conn = connect_db()
    if not conn: return []
    try:
        with conn.cursor() as cursor:
            sql = "SELECT ingredient_id, ingredient_name, unit, total_stock, reorder_level FROM current_inventory_view"
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        if conn: conn.close()

def add_ingredient_type(details):
    conn = connect_db()
    if not conn: return "Database connection failed."
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO ingredients (name, unit, reorder_level) VALUES (%s, %s, %s)"
            cursor.execute(sql, (details['name'], details['unit'], details['reorder_level']))
            conn.commit()
        return "Ingredient type added successfully!"
    except pymysql.IntegrityError:
        conn.rollback()
        return "Error: An ingredient with this name already exists."
    except Exception as e:
        conn.rollback()
        return f"An unexpected error occurred: {e}"
    finally:
        if conn: conn.close()

def get_all_suppliers():
    conn = connect_db()
    if not conn: return []
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, email, phone FROM supplier")
            return cursor.fetchall()
    finally:
        if conn: conn.close()

def get_batches_for_ingredient(ingredient_id):
    conn = connect_db()
    if not conn: return []
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT ib.id, s.name as supplier_name, ib.quantity_received, ib.quantity_remaining, 
                   ib.cost_per_unit, ib.received_date, ib.expiry_date 
            FROM ingredient_batches ib
            LEFT JOIN supplier s ON ib.supplier_id = s.id
            WHERE ib.ingredient_id = %s ORDER BY ib.expiry_date ASC
            """
            cursor.execute(sql, (ingredient_id,))
            return cursor.fetchall()
    finally:
        if conn: conn.close()

def add_ingredient_batch(details):
    conn = connect_db()
    if not conn: return "Database connection failed."
    try:
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO ingredient_batches 
            (ingredient_id, supplier_id, quantity_received, quantity_remaining, cost_per_unit, received_date, expiry_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                details['ingredient_id'], details['supplier_id'], details['quantity'],
                details['quantity'], details['cost_per_unit'], date.today(), details['expiry_date']
            ))
            conn.commit()
        return "Delivery recorded successfully!"
    except Exception as e:
        conn.rollback()
        return f"An unexpected error occurred: {e}"
    finally:
        if conn: conn.close()

def add_supplier(details):
    conn = connect_db()
    if not conn: return "Database connection failed."
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO supplier (name, email, phone) VALUES (%s, %s, %s)"
            cursor.execute(sql, (details['name'], details['email'], details['phone']))
            conn.commit()
        return "Supplier added successfully!"
    except pymysql.IntegrityError:
        conn.rollback()
        return "Error: A supplier with this name or email may already exist."
    finally:
        if conn: conn.close()

def update_supplier(supplier_id, details):
    conn = connect_db()
    if not conn: return "Database connection failed."
    try:
        with conn.cursor() as cursor:
            sql = "UPDATE supplier SET name = %s, email = %s, phone = %s WHERE id = %s"
            cursor.execute(sql, (details['name'], details['email'], details['phone'], supplier_id))
            conn.commit()
        return "Supplier updated successfully!"
    except pymysql.IntegrityError:
        conn.rollback()
        return "Error: The email may already be in use by another supplier."
    finally:
        if conn: conn.close()

def delete_supplier(supplier_id):
    conn = connect_db()
    if not conn: return "Database connection failed."
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM supplier WHERE id = %s", (supplier_id,))
            conn.commit()
        return "Supplier deleted successfully!"
    except Exception as e:
        conn.rollback()
        return f"An error occurred: {e}"
    finally:
        if conn: conn.close()

# --- Dish & Recipe Management Functions ---

def get_all_dishes():
    conn = connect_db()
    if not conn: return []
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, dname, price, category FROM dish ORDER BY dname")
            return cursor.fetchall()
    finally:
        if conn: conn.close()

def add_dish(details):
    conn = connect_db()
    if not conn: return "Database connection failed."
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO dish (dname, price, category) VALUES (%s, %s, %s)"
            cursor.execute(sql, (details['dname'], details['price'], details['category']))
            conn.commit()
        return "Dish added successfully!"
    except pymysql.IntegrityError:
        conn.rollback()
        return "Error: A dish with this name already exists."
    finally:
        if conn: conn.close()

def update_dish(dish_id, details):
    conn = connect_db()
    if not conn: return "Database connection failed."
    try:
        with conn.cursor() as cursor:
            sql = "UPDATE dish SET dname = %s, price = %s, category = %s WHERE id = %s"
            cursor.execute(sql, (details['dname'], details['price'], details['category'], dish_id))
            conn.commit()
        return "Dish updated successfully!"
    except pymysql.IntegrityError:
        conn.rollback()
        return "Error: A dish with this name may already exist."
    finally:
        if conn: conn.close()

def delete_dish(dish_id):
    conn = connect_db()
    if not conn: return "Database connection failed."
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM dish WHERE id = %s", (dish_id,))
            conn.commit()
        return "Dish deleted successfully!"
    except Exception as e:
        conn.rollback()
        return f"An error occurred: {e}"
    finally:
        if conn: conn.close()

def get_recipe_for_dish(dish_id):
    conn = connect_db()
    if not conn: return []
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT r.id, i.id as ingredient_id, i.name, r.quantity_needed, i.unit 
            FROM recipe r
            JOIN ingredients i ON r.ingredient_id = i.id
            WHERE r.dish_id = %s
            """
            cursor.execute(sql, (dish_id,))
            return cursor.fetchall()
    finally:
        if conn: conn.close()

def add_ingredient_to_recipe(details):
    conn = connect_db()
    if not conn: return "Database connection failed."
    try:
        with conn.cursor() as cursor:
            sql_check = "SELECT id FROM recipe WHERE dish_id = %s AND ingredient_id = %s"
            cursor.execute(sql_check, (details['dish_id'], details['ingredient_id']))
            if cursor.fetchone():
                return "Error: This ingredient is already in the recipe. Update it instead."
            sql = "INSERT INTO recipe (dish_id, ingredient_id, quantity_needed) VALUES (%s, %s, %s)"
            cursor.execute(sql, (details['dish_id'], details['ingredient_id'], details['quantity']))
            conn.commit()
        return "Ingredient added to recipe successfully!"
    except Exception as e:
        conn.rollback()
        return f"An unexpected error occurred: {e}"
    finally:
        if conn: conn.close()

def update_recipe_ingredient(recipe_id, quantity):
    conn = connect_db()
    if not conn: return "Database connection failed."
    try:
        with conn.cursor() as cursor:
            sql = "UPDATE recipe SET quantity_needed = %s WHERE id = %s"
            cursor.execute(sql, (quantity, recipe_id))
            conn.commit()
        return "Recipe ingredient updated successfully!"
    except Exception as e:
        conn.rollback()
        return f"An unexpected error occurred: {e}"
    finally:
        if conn: conn.close()

def remove_ingredient_from_recipe(recipe_id):
    conn = connect_db()
    if not conn: return "Database connection failed."
    try:
        with conn.cursor() as cursor:
            sql = "DELETE FROM recipe WHERE id = %s"
            cursor.execute(sql, (recipe_id,))
            conn.commit()
        return "Ingredient removed from recipe successfully!"
    except Exception as e:
        conn.rollback()
        return f"An unexpected error occurred: {e}"
    finally:
        if conn: conn.close()

def get_all_ingredient_names():
    conn = connect_db()
    if not conn: return []
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM ingredients ORDER BY name")
            return cursor.fetchall()
    finally:
        if conn: conn.close()

# --- Point-of-Sale Functions ---

def process_sale(waiter_id, order_items, total_amount):
    conn = connect_db()
    if not conn:
        return "Database connection failed."
    try:
        with conn.cursor() as cursor:
            ingredients_needed = {}
            for dish_id, quantity, price in order_items:
                recipe = get_recipe_for_dish(dish_id)
                if not recipe:
                    return f"Error: No recipe found for dish ID {dish_id}. Cannot process sale."
                for item in recipe:
                    ing_id = item['ingredient_id']
                    needed = float(item['quantity_needed']) * int(quantity)
                    ingredients_needed[ing_id] = ingredients_needed.get(ing_id, 0) + needed

            for ing_id, total_needed in ingredients_needed.items():
                cursor.execute("SELECT total_stock, ingredient_name FROM current_inventory_view WHERE ingredient_id = %s", (ing_id,))
                result = cursor.fetchone()
                if not result or result['total_stock'] < total_needed:
                    name = result['ingredient_name'] if result else f"ID {ing_id}"
                    stock = result['total_stock'] if result else 0
                    raise ValueError(f"Insufficient stock for {name}. Required: {total_needed}, Available: {stock}")

            sql_sale = "INSERT INTO sales (waiter_id, total_amount) VALUES (%s, %s)"
            cursor.execute(sql_sale, (waiter_id, total_amount))
            sale_id = cursor.lastrowid

            for dish_id, quantity, price in order_items:
                sql_sale_item = "INSERT INTO sale_items (sale_id, dish_id, quantity, price_per_item) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql_sale_item, (sale_id, dish_id, quantity, price))
                recipe = get_recipe_for_dish(dish_id)
                for item in recipe:
                    ing_id = item['ingredient_id']
                    qty_to_deduct = float(item['quantity_needed']) * int(quantity)
                    sql_batches = "SELECT id, quantity_remaining FROM ingredient_batches WHERE ingredient_id = %s AND quantity_remaining > 0 ORDER BY expiry_date ASC"
                    cursor.execute(sql_batches, (ing_id,))
                    batches = cursor.fetchall()
                    for batch in batches:
                        if qty_to_deduct <= 0:
                            break
                        deduct_from_this_batch = min(qty_to_deduct, batch['quantity_remaining'])
                        new_qty = float(batch['quantity_remaining']) - deduct_from_this_batch
                        sql_update_batch = "UPDATE ingredient_batches SET quantity_remaining = %s WHERE id = %s"
                        cursor.execute(sql_update_batch, (new_qty, batch['id']))
                        qty_to_deduct -= deduct_from_this_batch
            conn.commit()
            return f"Sale #{sale_id} processed successfully!"
    except (pymysql.Error, ValueError) as e:
        conn.rollback()
        return f"Error processing sale: {e}"
    finally:
        if conn:
            conn.close()

# --- Dashboard Data Functions ---

def get_dashboard_kpis():
    """Fetches Key Performance Indicators for the dashboard"""
    conn = connect_db()
    if not conn: return {}
    try:
        with conn.cursor() as cursor:
            # Total Revenue
            cursor.execute("SELECT SUM(total_amount) AS total_revenue FROM sales")
            total_revenue = cursor.fetchone()['total_revenue'] or 0
            
            # Total Dishes Sold
            cursor.execute("SELECT SUM(quantity) AS total_dishes_sold FROM sale_items")
            total_dishes_sold = cursor.fetchone()['total_dishes_sold'] or 0
            
            # Number of Sales
            cursor.execute("SELECT COUNT(id) AS num_sales FROM sales")
            num_sales = cursor.fetchone()['num_sales'] or 0
            
            return {
                "total_revenue": total_revenue,
                "total_dishes_sold": total_dishes_sold,
                "num_sales": num_sales
            }
    finally:
        if conn: conn.close()

def get_sales_by_day(days=7):
    """Fetches total sales revenue for the last N days"""
    conn = connect_db()
    if not conn: return []
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT DATE(sale_time) AS sale_date, SUM(total_amount) AS daily_sales
            FROM sales
            WHERE sale_time >= CURDATE() - INTERVAL %s DAY
            GROUP BY DATE(sale_time)
            ORDER BY sale_date ASC
            """
            cursor.execute(sql, (days,))
            return cursor.fetchall()
    finally:
        if conn: conn.close()
        
def get_top_selling_dishes(limit=5):
    """Fetches the most frequently sold dishes"""
    conn = connect_db()
    if not conn: return []
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT d.dname, SUM(si.quantity) AS total_sold
            FROM sale_items si
            JOIN dish d ON si.dish_id = d.id
            GROUP BY d.dname
            ORDER BY total_sold DESC
            LIMIT %s
            """
            cursor.execute(sql, (limit,))
            return cursor.fetchall()
    finally:
        if conn: conn.close()

def get_low_stock_alerts():
    """Fetches ingredients where stock is at or below the reorder level"""
    conn = connect_db()
    if not conn: return []
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT ingredient_name, total_stock, reorder_level, unit
            FROM current_inventory_view
            WHERE total_stock <= reorder_level
            """
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        if conn: conn.close()
