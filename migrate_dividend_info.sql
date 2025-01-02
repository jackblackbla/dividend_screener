START TRANSACTION;

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
JOIN dividend_v2.stocks s ON s.code COLLATE utf8mb4_unicode_ci = d.code COLLATE utf8mb4_unicode_ci;

COMMIT;