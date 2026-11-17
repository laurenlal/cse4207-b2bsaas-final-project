import { useEffect, useState } from "react";
import { fetchProducts } from "./services/api";

export default function App() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchProducts("Sony WH-1000XM5 headphones")
      .then((data) => setProducts(data.products))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main style={{ padding: "2rem" }}>
      <h1>Best2Buy</h1>
      <p>Compare electronics prices across retailers.</p>

      <h2>Sony WH-1000XM5</h2>

      {loading && <p>Loading prices...</p>}
      {error && <p>Error: {error}</p>}

      {!loading && !error && products.length === 0 && (
        <p>No shopping results returned.</p>
      )}

      {products.length > 0 && (
        <table cellPadding="12">
          <thead>
            <tr>
              <th>Product</th>
              <th>Retailer</th>
              <th>Price</th>
              <th>Link</th>
            </tr>
          </thead>

          <tbody>
            {products.map((product, index) => (
              <tr key={`${product.productId ?? "item"}-${index}`}>
                <td>{product.productName}</td>
                <td>{product.retailer}</td>
                <td>${Number(product.price).toFixed(2)}</td>
                <td>
                  {product.url && (
                    <a
                      href={product.url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      View
                    </a>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}