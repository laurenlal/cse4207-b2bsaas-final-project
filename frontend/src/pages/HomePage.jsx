import { useEffect } from "react";
import ItemCard from "../components/ItemCard";
import { useAsync } from "../hooks/useAsync";
import { fetchWishlist } from "../services/api";

export default function HomePage() {
  const wishlist = useAsync(fetchWishlist, "wishlist");

  useEffect(() => {
    document.title = "Wishlist | Best2Buy";
  }, []);

  return (
    <main className="page">
      <h1 className="page-title">Your wishlist</h1>

      {wishlist.status === "loading" && (
        <p className="muted">Loading your wishlist...</p>
      )}
      {wishlist.status === "error" && (
        <p className="error">
          Couldn&apos;t load your wishlist. Check that the API is running, then
          reload the page.
        </p>
      )}
      {wishlist.status === "ready" && (
        <ul className="item-grid">
          {wishlist.data.items.map((item) => (
            <ItemCard key={item.productId} item={item} />
          ))}
        </ul>
      )}
    </main>
  );
}
