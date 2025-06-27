import { Routes, Route, Link, useLocation } from 'react-router-dom';
import SourcesPage from './pages/SourcesPage';
import ArticlesPage from './pages/ArticlesPage';

function App() {
  const location = useLocation();

  return (
    <div>
      <header>
        <div className="container">
          <nav>
            <Link to="/" className="logo">
              TLDR
            </Link>
            <ul className="nav-links">
              <li>
                <Link 
                  to="/sources" 
                  className={location.pathname === '/sources' ? 'active' : ''}
                >
                  Sources
                </Link>
              </li>
            </ul>
          </nav>
        </div>
      </header>

      <main className="container">
        <Routes>
          <Route path="/" element={<ArticlesPage />} />
          <Route path="/sources" element={<SourcesPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App; 