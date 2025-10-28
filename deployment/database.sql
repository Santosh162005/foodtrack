-- Food Expiry Tracker Database Schema

CREATE DATABASE IF NOT EXISTS food_expiry_tracker;
USE food_expiry_tracker;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Food Items Table
CREATE TABLE IF NOT EXISTS food_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    food_name VARCHAR(200) NOT NULL,
    expiry_date DATE NOT NULL,
    purchase_date DATE DEFAULT (CURRENT_DATE),
    image_path VARCHAR(500),
    status ENUM('Fresh', 'Near Expiry', 'Expired') DEFAULT 'Fresh',
    category VARCHAR(100),
    quantity VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    food_item_id INT NOT NULL,
    message TEXT NOT NULL,
    is_sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (food_item_id) REFERENCES food_items(id) ON DELETE CASCADE
);

-- Food Categories Table
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

-- Insert Default Categories
INSERT INTO categories (name, description) VALUES
('Dairy', 'Milk, cheese, yogurt, butter'),
('Vegetables', 'Fresh vegetables'),
('Fruits', 'Fresh fruits'),
('Meat & Poultry', 'Chicken, beef, pork, lamb'),
('Seafood', 'Fish and shellfish'),
('Beverages', 'Drinks and juices'),
('Bakery', 'Bread, pastries, cakes'),
('Frozen Foods', 'Frozen meals and items'),
('Canned Goods', 'Canned vegetables, fruits, soups'),
('Condiments', 'Sauces, dressings, spices'),
('Snacks', 'Chips, cookies, crackers'),
('Other', 'Miscellaneous items');

-- Create indexes for better performance
CREATE INDEX idx_user_id ON food_items(user_id);
CREATE INDEX idx_expiry_date ON food_items(expiry_date);
CREATE INDEX idx_status ON food_items(status);
CREATE INDEX idx_user_notifications ON notifications(user_id);
