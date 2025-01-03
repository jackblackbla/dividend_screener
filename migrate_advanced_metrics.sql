-- 기존 컬럼 삭제 후 재추가
ALTER TABLE dividend_v2.dividend_info
  DROP COLUMN IF EXISTS adjusted_ratio,
  DROP COLUMN IF EXISTS adjusted_dividend_per_share,
  DROP COLUMN IF EXISTS ex_dividend_date,
  DROP COLUMN IF EXISTS consecutive_years,
  DROP COLUMN IF EXISTS dividend_growth_3y,
  DROP COLUMN IF EXISTS dividend_growth_5y;

ALTER TABLE dividend_v2.dividend_info
  ADD COLUMN adjusted_ratio DECIMAL(10,4) NULL,
  ADD COLUMN adjusted_dividend_per_share DECIMAL(20,2) NULL,
  ADD COLUMN ex_dividend_date DATE NULL,
  ADD COLUMN consecutive_years INT DEFAULT 0,
  ADD COLUMN dividend_growth_3y DECIMAL(5,2) NULL,
  ADD COLUMN dividend_growth_5y DECIMAL(5,2) NULL;

-- 인덱스 추가 (필터링 성능 향상을 위해)
CREATE INDEX idx_dividend_consecutive ON dividend_v2.dividend_info(consecutive_years);
CREATE INDEX idx_dividend_growth_3y ON dividend_v2.dividend_info(dividend_growth_3y);
CREATE INDEX idx_dividend_growth_5y ON dividend_v2.dividend_info(dividend_growth_5y);