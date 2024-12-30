import pandas as pd

# CSV 파일 읽기 (EUC-KR 인코딩)
df = pd.read_csv('temp_krx.csv', encoding='euc-kr')

# UTF-8 인코딩으로 저장
df.to_csv('temp_krx_utf8.csv', index=False, encoding='utf-8')