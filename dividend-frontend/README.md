# Dividend Screener

주식 배당금 스크리너 애플리케이션

## 프로젝트 개요

이 프로젝트는 한국 주식 시장의 배당 정보를 분석하고 필터링할 수 있는 웹 애플리케이션입니다. OpenDART API를 활용하여 기업의 재무 정보를 수집하고, 사용자가 다양한 조건으로 배당 정보를 검색할 수 있도록 합니다.

## 주요 기능

- 배당 정보 검색 및 필터링
- 기업 재무 정보 조회
- 배당 수익률, 배당 성장률 등 주요 지표 제공
- 사용자 정의 필터 기능

## 기술 스택

### 백엔드
- Python 3.10
- FastAPI
- SQLAlchemy
- OpenDART API
- SQLite

### 프론트엔드
- React 18
- TypeScript
- Tailwind CSS
- Vite

## 프로젝트 구조

```
dividend_screener/
├── api_server/            # FastAPI 서버
├── dividend-frontend/     # React 프론트엔드
├── adapters/              # 외부 API 어댑터
├── repositories/          # 데이터베이스 리포지토리
├── usecases/              # 비즈니스 로직
├── tests/                 # 테스트 코드
├── docs/                  # 문서
└── alembic/               # 데이터베이스 마이그레이션
```

## 설치 및 실행

### 백엔드

1. 가상 환경 생성 및 활성화:
```bash
python -m venv venv
source venv/bin/activate
```

2. 의존성 설치:
```bash
pip install -r requirements.txt
```

3. 데이터베이스 마이그레이션:
```bash
alembic upgrade head
```

4. 서버 실행:
```bash
uvicorn api_server.main:app --reload
```

### 프론트엔드

1. 의존성 설치:
```bash
cd dividend-frontend
npm install
```

2. 개발 서버 실행:
```bash
npm run dev
```

## 기여 가이드

기여를 원하시면 다음 단계를 따르세요:

1. 이슈를 생성하여 변경 사항을 논의합니다.
2. 새로운 브랜치를 생성합니다 (`git checkout -b feature/your-feature`).
3. 변경 사항을 커밋합니다 (`git commit -m 'Add some feature'`).
4. 브랜치를 푸시합니다 (`git push origin feature/your-feature`).
5. 풀 리퀘스트를 생성합니다.

## 라이선스

MIT License
