# Dividend Screener

주식 배당금 스크리너 프로젝트

## 기술 스택
- Node.js
- Express
- Jest (테스트 프레임워크)
- ESLint & Prettier (코드 포맷팅)

## 설치 방법
1. 저장소 복제
```bash
git clone https://github.com/your-account/dividend-screener.git
cd dividend-screener
```

2. 종속성 설치
```bash
npm install
```

3. 환경 변수 설정
```bash
cp .env.example .env
```

## 실행 방법
개발 서버 실행:
```bash
npm start
```

테스트 실행:
```bash
npm test
```

코드 포맷팅:
```bash
npm run lint:fix
```

## 프로젝트 구조
```
my-dividend-screener/
├── domain/
├── application/
├── infrastructure/
├── presentation/
├── tests/
├── .gitignore
├── .env.example
├── package.json
└── README.md
```

## 기여 가이드
1. 새로운 기능은 feature 브랜치에서 개발
2. PR 생성 전에 테스트 및 lint 실행
3. 코드 리뷰 후 main 브랜치로 병합