const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function fetchProducts(query) {
  const response = await fetch(
    `${API_BASE_URL}/products?q=${encodeURIComponent(query)}`
  );

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json();
}