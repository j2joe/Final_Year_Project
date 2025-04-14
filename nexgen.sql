CREATE DATABASE nexgen;
USE nexgen;

-- Users table (for signups)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15),
    business_name VARCHAR(100),
    password VARCHAR(255) NOT NULL,
    country VARCHAR(50),
    state VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Login sessions table
CREATE TABLE user_logins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

USE nexgen;

CREATE TABLE login_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('success', 'failed') NOT NULL,
    ip_address VARCHAR(45),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

USE nexgen;
CREATE TABLE password_reset_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(100) UNIQUE NOT NULL,
    expires_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

USE nexgen;
CREATE TABLE work_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    client_name VARCHAR(100),
    status ENUM('Draft','Active','Completed','Archived') DEFAULT 'Draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE work_order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    work_order_id INT NOT NULL,
    description TEXT NOT NULL,
    category ENUM('Materials','Labor','Shipping','Software','Other') NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    is_expense BOOLEAN DEFAULT TRUE,
    date DATE NOT NULL,
    FOREIGN KEY (work_order_id) REFERENCES work_orders(id) ON DELETE CASCADE
);

use nexgen;
ALTER TABLE login_attempts 
ADD COLUMN device VARCHAR(255) NULL AFTER ip_address,
ADD COLUMN location VARCHAR(255) NULL AFTER device;

use nexgen;
-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    name VARCHAR(50) NOT NULL,
    type ENUM('INCOME', 'EXPENSE') NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    category_id INT,
    amount DECIMAL(10,2) NOT NULL,
    description VARCHAR(255),
    date DATE NOT NULL,
    type ENUM('INCOME', 'EXPENSE') NOT NULL,
    payment_method ENUM('CASH', 'CREDIT_CARD', 'BANK_TRANSFER', 'OTHER'),
    is_recurring BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Default income categories
INSERT INTO categories (user_id, name, type) VALUES 
(1, 'Salary', 'INCOME'),
(1, 'Freelance', 'INCOME'),
(1, 'Investments', 'INCOME'),
(1, 'Gifts', 'INCOME'),
(1, 'Other Income', 'INCOME');

-- Default expense categories
INSERT INTO categories (user_id, name, type) VALUES 
(1, 'Food & Dining', 'EXPENSE'),
(1, 'Transportation', 'EXPENSE'),
(1, 'Housing', 'EXPENSE'),
(1, 'Utilities', 'EXPENSE'),
(1, 'Entertainment', 'EXPENSE'),
(1, 'Healthcare', 'EXPENSE'),
(1, 'Shopping', 'EXPENSE'),
(1, 'Other Expenses', 'EXPENSE');


