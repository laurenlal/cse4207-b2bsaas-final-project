import { formatPrice } from "../lib/format";
import { describePosition, rangePosition } from "../lib/offers";

// A track from the low to the high price, a tick at the median, and a dot for today's price.
export default function RangeBar({ stats, price, windowLabel, size = "sm" }) {
  const dot = rangePosition(stats, price) * 100;
  const median = rangePosition(stats, stats.median) * 100;
  const { text, tone } = describePosition(stats, price);

  const summary =
    `${formatPrice(price)} now. ${windowLabel}: low ${formatPrice(stats.low)}, ` +
    `median ${formatPrice(stats.median)}, high ${formatPrice(stats.high)}.`;

  return (
    <div className={`range range-${size}`}>
      <div className="range-track" role="img" aria-label={summary}>
        <span className="range-median" style={{ left: `${median}%` }} />
        <span
          className={`range-dot tone-${tone}`}
          style={{ left: `${dot}%` }}
        />
      </div>
      <div className="range-ends">
        <span>{formatPrice(stats.low)}</span>
        <span className={`range-caption tone-${tone}`}>{text}</span>
        <span>{formatPrice(stats.high)}</span>
      </div>
    </div>
  );
}
