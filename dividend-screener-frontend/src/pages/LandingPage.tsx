import React from 'react';
import { Link } from 'react-router-dom';

function LandingPage() {
  return (
    <div className="container mt-4">
      <div className="p-5 mb-4 bg-light rounded-3">
        <div className="container-fluid py-5">
          <h1 className="display-5 fw-bold">“배당주 스크리너 MVP”</h1>
          <p className="col-md-8 fs-4">
            연속배당주 찾기, DRIP 재투자 시뮬, 배당 캘린더 등<br />
            다양한 기능을 제공합니다.
          </p>
          <div>
            <Link to="/screener" className="btn btn-primary btn-lg me-3">
              바로 스크리너로 가기
            </Link>
            <Link to="/calendar" className="btn btn-outline-secondary btn-lg">
              배당 캘린더 보기
            </Link>
          </div>
        </div>
      </div>

      {/* (선택) 로그인/회원가입 버튼 */}
      <div>
        <Link to="/login" className="btn btn-link">로그인</Link>
        <Link to="/signup" className="btn btn-link">회원가입</Link>
      </div>
    </div>
  );
}
export default LandingPage;