import { formatPrice } from "../lib/format";

export default function PriceTag({ price, size = "md" }) {
  return <span className={`tag tag-${size}`}>{formatPrice(price)}</span>;
}
