# Restaurant Inventory & Management System

A comprehensive, multi-user desktop application designed to manage a restaurant's core operations, from inventory and recipe management to point-of-sale and business analytics. This system provides a robust backend powered by MySQL and an intuitive graphical user interface built with Python.

---

##  Key Features

- **Secure Authentication:** A secure login system with hashed passwords and a one-time script for initial admin user creation.
- **Role-Based Access Control:** A tailored user experience for different employee roles (Admin, Manager, Chef, Waiter), ensuring users only see the modules relevant to their job.
- **Complete Management Modules:** Full CRUD (Create, Read, Update, Delete) functionality for:
    - **Employees:** Manage staff accounts and roles.
    - **Suppliers:** Keep track of all vendor information.
    - **Inventory:** Manage raw ingredients, track batches with expiry dates, and receive low-stock alerts.
    - **Menu & Recipes:** Create dishes, set prices, and define detailed recipes that link directly to your inventory.
- **Point-of-Sale (POS) Simulation:** A simple and efficient interface for waiters to process customer orders. The system automatically deducts ingredients from the inventory in real-time based on the recipes of sold items.
- **Business Intelligence Dashboard:** A dynamic dashboard for managers and admins, featuring:
    - **Key Performance Indicators (KPIs):** See total revenue, dishes sold, and total transactions at a glance.
    - **Visual Charts:** Analyze sales trends and top-selling dishes.
    - **Live Alerts:** A table for low-stock alerts to streamline purchasing decisions.

---

##  Tech Stack

- **Backend:** Python
- **Database:** MySQL
- **GUI Framework:** CustomTkinter (with `tkinter` core)
- **Data Visualization:** Matplotlib & Pandas
- **Database Connector:** PyMySQL

---

##  Project Structure

The project is organized into four main files for clarity and maintainability:

- `schema.sql`: The architectural blueprint for the MySQL database. Contains all `CREATE TABLE` and `CREATE VIEW` statements required to structure the data.
- `utils.py`: The backend engine. This file handles all database connections and contains the functions for all CRUD operations and data processing logic.
- `main.py`: The frontend of the application. It contains all the code for the graphical user interface, including windows, tabs, buttons, and event handling.
- `create_admin.py`: A command-line utility script to securely create the initial 'admin' user, which is the first step in setting up the application.
