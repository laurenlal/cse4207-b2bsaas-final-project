import { Link } from "react-router-dom";
import PriceTag from "./PriceTag";
import ProductImage from "./ProductImage";

export default function ItemCard({ item }) {
  return (
    <li>
      <Link
        to={`/item/${item.productId}`}
        className={`item-card${item.hasPriceDrop ? " has-drop" : ""}`}
      >
        <ProductImage src={item.image} className="item-card-image" />
        <span className="item-card-name">{item.productName}</span>
        <span className="item-card-prices">
          <PriceTag price={item.lowestPrice} />
          <span className="item-card-meta">
            at {item.lowestRetailer}, {item.offerCount} offers
          </span>
        </span>
        {item.hasPriceDrop && (
          <span className="drop-badge">
            Price dropped {item.bestDropPercent}%
          </span>
        )}
      </Link>
    </li>
  );
}
