import { useEffect } from "react";
import {
  Link,
  useLocation,
  useParams,
  useSearchParams,
} from "react-router-dom";
import OfferExplorer from "../components/OfferExplorer";
import Sidebar from "../components/Sidebar";
import StatsSummary from "../components/StatsSummary";
import { useAsync } from "../hooks/useAsync";
import { fetchItem, fetchWishlist } from "../services/api";

export default function ItemPage() {
  const { productId } = useParams();
  const { search } = useLocation();
  const [params, setParams] = useSearchParams();
  const sortDir = params.get("sort") === "desc" ? "desc" : "asc";

  const wishlist = useAsync(fetchWishlist, "wishlist");
  const item = useAsync(fetchItem, productId);

  const itemName = item.data?.productName;
  useEffect(() => {
    document.title = itemName ? `${itemName} | Best2Buy` : "Best2Buy";
  }, [itemName]);

  // Only the sort direction lives in the URL; it carries over when you pick another item.
  const onSortChange = (dir) =>
    setParams(dir === "desc" ? { sort: "desc" } : {}, { replace: true });

  return (
    <div className="item-layout">
      <Sidebar wishlist={wishlist} search={search} />

      <main className="item-main">
        {item.status === "loading" && (
          <p className="muted">Loading prices...</p>
        )}

        {item.status === "error" && item.error.status === 404 && (
          <>
            <h1 className="page-title">We couldn&apos;t find that item</h1>
            <Link to="/" className="text-link">
              Back to your wishlist
            </Link>
          </>
        )}

        {item.status === "error" && item.error.status !== 404 && (
          <p className="error">
            Couldn&apos;t load prices for this item. Check that the API is
            running, then reload the page.
          </p>
        )}

        {item.status === "ready" && (
          <>
            <StatsSummary item={item.data} />
            <OfferExplorer
              key={item.data.productId}
              item={item.data}
              sortDir={sortDir}
              onSortChange={onSortChange}
            />
          </>
        )}
      </main>
    </div>
  );
}
