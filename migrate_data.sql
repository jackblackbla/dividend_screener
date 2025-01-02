-- stocks 테이블로 데이터 이관
INSERT IGNORE INTO dividend_v2.stocks (code, name, sector, market_cap)
SELECT DISTINCT
    s.code,
    s.name,
    s.industry,
    NULL AS market_cap  -- market_cap 정보는 기존 DB에 없으므로 NULL 처리
FROM dividend.stocks s;

-- dividend_info 테이블로 데이터 이관
INSERT INTO dividend_v2.dividend_info (stock_id, year, dividend_per_share, adjusted_dividend_per_share, payout_ratio, has_dividend_cut)
SELECT
    s.stock_id,
    d.year,
    d.dividend_per_share,
    d.adjusted_dividend_per_share,
    NULL AS payout_ratio,  -- payout_ratio 정보는 기존 DB에 없으므로 NULL 처리
    0 AS has_dividend_cut  -- has_dividend_cut 정보는 기존 DB에 없으므로 기본값 0
FROM dividend.dividend_info d
JOIN dividend_v2.stocks s ON s.code = d.code;

-- events 테이블로 데이터 이관 (stock_issuance_reduction 테이블 사용)
INSERT INTO dividend_v2.events (stock_id, event_type, event_date, factor, description)
SELECT
    s.stock_id,
    CASE
        WHEN i.isu_dcrs_stle LIKE '%증자%' THEN '증자'
        WHEN i.isu_dcrs_stle LIKE '%감자%' THEN '감자'
        ELSE '기타'
    END AS event_type,
    i.isu_dcrs_de AS event_date,
    i.adjusted_ratio AS factor,
    CONCAT(i.isu_dcrs_stle, ' - ', i.isu_dcrs_stock_knd) AS description
FROM dividend.stock_issuance_reduction i
JOIN dividend_v2.stocks s ON s.code = i.corp_code;