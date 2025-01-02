START TRANSACTION;

-- events 테이블로 데이터 이관
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
JOIN dividend_v2.stocks s ON s.code COLLATE utf8mb4_unicode_ci = i.corp_code COLLATE utf8mb4_unicode_ci;

COMMIT;