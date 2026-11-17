const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function getJson(path, signal) {
  const response = await fetch(`${API_BASE_URL}${path}`, { signal });

  if (!response.ok) {
    const error = new Error(`API request failed: ${response.status}`);
    error.status = response.status;
    throw error;
  }

  return response.json();
}

// Raw search results (the original endpoint).
export async function fetchProducts(query) {
  return getJson(`/products?q=${encodeURIComponent(query)}`);
}

// Wishlist endpoints. Each takes (argument, abortSignal) so they work with useAsync.
export function fetchWishlist(_arg, signal) {
  return getJson("/wishlist", signal);
}

export function fetchItem(productId, signal) {
  return getJson(`/wishlist/${encodeURIComponent(productId)}`, signal);
}
