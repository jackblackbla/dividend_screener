import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
      <div className="container">
        <Link className="navbar-brand" to="/">배당주 스크리너</Link>

        <button className="navbar-toggler" type="button"
                data-bs-toggle="collapse"
                data-bs-target="#navbarSupportedContent"
        >
          <span className="navbar-toggler-icon"></span>
        </button>

        <div className="collapse navbar-collapse" id="navbarSupportedContent">
          <ul className="navbar-nav me-auto mb-2 mb-lg-0">
            <li className="nav-item">
              <Link className="nav-link" to="/screener">스크리너</Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/calendar">배당 캘린더</Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/drip">DRIP 시뮬</Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/login">로그인</Link>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;