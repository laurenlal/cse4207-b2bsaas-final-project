import { Link, Route, Routes } from "react-router-dom";
import HomePage from "./pages/HomePage";
import ItemPage from "./pages/ItemPage";

export default function App() {
  return (
    <>
      <header className="app-header">
        <Link to="/" className="brand">
          <span className="brand-tag" aria-hidden="true" />
          Best2Buy
        </Link>
      </header>

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/item/:productId" element={<ItemPage />} />
        <Route
          path="*"
          element={
            <main className="page">
              <h1 className="page-title">Page not found</h1>
              <Link to="/" className="text-link">
                Back to your wishlist
              </Link>
            </main>
          }
        />
      </Routes>
    </>
  );
}
