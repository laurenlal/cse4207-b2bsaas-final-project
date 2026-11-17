import { formatPrice, formatWindow } from "../lib/format";
import PriceTag from "./PriceTag";
import ProductImage from "./ProductImage";
import RangeBar from "./RangeBar";

export default function StatsSummary({ item }) {
  const { stats } = item;
  const windowLabel = formatWindow(item.trackingDays);
  const drops = item.offers.filter((offer) => offer.isDrop);
  const biggest = drops.reduce(
    (best, offer) =>
      !best || offer.change.dropPercent > best.change.dropPercent
        ? offer
        : best,
    null,
  );

  return (
    <section className="summary" aria-labelledby="item-title">
      <ProductImage src={item.image} className="summary-image" />

      <div className="summary-main">
        <h1 id="item-title" className="page-title">
          {item.productName}
        </h1>

        <p className="summary-lowest">
          <span className="muted">Lowest new price</span>
          <PriceTag price={stats.currentLowest.price} size="lg" />
          <span>at {stats.currentLowest.retailer}</span>
        </p>

        {biggest && (
          <p className="drop-banner" role="status">
            Price dropped {biggest.change.dropPercent}% at {biggest.retailer},
            from {formatPrice(biggest.change.previousPrice)} to{" "}
            {formatPrice(biggest.price)}.
            {drops.length > 1 &&
              ` ${drops.length - 1} more ${drops.length === 2 ? "offer" : "offers"} dropped too.`}
          </p>
        )}

        <div className="summary-stats">
          <h2 className="summary-window">{windowLabel}</h2>
          <dl className="stat-row">
            <div>
              <dt>Low</dt>
              <dd>{formatPrice(stats.low)}</dd>
            </div>
            <div>
              <dt>Median</dt>
              <dd>{formatPrice(stats.median)}</dd>
            </div>
            <div>
              <dt>High</dt>
              <dd>{formatPrice(stats.high)}</dd>
            </div>
          </dl>
          <RangeBar
            stats={stats}
            price={stats.currentLowest.price}
            windowLabel={windowLabel}
            size="lg"
          />
        </div>
      </div>
    </section>
  );
}
