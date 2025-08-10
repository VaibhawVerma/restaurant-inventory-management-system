CREATE DATABASE IF NOT EXISTS `restaurant-inventory-db`;
USE `restaurant-inventory-db`;

-- =================================================================
-- 1. USER AND EMPLOYEE TABLES
-- =================================================================

-- Stores hashed login credentials for security
CREATE TABLE IF NOT EXISTS `user_account` (
  `uid` INT AUTO_INCREMENT PRIMARY KEY,
  `username` VARCHAR(50) UNIQUE NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL
);

-- Stores employee details
CREATE TABLE IF NOT EXISTS `employee` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `role` ENUM('admin', 'manager', 'waiter', 'chef') NOT NULL,
  `fname` VARCHAR(50) NOT NULL,
  `mname` VARCHAR(50),
  `lname` VARCHAR(50) NOT NULL,
  `email` VARCHAR(100) UNIQUE,
  `phone` VARCHAR(15),
  `manager_id` INT,
  `uid` INT UNIQUE,
  FOREIGN KEY (`uid`) REFERENCES `user_account`(`uid`) ON DELETE SET NULL,
  FOREIGN KEY (`manager_id`) REFERENCES `employee`(`id`) ON DELETE SET NULL
);

-- =================================================================
-- 2. MENU AND PROFITABILITY TABLES
-- =================================================================

-- Stores dishes with their selling price
CREATE TABLE IF NOT EXISTS `dish` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `dname` VARCHAR(100) UNIQUE NOT NULL,
  `price` DECIMAL(10, 2) NOT NULL,
  `category` VARCHAR(50)
);

-- =================================================================
-- 3. SALES AND ORDERS TABLES
-- =================================================================

-- Records each sale transaction with a timestamp and total amount
CREATE TABLE IF NOT EXISTS `sales` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `sale_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `waiter_id` INT,
  `total_amount` DECIMAL(10, 2) NOT NULL,
  FOREIGN KEY (`waiter_id`) REFERENCES `employee`(`id`) ON DELETE SET NULL
);

-- Linking table for the many-to-many relationship between sales and dishes
CREATE TABLE IF NOT EXISTS `sale_items` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `sale_id` INT,
  `dish_id` INT,
  `quantity` INT NOT NULL,
  `price_per_item` DECIMAL(10, 2) NOT NULL,
  FOREIGN KEY (`sale_id`) REFERENCES `sales`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`dish_id`) REFERENCES `dish`(`id`) ON DELETE CASCADE
);

-- =================================================================
-- 4. INVENTORY & SUPPLIER TABLES
-- =================================================================

-- Stores details about suppliers
CREATE TABLE IF NOT EXISTS `supplier` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(100),
  `phone` VARCHAR(15)
);

-- Stores general information about ingredients
CREATE TABLE IF NOT EXISTS `ingredients` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) UNIQUE NOT NULL,
  `unit` VARCHAR(20) NOT NULL, -- 'kg', 'liters', 'units'
  `reorder_level` INT -- The quantity threshold to trigger a reorder warning
);

-- table for tracking individual batches of ingredients
CREATE TABLE IF NOT EXISTS `ingredient_batches` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `ingredient_id` INT,
    `supplier_id` INT,
    `quantity_received` DECIMAL(10, 2) NOT NULL,
    `quantity_remaining` DECIMAL(10, 2) NOT NULL,
    `cost_per_unit` DECIMAL(10, 2) NOT NULL,
    `received_date` DATE,
    `expiry_date` DATE NOT NULL,
    FOREIGN KEY (`ingredient_id`) REFERENCES `ingredients`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`supplier_id`) REFERENCES `supplier`(`id`) ON DELETE SET NULL
);

-- Stores the recipe for each dish
CREATE TABLE IF NOT EXISTS `recipe` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `dish_id` INT,
  `ingredient_id` INT,
  `quantity_needed` DECIMAL(10, 2) NOT NULL,
  FOREIGN KEY (`dish_id`) REFERENCES `dish`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`ingredient_id`) REFERENCES `ingredients`(`id`) ON DELETE CASCADE
);

-- =================================================================
-- 5. VIEWS 
-- =================================================================

-- VIEW to see the current total stock of each ingredient
CREATE OR REPLACE VIEW `current_inventory_view` AS
SELECT
    i.id AS ingredient_id,
    i.name AS ingredient_name,
    i.unit,
    i.reorder_level,
    SUM(ib.quantity_remaining) AS total_stock
FROM
    ingredients i
LEFT JOIN
    ingredient_batches ib ON i.id = ib.ingredient_id
GROUP BY
    i.id;

-- VIEW to calculate the cost of making each dish
CREATE OR REPLACE VIEW `dish_cost_view` AS
SELECT
    d.id AS dish_id,
    d.dname,
    d.price AS selling_price,
    SUM(r.quantity_needed * ib.cost_per_unit) AS material_cost,
    (d.price - SUM(r.quantity_needed * ib.cost_per_unit)) AS estimated_profit
FROM
    dish d
JOIN
    recipe r ON d.id = r.dish_id
JOIN
    ingredients i ON r.ingredient_id = i.id
JOIN
    (SELECT ingredient_id, AVG(cost_per_unit) as cost_per_unit FROM ingredient_batches GROUP BY ingredient_id) ib
    ON i.id = ib.ingredient_id
GROUP BY
    d.id;
