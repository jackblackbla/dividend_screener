CREATE TABLE dividend_v2.stocks (
  stock_id INT AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(20) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL,
  sector VARCHAR(50),
  market_cap BIGINT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dividend_v2.dividend_info (
  dividend_id INT AUTO_INCREMENT PRIMARY KEY,
  stock_id INT NOT NULL,
  year INT NOT NULL,
  dividend_per_share DECIMAL(10,2),
  adjusted_dividend_per_share DECIMAL(10,2),
  payout_ratio DECIMAL(5,2),
  has_dividend_cut TINYINT(1) DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (stock_id) REFERENCES stocks(stock_id)
);

CREATE TABLE dividend_v2.events (
  event_id INT AUTO_INCREMENT PRIMARY KEY,
  stock_id INT NOT NULL,
  event_type VARCHAR(30) NOT NULL,
  event_date DATE NOT NULL,
  factor DECIMAL(10,5) NULL,
  description VARCHAR(200),
  FOREIGN KEY (stock_id) REFERENCES stocks(stock_id)
);

CREATE TABLE dividend_v2.users (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(100) NOT NULL UNIQUE,
  password_hash VARCHAR(200) NOT NULL,
  plan_type ENUM('FREE','BASIC','PREMIUM') DEFAULT 'FREE',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dividend_v2.watchlist (
  watchlist_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  stock_id INT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id),
  FOREIGN KEY (stock_id) REFERENCES stocks(stock_id)
);

CREATE TABLE dividend_v2.drip_scenario (
  scenario_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  stock_id INT NOT NULL,
  initial_investment DECIMAL(15,2),
  monthly_investment DECIMAL(15,2),
  dividend_reinvestment BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id),
  FOREIGN KEY (stock_id) REFERENCES stocks(stock_id)
);