PRAGMA foreign_keys = ON;

-- 1. Create the 'products' table
-- This table stores the inventory items the agent can query.
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0
);

-- 2. Create the 'orders' table
-- This table tracks sales, allowing the agent to answer questions like "How many orders today?"
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    quantity INTEGER NOT NULL,
    order_date DATE NOT NULL, -- Format: YYYY-MM-DD
    total_amount DECIMAL(10, 2),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- 3. Seed Data: Products
-- Inserting a mix of high and low price items to test "Top 3 products by price"
INSERT INTO products (name, category, price, stock_quantity) VALUES 
('Pro Laptop X1', 'Electronics', 1299.99, 50),
('Gaming Mouse', 'Electronics', 59.99, 200),
('Mechanical Keyboard', 'Electronics', 149.50, 75),
('4K Monitor', 'Electronics', 399.00, 30),
('Ergonomic Chair', 'Furniture', 299.99, 15),
('Standing Desk', 'Furniture', 450.00, 10),
('USB-C Cable', 'Accessories', 12.99, 500),
('Wireless Headset', 'Electronics', 89.99, 120);

-- 4. Seed Data: Orders
-- Inserting orders with different dates to test date-based queries
-- Note: calculating total_amount manually here for simplicity
INSERT INTO orders (product_id, quantity, order_date, total_amount) VALUES 
(1, 1, DATE('now'), 1299.99),          -- Order placed "today"
(3, 2, DATE('now'), 299.00),           -- Order placed "today"
(7, 5, DATE('now', '-1 day'), 64.95),  -- Yesterday
(2, 1, DATE('now', '-2 days'), 59.99), -- 2 days ago
(6, 1, DATE('now'), 450.00),           -- Order placed "today"
(4, 2, DATE('now', '-7 days'), 798.00); -- Last week

-- Verification Query (Optional: just to see what's inside)
SELECT '--- Products ---' as TableName;
SELECT * FROM products;
SELECT '--- Orders ---' as TableName;
SELECT * FROM orders;