import tkinter
import customtkinter as ctk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pymysql
import pymysql.cursors
import hashlib
import re

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import DateFormatter
from PIL import Image, ImageTk

from utils import (
    get_all_employees, add_employee, update_employee, delete_employee,
    get_all_ingredient_types, add_ingredient_type, get_all_suppliers,
    get_batches_for_ingredient, add_ingredient_batch, add_supplier,
    update_supplier, delete_supplier, get_all_dishes, add_dish,
    update_dish, delete_dish, get_recipe_for_dish, get_all_ingredient_names,
    add_ingredient_to_recipe, update_recipe_ingredient, remove_ingredient_from_recipe,
    process_sale,
    get_dashboard_kpis, get_sales_by_day, get_top_selling_dishes, get_low_stock_alerts
)

# --- Database Connection & Login Verification ---
def connect_db():
    try:
        return pymysql.connect(host='localhost', user='root', password='java0603', database='restaurant-inventory-db', cursorclass=pymysql.cursors.DictCursor, autocommit=False)
    except pymysql.Error as e:
        messagebox.showerror("Database Error", f"Could not connect: {e}")
        return None

def verify_login(username, password):
    try:
        conn = pymysql.connect(host='localhost', user='root', password='java0603', database='restaurant-inventory-db', cursorclass=pymysql.cursors.DictCursor, autocommit=True)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        with conn.cursor() as cursor:
            sql = "SELECT u.uid, e.id as employee_id, u.username, e.role, e.fname FROM user_account u JOIN employee e ON u.uid = e.uid WHERE u.username = %s AND u.password_hash = %s"
            cursor.execute(sql, (username, password_hash))
            return cursor.fetchone()
    except pymysql.Error:
        return None
    finally:
        if 'conn' in locals() and conn: conn.close()

# --- App and Frame Classes ---
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Restaurant BI Dashboard")
        self.geometry("500x450")
        self.minsize(500, 450)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        self.user_info = None
        
        self.container = ctk.CTkFrame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.login_frame = LoginFrame(parent=self.container, controller=self)
        self.frames[LoginFrame] = self.login_frame
        self.login_frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(LoginFrame)

    def show_frame(self, page_name):
        frame = self.frames.get(page_name)
        if frame:
            frame.tkraise()

    def successful_login(self, user_data):
        self.user_info = user_data
        
        self.main_app_frame = MainApplicationFrame(parent=self.container, controller=self)
        self.frames[MainApplicationFrame] = self.main_app_frame
        self.main_app_frame.grid(row=0, column=0, sticky="nsew")
        
        self.login_frame.destroy()
        
        self.geometry("1300x800")
        self.minsize(1200, 700)
        
        self.show_frame(MainApplicationFrame)

    def logout(self):
        if hasattr(self, 'main_app_frame'):
            self.main_app_frame.destroy()
            del self.frames[MainApplicationFrame]

        self.user_info = None
        self.login_frame = LoginFrame(parent=self.container, controller=self)
        self.frames[LoginFrame] = self.login_frame
        self.login_frame.grid(row=0, column=0, sticky="nsew")
        self.geometry("500x450")
        self.minsize(500, 450)
        self.show_frame(LoginFrame)

class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.label = ctk.CTkLabel(self, text="Restaurant Management System", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.pack(pady=40)
        self.username_entry = ctk.CTkEntry(self, width=250, placeholder_text="Username")
        self.username_entry.pack(pady=12, padx=10)
        self.password_entry = ctk.CTkEntry(self, width=250, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=12, padx=10)
        self.login_button = ctk.CTkButton(self, text="Login", command=self.login_event)
        self.login_button.pack(pady=20, padx=10)
        self.controller.bind('<Return>', lambda event=None: self.login_button.invoke())

    def login_event(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showwarning("Login Error", "Username and password are required.")
            return
        user_data = verify_login(username, password)
        if user_data:
            messagebox.showinfo("Login Successful", f"Welcome, {user_data['fname']}!")
            self.controller.successful_login(user_data)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

class MainApplicationFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        plt.style.use('dark_background')
        
        logout_button = ctk.CTkButton(self, text="Logout", width=100, command=self.controller.logout, fg_color="#D32F2F", hover_color="#B71C1C")
        logout_button.place(relx=0.99, y=10, anchor='ne')

        self.notebook = ctk.CTkTabview(self, width=1250, height=750)
        self.notebook.pack(pady=(40, 10), padx=10, fill="both", expand=True)
        
        self.create_tabs_based_on_role()


    def is_valid_email(self, email):
        """regex for validating an email address"""
        if re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            return True
        return False

    def create_tabs_based_on_role(self):
        user_role = self.controller.user_info.get('role')
        
        if user_role in ['admin', 'manager']:
            dashboard_tab = self.notebook.add("Dashboard")
            self.populate_dashboard_tab(dashboard_tab)
        if user_role in ['admin', 'manager', 'waiter']:
            pos_tab = self.notebook.add("New Sale")
            self.populate_pos_tab(pos_tab)
        if user_role in ['admin', 'manager', 'chef']:
            menu_tab = self.notebook.add("Menu & Recipes")
            self.populate_menu_tab(menu_tab)
        if user_role in ['admin', 'manager', 'chef']:
            inventory_tab = self.notebook.add("Inventory")
            self.populate_inventory_tab(inventory_tab)
        if user_role == 'admin':
            suppliers_tab = self.notebook.add("Suppliers")
            employees_tab = self.notebook.add("Employees")
            self.populate_suppliers_tab(suppliers_tab)
            self.populate_employees_tab(employees_tab)
            
        if user_role == 'waiter': self.notebook.set("New Sale")
        elif user_role == 'chef': self.notebook.set("Menu & Recipes")
        else: self.notebook.set("Dashboard")

    def populate_dashboard_tab(self, tab):
        self.dashboard_widgets = {}
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        header_frame = ctk.CTkFrame(tab)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header_frame, text="Business Intelligence Dashboard", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Refresh Data", command=self.refresh_dashboard_data).grid(row=0, column=1, padx=10, pady=10)
        content_frame = ctk.CTkFrame(tab, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=0)
        content_frame.grid_columnconfigure((0, 1), weight=1)
        content_frame.grid_rowconfigure((1, 2), weight=1)
        kpi_frame = ctk.CTkFrame(content_frame)
        kpi_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        kpi_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.create_kpi_widgets(kpi_frame)
        self.dashboard_widgets['sales_chart_frame'] = ctk.CTkFrame(content_frame)
        self.dashboard_widgets['sales_chart_frame'].grid(row=1, column=0, sticky="nsew", padx=(0, 5), pady=5)
        self.dashboard_widgets['top_dishes_chart_frame'] = ctk.CTkFrame(content_frame)
        self.dashboard_widgets['top_dishes_chart_frame'].grid(row=1, column=1, sticky="nsew", padx=(5, 0), pady=5)
        alerts_frame = ctk.CTkFrame(content_frame)
        alerts_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(5, 0))
        alerts_frame.grid_rowconfigure(1, weight=1)
        alerts_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(alerts_frame, text="Low Stock Alerts", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, pady=5)
        alert_columns = ("Ingredient", "Stock", "Reorder Level", "Unit")
        self.dashboard_widgets['alerts_tree'] = ttk.Treeview(alerts_frame, columns=alert_columns, show="headings")
        self.dashboard_widgets['alerts_tree'].grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        for col in alert_columns:
            self.dashboard_widgets['alerts_tree'].heading(col, text=col, anchor='center')
            self.dashboard_widgets['alerts_tree'].column(col, anchor='center')
        self.refresh_dashboard_data()

    def create_kpi_widgets(self, parent_frame):
        kpi_data = [
            {"label": "Total Revenue", "key": "total_revenue", "format": "₹{:.2f}"},
            {"label": "Total Dishes Sold", "key": "total_dishes_sold", "format": "{}"},
            {"label": "Total Transactions", "key": "num_sales", "format": "{}"}
        ]
        for i, data in enumerate(kpi_data):
            frame = ctk.CTkFrame(parent_frame)
            frame.grid(row=0, column=i, sticky="ew", padx=5, pady=5)
            frame.grid_columnconfigure(0, weight=1)
            label = ctk.CTkLabel(frame, text=data['label'], font=ctk.CTkFont(size=14))
            label.grid(row=0, column=0, pady=(5,0))
            value_label = ctk.CTkLabel(frame, text="...", font=ctk.CTkFont(size=24, weight="bold"))
            value_label.grid(row=1, column=0, pady=(0,5))
            self.dashboard_widgets[data['key']] = value_label

    def refresh_dashboard_data(self):
        kpis = get_dashboard_kpis()
        if kpis:
            self.dashboard_widgets['total_revenue'].configure(text=f"₹{kpis.get('total_revenue', 0):.2f}")
            self.dashboard_widgets['total_dishes_sold'].configure(text=f"{int(kpis.get('total_dishes_sold', 0))}")
            self.dashboard_widgets['num_sales'].configure(text=f"{kpis.get('num_sales', 0)}")
        sales_data = get_sales_by_day(days=7)
        self.create_chart(self.dashboard_widgets['sales_chart_frame'], sales_data, 'Sales Over Last 7 Days', 'sale_date', 'daily_sales', 'Date', 'Revenue (₹)', kind='line')
        top_dishes_data = get_top_selling_dishes(limit=5)
        self.create_chart(self.dashboard_widgets['top_dishes_chart_frame'], top_dishes_data, 'Top 5 Selling Dishes', 'dname', 'total_sold', 'Dish', 'Quantity Sold', kind='bar')
        alerts = get_low_stock_alerts()
        for item in self.dashboard_widgets['alerts_tree'].get_children(): self.dashboard_widgets['alerts_tree'].delete(item)
        for alert in alerts:
            self.dashboard_widgets['alerts_tree'].insert("", "end", values=(alert['ingredient_name'], alert['total_stock'], alert['reorder_level'], alert['unit']))

    def create_chart(self, parent_frame, data, title, x_col, y_col, xlabel, ylabel, kind='bar'):
        for widget in parent_frame.winfo_children():
            widget.destroy()
        if not data:
            ctk.CTkLabel(parent_frame, text=f"{title}\n(No data available)").pack(expand=True, padx=10, pady=10)
            return
        df = pd.DataFrame(data)
        df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
        df.dropna(subset=[y_col], inplace=True)
        if df.empty:
            ctk.CTkLabel(parent_frame, text=f"{title}\n(No data available)").pack(expand=True, padx=10, pady=10)
            return
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor('#2B2B2B')
        ax.set_facecolor('#242424')
        bar_color = '#3498db'
        if kind == 'bar':
            bars = ax.bar(df[x_col], df[y_col], color=bar_color)
            ax.bar_label(bars, fmt='%.0f', color='white', fontsize=10)
            plt.xticks(rotation=15, ha='right', fontsize=9)
        else:
            df[x_col] = pd.to_datetime(df[x_col])
            ax.plot(df[x_col], df[y_col], marker='o', linestyle='-', color=bar_color, markersize=8, markerfacecolor='#85c1e9')
            ax.xaxis.set_major_formatter(DateFormatter('%b %d'))
            plt.xticks(rotation=15, ha='right', fontsize=9)
        ax.set_title(title, color='white', fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel(xlabel, color='white', fontsize=10, labelpad=10)
        ax.set_ylabel(ylabel, color='white', fontsize=10, labelpad=10)
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('grey')
        ax.spines['bottom'].set_color('grey')
        ax.grid(axis='y', linestyle='--', alpha=0.2)
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True, padx=10, pady=10)
        plt.close(fig)

    def populate_pos_tab(self, tab):
        self.current_order = {}
        tab.grid_columnconfigure(0, weight=2); tab.grid_columnconfigure(1, weight=1); tab.grid_rowconfigure(0, weight=1)
        menu_frame = ctk.CTkFrame(tab); menu_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(menu_frame, text="Menu", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        self.menu_items_frame = ctk.CTkScrollableFrame(menu_frame, label_text="Dishes"); self.menu_items_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.load_menu_for_pos()
        order_frame = ctk.CTkFrame(tab); order_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew"); order_frame.grid_rowconfigure(1, weight=1); order_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(order_frame, text="Current Order", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, pady=10)
        order_columns = ("Qty", "Dish", "Price", "Subtotal"); self.order_tree = ttk.Treeview(order_frame, columns=order_columns, show="headings"); self.order_tree.grid(row=1, column=0, sticky="nsew", padx=10)
        for col in order_columns:
            self.order_tree.heading(col, text=col, anchor='center')
            if col == "Dish": self.order_tree.column(col, anchor='w', width=150)
            else: self.order_tree.column(col, anchor='center', width=80)
        total_frame = ctk.CTkFrame(order_frame); total_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10); total_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(total_frame, text="TOTAL:", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=5)
        self.total_label = ctk.CTkLabel(total_frame, text="₹0.00", font=ctk.CTkFont(size=16, weight="bold")); self.total_label.grid(row=0, column=1, sticky="e", padx=5)
        order_button_frame = ctk.CTkFrame(order_frame); order_button_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10)); order_button_frame.grid_columnconfigure((0,1), weight=1)
        ctk.CTkButton(order_button_frame, text="Remove Selected", command=self.remove_from_order_event, fg_color="#D32F2F", hover_color="#B71C1C").grid(row=0, column=0, padx=5, sticky="ew")
        ctk.CTkButton(order_button_frame, text="Clear Order", command=self.clear_order_event).grid(row=0, column=1, padx=5, sticky="ew")
        ctk.CTkButton(order_frame, text="COMPLETE SALE", font=ctk.CTkFont(size=16, weight="bold"), command=self.complete_sale_event).grid(row=4, column=0, sticky="ew", padx=10, pady=10, ipady=10)
    
    def load_menu_for_pos(self):
        for widget in self.menu_items_frame.winfo_children(): widget.destroy()
        dishes = get_all_dishes()
        for dish in dishes:
            dish_id = dish['id']; dname = dish['dname']; price = dish['price']
            btn_text = f"{dname}\n₹{price:.2f}"
            button = ctk.CTkButton(self.menu_items_frame, text=btn_text, command=lambda d_id=dish_id, d_name=dname, d_price=price: self.add_to_order_event(d_id, d_name, d_price))
            button.pack(fill="x", padx=10, pady=5)
    
    def add_to_order_event(self, dish_id, name, price):
        if dish_id in self.current_order: self.current_order[dish_id]['quantity'] += 1
        else: self.current_order[dish_id] = {'name': name, 'price': float(price), 'quantity': 1}
        self.refresh_order_tree()
    
    def remove_from_order_event(self):
        selected_item = self.order_tree.focus()
        if not selected_item: messagebox.showwarning("Selection Error", "Please select an item from the order to remove."); return
        item_values = self.order_tree.item(selected_item)['values']; dish_name_to_remove = item_values[1]
        dish_id_to_remove = None
        for dish_id, details in self.current_order.items():
            if details['name'] == dish_name_to_remove: dish_id_to_remove = dish_id; break
        if dish_id_to_remove:
            if self.current_order[dish_id_to_remove]['quantity'] > 1: self.current_order[dish_id_to_remove]['quantity'] -= 1
            else: del self.current_order[dish_id_to_remove]
        self.refresh_order_tree()
    
    def clear_order_event(self):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the entire order?"):
            self.current_order = {}; self.refresh_order_tree()
    
    def refresh_order_tree(self):
        for item in self.order_tree.get_children(): self.order_tree.delete(item)
        total = 0.0
        for dish_id, details in self.current_order.items():
            qty = details['quantity']; name = details['name']; price = details['price']; subtotal = qty * price; total += subtotal
            self.order_tree.insert("", "end", values=(qty, name, f"{price:.2f}", f"{subtotal:.2f}"))
        self.total_label.configure(text=f"₹{total:.2f}")
    
    def complete_sale_event(self):
        if not self.current_order: messagebox.showwarning("Empty Order", "Cannot process an empty order."); return
        waiter_id = self.controller.user_info['employee_id']
        total_amount = sum(d['price'] * d['quantity'] for d in self.current_order.values())
        order_items = [(dish_id, details['quantity'], details['price']) for dish_id, details in self.current_order.items()]
        if not messagebox.askyesno("Confirm Sale", f"Complete sale for a total of ₹{total_amount:.2f}?"): return
        response = process_sale(waiter_id, order_items, total_amount)
        messagebox.showinfo("Sale Processing", response)
        if "successfully" in response:
            self.current_order = {}; self.refresh_order_tree()
            if hasattr(self, 'ingredient_types_tree'): self.refresh_ingredient_types_table()
            if hasattr(self, 'dashboard_widgets'): self.refresh_dashboard_data()
    
    def populate_menu_tab(self, tab):
        self.selected_dish_id = None; self.selected_recipe_item_id = None; self.ingredients_map = {}
        tab.grid_columnconfigure(0, weight=2); tab.grid_columnconfigure(1, weight=3); tab.grid_rowconfigure(0, weight=1)
        dish_frame = ctk.CTkFrame(tab); dish_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew"); dish_frame.grid_rowconfigure(1, weight=1); dish_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(dish_frame, text="Menu Dishes", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, pady=10)
        dish_columns = ("ID", "Dish Name", "Price", "Category"); self.dish_tree = ttk.Treeview(dish_frame, columns=dish_columns, show="headings"); self.dish_tree.grid(row=1, column=0, sticky="nsew")
        for col in dish_columns: self.dish_tree.heading(col, text=col, anchor='center'); self.dish_tree.column(col, anchor='center', width=80)
        self.dish_tree.bind("<<TreeviewSelect>>", self.on_dish_select)
        dish_form_frame = ctk.CTkFrame(dish_frame); dish_form_frame.grid(row=2, column=0, pady=10, sticky="ew"); dish_form_frame.grid_columnconfigure((0, 1), weight=1)
        self.dish_name_entry = ctk.CTkEntry(dish_form_frame, placeholder_text="Dish Name"); self.dish_name_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.dish_price_entry = ctk.CTkEntry(dish_form_frame, placeholder_text="Price (e.g., 12.99)"); self.dish_price_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.dish_category_entry = ctk.CTkEntry(dish_form_frame, placeholder_text="Category (e.g., Appetizer)"); self.dish_category_entry.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        dish_button_frame = ctk.CTkFrame(dish_form_frame); dish_button_frame.grid(row=2, column=0, columnspan=2, pady=5, sticky="ew"); dish_button_frame.grid_columnconfigure((0,1,2,3), weight=1)
        ctk.CTkButton(dish_button_frame, text="Add Dish", command=self.add_dish_event).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(dish_button_frame, text="Update Selected", command=self.update_dish_event).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(dish_button_frame, text="Delete Selected", command=self.delete_dish_event, fg_color="#D32F2F", hover_color="#B71C1C").grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(dish_button_frame, text="Clear Form", command=self.clear_dish_form).grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        recipe_frame = ctk.CTkFrame(tab); recipe_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew"); recipe_frame.grid_rowconfigure(1, weight=1); recipe_frame.grid_columnconfigure(0, weight=1)
        self.recipe_label = ctk.CTkLabel(recipe_frame, text="Select a Dish to View Recipe", font=ctk.CTkFont(size=18, weight="bold")); self.recipe_label.grid(row=0, column=0, pady=10)
        recipe_columns = ("ID", "Ingredient", "Quantity Needed", "Unit"); self.recipe_tree = ttk.Treeview(recipe_frame, columns=recipe_columns, show="headings"); self.recipe_tree.grid(row=1, column=0, sticky="nsew")
        for col in recipe_columns: self.recipe_tree.heading(col, text=col, anchor='center'); self.recipe_tree.column(col, anchor='center', width=100)
        self.recipe_tree.bind("<<TreeviewSelect>>", self.on_recipe_item_select)
        recipe_form_frame = ctk.CTkFrame(recipe_frame); recipe_form_frame.grid(row=2, column=0, pady=10, sticky="ew"); recipe_form_frame.grid_columnconfigure(0, weight=2); recipe_form_frame.grid_columnconfigure(1, weight=1)
        self.recipe_ingredient_menu_var = ctk.StringVar(value="Select Ingredient"); self.recipe_ingredient_menu = ctk.CTkOptionMenu(recipe_form_frame, variable=self.recipe_ingredient_menu_var); self.recipe_ingredient_menu.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.recipe_qty_entry = ctk.CTkEntry(recipe_form_frame, placeholder_text="Quantity"); self.recipe_qty_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        recipe_button_frame = ctk.CTkFrame(recipe_form_frame); recipe_button_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew"); recipe_button_frame.grid_columnconfigure((0,1,2), weight=1)
        ctk.CTkButton(recipe_button_frame, text="Add Ingredient", command=self.add_recipe_item_event).grid(row=0, column=0, padx=5, sticky="ew")
        ctk.CTkButton(recipe_button_frame, text="Update Selected", command=self.update_recipe_item_event).grid(row=0, column=1, padx=5, sticky="ew")
        ctk.CTkButton(recipe_button_frame, text="Remove Selected", command=self.remove_recipe_item_event, fg_color="#D32F2F", hover_color="#B71C1C").grid(row=0, column=2, padx=5, sticky="ew")
        self.refresh_dish_table(); self.load_all_ingredients_for_menu()
    
    def refresh_dish_table(self):
        for item in self.dish_tree.get_children(): self.dish_tree.delete(item)
        dishes = get_all_dishes()
        for dish in dishes: self.dish_tree.insert("", "end", values=(dish['id'], dish['dname'], f"{dish['price']:.2f}", dish['category']))
    
    def load_all_ingredients_for_menu(self):
        ingredients = get_all_ingredient_names()
        if not ingredients: self.recipe_ingredient_menu.configure(values=["No ingredients found"]); return
        ingredient_names = [ing['name'] for ing in ingredients]; self.ingredients_map = {ing['name']: ing['id'] for ing in ingredients}; self.recipe_ingredient_menu.configure(values=ingredient_names); self.recipe_ingredient_menu_var.set(ingredient_names[0])
    
    def on_dish_select(self, event):
        if not self.dish_tree.selection(): return
        selected_item = self.dish_tree.focus(); dish_data = self.dish_tree.item(selected_item)['values']
        self.clear_dish_form_fields(); self.selected_dish_id = dish_data[0]; self.dish_name_entry.insert(0, dish_data[1]); self.dish_price_entry.insert(0, dish_data[2]); self.dish_category_entry.insert(0, dish_data[3])
        self.recipe_label.configure(text=f"Recipe for: {dish_data[1]}"); self.refresh_recipe_view(); self.clear_recipe_form()
    
    def on_recipe_item_select(self, event):
        if not self.recipe_tree.selection(): return
        selected_item = self.recipe_tree.focus(); recipe_item_data = self.recipe_tree.item(selected_item)['values']
        self.selected_recipe_item_id = recipe_item_data[0]; ingredient_name = recipe_item_data[1]; quantity = recipe_item_data[2]
        self.recipe_ingredient_menu_var.set(ingredient_name); self.recipe_qty_entry.delete(0, 'end'); self.recipe_qty_entry.insert(0, quantity)
        self.recipe_ingredient_menu.configure(state="disabled")
    
    def refresh_recipe_view(self):
        for item in self.recipe_tree.get_children(): self.recipe_tree.delete(item)
        if self.selected_dish_id is None: return
        recipe_items = get_recipe_for_dish(self.selected_dish_id)
        for item in recipe_items: self.recipe_tree.insert("", "end", values=(item['id'], item['name'], item['quantity_needed'], item['unit']))
        self.clear_recipe_form()
    
    def clear_dish_form_fields(self):
        self.dish_name_entry.delete(0, 'end'); self.dish_price_entry.delete(0, 'end'); self.dish_category_entry.delete(0, 'end')
    
    def clear_dish_form(self):
        self.selected_dish_id = None; self.clear_dish_form_fields()
        if self.dish_tree.selection(): self.dish_tree.selection_remove(self.dish_tree.selection())
        self.recipe_label.configure(text="Select a Dish to View Recipe")
        for item in self.recipe_tree.get_children(): self.recipe_tree.delete(item)
        self.clear_recipe_form()
    
    def clear_recipe_form(self):
        self.selected_recipe_item_id = None; self.recipe_qty_entry.delete(0, 'end')
        if self.ingredients_map: self.recipe_ingredient_menu_var.set(list(self.ingredients_map.keys())[0])
        self.recipe_ingredient_menu.configure(state="normal")
        if self.recipe_tree.selection(): self.recipe_tree.selection_remove(self.recipe_tree.selection())
    
    def add_dish_event(self):
        details = {'dname': self.dish_name_entry.get(), 'price': self.dish_price_entry.get(), 'category': self.dish_category_entry.get()}
        if not details['dname'] or not details['price']: messagebox.showwarning("Input Error", "Dish Name and Price are required."); return
        response = add_dish(details); messagebox.showinfo("Response", response)
        if "successfully" in response:
            self.refresh_dish_table(); self.clear_dish_form()
            if hasattr(self, 'menu_items_frame'): self.load_menu_for_pos()
    
    def update_dish_event(self):
        if self.selected_dish_id is None: messagebox.showwarning("Selection Error", "Please select a dish to update."); return
        details = {'dname': self.dish_name_entry.get(), 'price': self.dish_price_entry.get(), 'category': self.dish_category_entry.get()}
        if not details['dname'] or not details['price']: messagebox.showwarning("Input Error", "Dish Name and Price are required."); return
        response = update_dish(self.selected_dish_id, details); messagebox.showinfo("Response", response)
        if "successfully" in response:
            self.refresh_dish_table(); self.clear_dish_form()
            if hasattr(self, 'menu_items_frame'): self.load_menu_for_pos()
    
    def delete_dish_event(self):
        if self.selected_dish_id is None: messagebox.showwarning("Selection Error", "Please select a dish to delete."); return
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this dish?\nThis will also remove its recipe."):
            response = delete_dish(self.selected_dish_id); messagebox.showinfo("Response", response)
            if "successfully" in response:
                self.refresh_dish_table(); self.clear_dish_form()
                if hasattr(self, 'menu_items_frame'): self.load_menu_for_pos()
    
    def add_recipe_item_event(self):
        if self.selected_dish_id is None: messagebox.showwarning("Selection Error", "Please select a dish first."); return
        ingredient_name = self.recipe_ingredient_menu_var.get(); quantity = self.recipe_qty_entry.get()
        if ingredient_name == "Select Ingredient" or not quantity: messagebox.showwarning("Input Error", "Please select an ingredient and specify the quantity."); return
        details = {'dish_id': self.selected_dish_id, 'ingredient_id': self.ingredients_map[ingredient_name], 'quantity': quantity}
        response = add_ingredient_to_recipe(details); messagebox.showinfo("Response", response)
        if "successfully" in response: self.refresh_recipe_view()
    
    def update_recipe_item_event(self):
        if self.selected_recipe_item_id is None: messagebox.showwarning("Selection Error", "Please select an ingredient from the recipe to update."); return
        quantity = self.recipe_qty_entry.get()
        if not quantity: messagebox.showwarning("Input Error", "Quantity cannot be empty."); return
        response = update_recipe_ingredient(self.selected_recipe_item_id, quantity); messagebox.showinfo("Response", response)
        if "successfully" in response: self.refresh_recipe_view()
    
    def remove_recipe_item_event(self):
        if self.selected_recipe_item_id is None: messagebox.showwarning("Selection Error", "Please select an ingredient from the recipe table to remove."); return
        if messagebox.askyesno("Confirm Remove", "Are you sure you want to remove this ingredient from the recipe?"):
            response = remove_ingredient_from_recipe(self.selected_recipe_item_id); messagebox.showinfo("Response", response)
            if "successfully" in response: self.refresh_recipe_view()
    
    def populate_suppliers_tab(self, tab):
        self.selected_supplier_id = None; tab.grid_columnconfigure(0, weight=1); tab.grid_columnconfigure(1, weight=2); tab.grid_rowconfigure(0, weight=1)
        form_frame = ctk.CTkFrame(tab); form_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew"); form_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(form_frame, text="Manage Suppliers", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, columnspan=2, pady=20)
        ctk.CTkLabel(form_frame, text="Supplier Name:").grid(row=1, column=0, padx=10, pady=5, sticky="w"); self.supplier_name_entry = ctk.CTkEntry(form_frame); self.supplier_name_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(form_frame, text="Email:").grid(row=2, column=0, padx=10, pady=5, sticky="w"); self.supplier_email_entry = ctk.CTkEntry(form_frame); self.supplier_email_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(form_frame, text="Phone:").grid(row=3, column=0, padx=10, pady=5, sticky="w"); self.supplier_phone_entry = ctk.CTkEntry(form_frame); self.supplier_phone_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        button_frame = ctk.CTkFrame(form_frame); button_frame.grid(row=4, column=0, columnspan=2, pady=20); button_frame.grid_columnconfigure((0,1,2,3), weight=1)
        ctk.CTkButton(button_frame, text="Add Supplier", command=self.add_supplier_event).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(button_frame, text="Update Selected", command=self.update_supplier_event).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(button_frame, text="Delete Selected", command=self.delete_supplier_event, fg_color="#D32F2F", hover_color="#B71C1C").grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(button_frame, text="Clear Form", command=self.clear_supplier_form).grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        table_frame = ctk.CTkFrame(tab); table_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew"); table_frame.grid_rowconfigure(0, weight=1); table_frame.grid_columnconfigure(0, weight=1)
        style = ttk.Style(); style.theme_use("default"); style.configure("Treeview", background="#2a2d2e", foreground="white", fieldbackground="#2a2d2e", borderwidth=0); style.map('Treeview', background=[('selected', '#2c5d87')]); style.configure("Treeview.Heading", font=('Calibri', 10,'bold'), background="#2c5d87", foreground="white", relief="flat"); style.map("Treeview.Heading", background=[('active', '#3a75a8')])
        supplier_columns = ("ID", "Name", "Email", "Phone"); self.supplier_tree = ttk.Treeview(table_frame, columns=supplier_columns, show="headings"); self.supplier_tree.grid(row=0, column=0, sticky="nsew")
        for col in supplier_columns: self.supplier_tree.heading(col, text=col, anchor='center'); self.supplier_tree.column(col, anchor='center')
        self.supplier_tree.bind("<<TreeviewSelect>>", self.on_supplier_select); self.refresh_supplier_table()
    
    def refresh_supplier_table(self):
        for item in self.supplier_tree.get_children(): self.supplier_tree.delete(item)
        suppliers = get_all_suppliers()
        for sup in suppliers: self.supplier_tree.insert("", "end", values=(sup['id'], sup['name'], sup['email'], sup['phone']))
    
    def clear_supplier_form(self):
        self.selected_supplier_id = None; self.supplier_name_entry.delete(0, 'end'); self.supplier_email_entry.delete(0, 'end'); self.supplier_phone_entry.delete(0, 'end')
        if self.supplier_tree.selection(): self.supplier_tree.selection_remove(self.supplier_tree.selection())
    
    def on_supplier_select(self, event):
        if not self.supplier_tree.selection(): return
        selected_item = self.supplier_tree.focus(); sup_data = self.supplier_tree.item(selected_item)['values']
        self.supplier_name_entry.delete(0, 'end'); self.supplier_email_entry.delete(0, 'end'); self.supplier_phone_entry.delete(0, 'end')
        self.selected_supplier_id = sup_data[0]; self.supplier_name_entry.insert(0, sup_data[1]); self.supplier_email_entry.insert(0, sup_data[2]); self.supplier_phone_entry.insert(0, sup_data[3])
    
    def add_supplier_event(self):
        details = {'name': self.supplier_name_entry.get(), 'email': self.supplier_email_entry.get(), 'phone': self.supplier_phone_entry.get()}
        if not all(details.values()): messagebox.showwarning("Input Error", "All fields are required."); return
        response = add_supplier(details); messagebox.showinfo("Response", response)
        if "successfully" in response: self.refresh_supplier_table(); self.clear_supplier_form(); self.load_suppliers()
    
    def update_supplier_event(self):
        if self.selected_supplier_id is None: messagebox.showwarning("Selection Error", "Please select a supplier to update."); return
        details = {'name': self.supplier_name_entry.get(), 'email': self.supplier_email_entry.get(), 'phone': self.supplier_phone_entry.get()}
        if not all(details.values()): messagebox.showwarning("Input Error", "All fields are required."); return
        response = update_supplier(self.selected_supplier_id, details); messagebox.showinfo("Response", response)
        if "successfully" in response: self.refresh_supplier_table(); self.clear_supplier_form(); self.load_suppliers()
    
    def delete_supplier_event(self):
        if self.selected_supplier_id is None: messagebox.showwarning("Selection Error", "Please select a supplier to delete."); return
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete this supplier?\nThis action cannot be undone."):
            response = delete_supplier(self.selected_supplier_id); messagebox.showinfo("Response", response)
            if "successfully" in response: self.refresh_supplier_table(); self.clear_supplier_form(); self.load_suppliers()
    
    def populate_inventory_tab(self, tab):
        self.selected_ingredient_id = None; self.suppliers_map = {}
        tab.grid_columnconfigure(0, weight=2); tab.grid_columnconfigure(1, weight=3); tab.grid_rowconfigure(0, weight=1)
        types_frame = ctk.CTkFrame(tab); types_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew"); types_frame.grid_rowconfigure(1, weight=1); types_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(types_frame, text="Ingredient Stock", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, pady=10)
        types_columns = ("ID", "Name", "Unit", "Total Stock", "Reorder Level"); self.ingredient_types_tree = ttk.Treeview(types_frame, columns=types_columns, show="headings"); self.ingredient_types_tree.grid(row=1, column=0, sticky="nsew")
        for col in types_columns: self.ingredient_types_tree.heading(col, text=col, anchor='center'); self.ingredient_types_tree.column(col, anchor='center', width=80)
        self.ingredient_types_tree.bind("<<TreeviewSelect>>", self.on_ingredient_type_select); self.refresh_ingredient_types_table()
        add_type_frame = ctk.CTkFrame(types_frame); add_type_frame.grid(row=2, column=0, pady=10, sticky="ew"); add_type_frame.grid_columnconfigure((0,1,2), weight=1)
        self.ing_name_entry = ctk.CTkEntry(add_type_frame, placeholder_text="Ingredient Name"); self.ing_name_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.ing_unit_entry = ctk.CTkEntry(add_type_frame, placeholder_text="Unit (e.g., kg)"); self.ing_unit_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.ing_reorder_entry = ctk.CTkEntry(add_type_frame, placeholder_text="Reorder Level"); self.ing_reorder_entry.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(add_type_frame, text="Add New Type", command=self.add_ingredient_type_event).grid(row=1, column=0, columnspan=3, pady=5, sticky="ew")
        batches_frame = ctk.CTkFrame(tab); batches_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew"); batches_frame.grid_rowconfigure(1, weight=1); batches_frame.grid_columnconfigure(0, weight=1)
        self.batch_label = ctk.CTkLabel(batches_frame, text="Ingredient Batches", font=ctk.CTkFont(size=18, weight="bold")); self.batch_label.grid(row=0, column=0, pady=10)
        batches_columns = ("Batch ID", "Supplier", "Qty Rcvd", "Qty Left", "Cost/Unit", "Received", "Expires"); self.batches_tree = ttk.Treeview(batches_frame, columns=batches_columns, show="headings"); self.batches_tree.grid(row=1, column=0, sticky="nsew")
        for col in batches_columns: self.batches_tree.heading(col, text=col, anchor='center'); self.batches_tree.column(col, anchor='center', width=100)
        add_batch_frame = ctk.CTkFrame(batches_frame); add_batch_frame.grid(row=2, column=0, pady=10, sticky="ew"); add_batch_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(add_batch_frame, text="Record New Delivery:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, pady=(5,10))
        ctk.CTkLabel(add_batch_frame, text="Quantity:").grid(row=1, column=0, padx=5, pady=5, sticky="w"); self.batch_qty_entry = ctk.CTkEntry(add_batch_frame, placeholder_text="e.g., 25"); self.batch_qty_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(add_batch_frame, text="Cost/Unit:").grid(row=2, column=0, padx=5, pady=5, sticky="w"); self.batch_cost_entry = ctk.CTkEntry(add_batch_frame, placeholder_text="e.g., 5.99"); self.batch_cost_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(add_batch_frame, text="Supplier:").grid(row=3, column=0, padx=5, pady=5, sticky="w"); self.supplier_menu_var = ctk.StringVar(value="Select Supplier"); self.supplier_menu = ctk.CTkOptionMenu(add_batch_frame, variable=self.supplier_menu_var); self.supplier_menu.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(add_batch_frame, text="Expiry Date:").grid(row=4, column=0, padx=5, pady=5, sticky="w"); self.expiry_date_entry = DateEntry(add_batch_frame, width=15, background='#2c5d87', foreground='white', borderwidth=2, date_pattern='y-mm-dd'); self.expiry_date_entry.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        ctk.CTkButton(add_batch_frame, text="Add Delivery", command=self.add_batch_event).grid(row=5, column=0, columnspan=2, pady=10, sticky="ew")
        self.load_suppliers()
    
    def load_suppliers(self):
        suppliers = get_all_suppliers()
        if not suppliers: self.supplier_menu.configure(values=["No suppliers found"]); return
        supplier_names = [s['name'] for s in suppliers]; self.suppliers_map = {s['name']: s['id'] for s in suppliers}; self.supplier_menu.configure(values=supplier_names); self.supplier_menu_var.set(supplier_names[0])
    
    def on_ingredient_type_select(self, event):
        if not self.ingredient_types_tree.selection(): return
        selected_item = self.ingredient_types_tree.focus(); item_details = self.ingredient_types_tree.item(selected_item)['values']; self.selected_ingredient_id = item_details[0]; ingredient_name = item_details[1]
        self.batch_label.configure(text=f"Batches for: {ingredient_name}"); self.refresh_batch_view()
    
    def refresh_batch_view(self):
        for item in self.batches_tree.get_children(): self.batches_tree.delete(item)
        if self.selected_ingredient_id is None: return
        batches = get_batches_for_ingredient(self.selected_ingredient_id)
        for batch in batches: self.batches_tree.insert("", "end", values=(batch['id'], batch['supplier_name'], batch['quantity_received'], batch['quantity_remaining'], batch['cost_per_unit'], batch['received_date'], batch['expiry_date']))
    
    def add_batch_event(self):
        if self.selected_ingredient_id is None: messagebox.showwarning("Selection Error", "Please select an ingredient type from the left table first."); return
        supplier_name = self.supplier_menu_var.get()
        if supplier_name == "Select Supplier" or supplier_name == "No suppliers found": messagebox.showwarning("Input Error", "Please select a supplier."); return
        details = {'ingredient_id': self.selected_ingredient_id, 'supplier_id': self.suppliers_map[supplier_name], 'quantity': self.batch_qty_entry.get(), 'cost_per_unit': self.batch_cost_entry.get(), 'expiry_date': self.expiry_date_entry.get_date().strftime('%Y-%m-%d')}
        if not details['quantity'] or not details['cost_per_unit']: messagebox.showwarning("Input Error", "Quantity and Cost fields are required."); return
        response = add_ingredient_batch(details); messagebox.showinfo("Response", response)
        if "successfully" in response: self.refresh_batch_view(); self.refresh_ingredient_types_table(); self.batch_qty_entry.delete(0, 'end'); self.batch_cost_entry.delete(0, 'end')
    
    def refresh_ingredient_types_table(self):
        for item in self.ingredient_types_tree.get_children(): self.ingredient_types_tree.delete(item)
        ingredients = get_all_ingredient_types()
        for ing in ingredients: self.ingredient_types_tree.insert("", "end", values=(ing['ingredient_id'], ing['ingredient_name'], ing['unit'], ing['total_stock'] if ing['total_stock'] is not None else 0, ing['reorder_level']))
    
    def add_ingredient_type_event(self):
        details = {'name': self.ing_name_entry.get(), 'unit': self.ing_unit_entry.get(), 'reorder_level': self.ing_reorder_entry.get()}
        if not all(details.values()): messagebox.showwarning("Input Error", "All fields are required."); return
        response = add_ingredient_type(details); messagebox.showinfo("Response", response)
        if "successfully" in response: self.refresh_ingredient_types_table(); self.ing_name_entry.delete(0, 'end'); self.ing_unit_entry.delete(0, 'end'); self.ing_reorder_entry.delete(0, 'end'); self.load_all_ingredients_for_menu()
    
    def populate_employees_tab(self, tab):
        self.selected_employee_id = None
        tab.grid_columnconfigure(0, weight=1); tab.grid_columnconfigure(1, weight=3); tab.grid_rowconfigure(0, weight=1)
        form_frame = ctk.CTkFrame(tab); form_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew"); form_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(form_frame, text="Manage Employees", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, columnspan=2, pady=20)
        ctk.CTkLabel(form_frame, text="First Name:").grid(row=1, column=0, padx=10, pady=5, sticky="w"); self.fname_entry = ctk.CTkEntry(form_frame); self.fname_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(form_frame, text="Last Name:").grid(row=2, column=0, padx=10, pady=5, sticky="w"); self.lname_entry = ctk.CTkEntry(form_frame); self.lname_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(form_frame, text="Email:").grid(row=3, column=0, padx=10, pady=5, sticky="w"); self.email_entry = ctk.CTkEntry(form_frame); self.email_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(form_frame, text="Username:").grid(row=4, column=0, padx=10, pady=5, sticky="w"); self.username_entry = ctk.CTkEntry(form_frame); self.username_entry.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(form_frame, text="Password:").grid(row=5, column=0, padx=10, pady=5, sticky="w"); self.password_entry = ctk.CTkEntry(form_frame, show="*"); self.password_entry.grid(row=5, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(form_frame, text="Role:").grid(row=6, column=0, padx=10, pady=5, sticky="w"); self.role_menu = ctk.CTkOptionMenu(form_frame, values=["manager", "waiter", "chef"]); self.role_menu.grid(row=6, column=1, padx=10, pady=5, sticky="ew")
        button_frame = ctk.CTkFrame(form_frame); button_frame.grid(row=7, column=0, columnspan=2, pady=20); button_frame.grid_columnconfigure((0,1,2,3), weight=1)
        ctk.CTkButton(button_frame, text="Add Employee", command=self.add_employee_event).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(button_frame, text="Update Selected", command=self.update_employee_event).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(button_frame, text="Delete Selected", command=self.delete_employee_event, fg_color="#D32F2F", hover_color="#B71C1C").grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(button_frame, text="Clear Form", command=self.clear_form_button_action).grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        table_frame = ctk.CTkFrame(tab); table_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew"); table_frame.grid_rowconfigure(0, weight=1); table_frame.grid_columnconfigure(0, weight=1)
        columns = ("ID", "First Name", "Last Name", "Role", "Email", "Username"); self.employee_tree = ttk.Treeview(table_frame, columns=columns, show="headings"); self.employee_tree.grid(row=0, column=0, sticky="nsew")
        for col in columns: self.employee_tree.column(col, anchor='center')
        v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.employee_tree.yview); v_scroll.grid(row=0, column=1, sticky="ns"); self.employee_tree.configure(yscrollcommand=v_scroll.set)
        h_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.employee_tree.xview); h_scroll.grid(row=1, column=0, sticky="ew"); self.employee_tree.configure(xscrollcommand=h_scroll.set)
        self.employee_tree.bind("<<TreeviewSelect>>", self.on_employee_select); self.refresh_employee_table()
    
    def clear_form_fields(self):
        self.fname_entry.delete(0, 'end'); self.lname_entry.delete(0, 'end'); self.email_entry.delete(0, 'end'); self.username_entry.delete(0, 'end'); self.password_entry.delete(0, 'end')
    
    def clear_form_button_action(self):
        self.selected_employee_id = None;
        if self.employee_tree.selection(): self.employee_tree.selection_remove(self.employee_tree.selection())
        self.username_entry.configure(state="normal"); self.password_entry.configure(state="normal"); self.clear_form_fields()
    
    def on_employee_select(self, event):
        if not self.employee_tree.selection(): return
        selected_item = self.employee_tree.focus(); emp_data = self.employee_tree.item(selected_item)['values']
        self.clear_form_fields()
        self.selected_employee_id = emp_data[0]
        self.fname_entry.insert(0, emp_data[1]); self.lname_entry.insert(0, emp_data[2]); self.role_menu.set(emp_data[3]); self.email_entry.insert(0, emp_data[4])
        self.username_entry.configure(state="normal"); self.username_entry.delete(0, 'end'); self.username_entry.insert(0, emp_data[5]); self.username_entry.configure(state="disabled")
        self.password_entry.configure(state="disabled")
    
    def refresh_employee_table(self):
        for item in self.employee_tree.get_children(): self.employee_tree.delete(item)
        employees = get_all_employees()
        for col in self.employee_tree["columns"]: self.employee_tree.heading(col, text=col)
        for emp in employees: self.employee_tree.insert("", "end", values=(emp['id'], emp['fname'], emp['lname'], emp['role'], emp['email'], emp['username']))
    
    def add_employee_event(self):
        details = {'fname': self.fname_entry.get(), 'lname': self.lname_entry.get(), 'email': self.email_entry.get(), 'username': self.username_entry.get(), 'password': self.password_entry.get(), 'role': self.role_menu.get()}
        if not all(details.values()):
            messagebox.showwarning("Input Error", "All fields are required for adding an employee.")
            return
        if not self.is_valid_email(details['email']):
            messagebox.showwarning("Input Error", "Please enter a valid email address.")
            return
        response = add_employee(details)
        messagebox.showinfo("Response", response)
        if "successfully" in response:
            self.refresh_employee_table()
            self.clear_form_button_action()

    def update_employee_event(self):
        if self.selected_employee_id is None:
            messagebox.showwarning("Selection Error", "Please select an employee from the table to update.")
            return
        details = {'fname': self.fname_entry.get(), 'lname': self.lname_entry.get(), 'email': self.email_entry.get(), 'role': self.role_menu.get()}
        if not all(details.values()):
            messagebox.showwarning("Input Error", "First name, last name, email, and role are required.")
            return
        if not self.is_valid_email(details['email']):
            messagebox.showwarning("Input Error", "Please enter a valid email address.")
            return
        response = update_employee(self.selected_employee_id, details)
        messagebox.showinfo("Response", response)
        if "successfully" in response:
            self.refresh_employee_table()
            self.clear_form_button_action()

    def delete_employee_event(self):
        if self.selected_employee_id is None: messagebox.showwarning("Selection Error", "Please select an employee from the table to delete."); return
        if self.selected_employee_id == self.controller.user_info.get('employee_id'): messagebox.showerror("Action Forbidden", "You cannot delete your own account while logged in."); return
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete employee ID {self.selected_employee_id}?\nThis action cannot be undone."):
            response = delete_employee(self.selected_employee_id); messagebox.showinfo("Response", response)
            if "successfully" in response: self.refresh_employee_table(); self.clear_form_button_action()

if __name__ == "__main__":
    app = App()
    app.mainloop()