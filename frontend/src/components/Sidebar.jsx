import { NavLink } from "react-router-dom";
import PriceTag from "./PriceTag";
import ProductImage from "./ProductImage";

// `search` is carried onto every link so the sort direction survives switching items.
export default function Sidebar({ wishlist, search }) {
  return (
    <nav className="sidebar" aria-label="Wishlist">
      <h2 className="sidebar-title">Wishlist</h2>

      {wishlist.status === "loading" && (
        <p className="muted">Loading items...</p>
      )}
      {wishlist.status === "error" && (
        <p className="muted">Couldn&apos;t load your wishlist.</p>
      )}

      {wishlist.status === "ready" && (
        <ul className="sidebar-list">
          {wishlist.data.items.map((item) => (
            <li key={item.productId}>
              <NavLink
                to={{ pathname: `/item/${item.productId}`, search }}
                className="sidebar-link"
              >
                <ProductImage src={item.image} className="sidebar-image" />
                <span className="sidebar-name">{item.productName}</span>
                <span className="sidebar-price">
                  <PriceTag price={item.lowestPrice} size="sm" />
                  {item.hasPriceDrop && (
                    <span className="drop-dot">Price drop</span>
                  )}
                </span>
              </NavLink>
            </li>
          ))}
        </ul>
      )}
    </nav>
  );
}
