from sqlalchemy import create_engine, text

# DB 연결 설정 (root 계정)
DB_URL = "mysql+pymysql://root@localhost:3306/dividend"
engine = create_engine(DB_URL)

def create_tables():
    """필요한 테이블 생성"""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS stocks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                code VARCHAR(20) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                exchange VARCHAR(10) NOT NULL,
                sector VARCHAR(100),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS market (
                id INT AUTO_INCREMENT PRIMARY KEY,
                stock_id INT NOT NULL,
                date DATE NOT NULL,
                close_price DECIMAL(15,2),
                market_cap BIGINT,
                FOREIGN KEY (stock_id) REFERENCES stocks(id),
                UNIQUE KEY (stock_id, date)
            )
        """))
        conn.commit()

if __name__ == "__main__":
    create_tables()
    print("테이블 생성 완료")