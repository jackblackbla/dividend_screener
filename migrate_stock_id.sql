START TRANSACTION;

-- stocks 테이블의 id 컬럼을 stock_id로 변경
ALTER TABLE dividend_v2.stocks
CHANGE COLUMN id stock_id INT(11) NOT NULL AUTO_INCREMENT;

-- stocks 테이블을 참조하는 외래키 제약조건 업데이트
ALTER TABLE dividend_v2.financial_statements
DROP FOREIGN KEY financial_statements_ibfk_1,
CHANGE COLUMN stock_id stock_id INT(11) NOT NULL,
ADD CONSTRAINT financial_statements_stock_id_fk
FOREIGN KEY (stock_id) REFERENCES dividend_v2.stocks(stock_id);

ALTER TABLE dividend_v2.dividend_info
DROP FOREIGN KEY dividend_info_ibfk_1,
CHANGE COLUMN stock_id stock_id INT(11) NOT NULL,
ADD CONSTRAINT dividend_info_stock_id_fk
FOREIGN KEY (stock_id) REFERENCES dividend_v2.stocks(stock_id);

ALTER TABLE dividend_v2.dividend_yields
DROP FOREIGN KEY dividend_yields_ibfk_1,
CHANGE COLUMN stock_id stock_id INT(11) NOT NULL,
ADD CONSTRAINT dividend_yields_stock_id_fk
FOREIGN KEY (stock_id) REFERENCES dividend_v2.stocks(stock_id);

ALTER TABLE dividend_v2.stock_prices
DROP FOREIGN KEY stock_prices_ibfk_1,
CHANGE COLUMN stock_id stock_id INT(11) NOT NULL,
ADD CONSTRAINT stock_prices_stock_id_fk
FOREIGN KEY (stock_id) REFERENCES dividend_v2.stocks(stock_id);

ALTER TABLE dividend_v2.stock_issuance_reduction
DROP FOREIGN KEY stock_issuance_reduction_ibfk_1,
CHANGE COLUMN stock_id stock_id INT(11) NOT NULL,
ADD CONSTRAINT stock_issuance_reduction_stock_id_fk
FOREIGN KEY (stock_id) REFERENCES dividend_v2.stocks(stock_id);

COMMIT;