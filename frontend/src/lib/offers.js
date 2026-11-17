export const CONDITION_ORDER = ["new", "refurbished", "used"];
export const CONDITION_LABELS = {
  new: "New",
  refurbished: "Refurbished",
  used: "Used",
};

export function parsePrice(text) {
  const value = Number.parseFloat(text);
  return Number.isFinite(value) ? value : null;
}

// Where a price sits between a low and a high, from 0 (the low) to 1 (the high).
export function rangePosition({ low, high }, price) {
  const span = high - low;
  if (span <= 0) return 0.5;
  return Math.min(Math.max((price - low) / span, 0), 1);
}

// Plain-language description of a price relative to its range.
export function describePosition(stats, price) {
  if (price <= stats.low) return { text: "At its low", tone: "good" };

  const position = rangePosition(stats, price);
  if (position < 0.25) return { text: "Near its low", tone: "good" };
  if (position > 0.75) return { text: "Near its high", tone: "high" };
  if (price < stats.median) return { text: "Below its median", tone: "good" };
  return { text: "Above its median", tone: "neutral" };
}

// Empty retailers/conditions arrays mean "no filter". min/max are numbers or null.
export function applyOfferView(
  offers,
  { retailers, conditions, min, max, sortDir },
) {
  const direction = sortDir === "desc" ? -1 : 1;

  return offers
    .filter(
      (offer) => retailers.length === 0 || retailers.includes(offer.retailer),
    )
    .filter(
      (offer) =>
        conditions.length === 0 || conditions.includes(offer.condition),
    )
    .filter((offer) => min === null || offer.price >= min)
    .filter((offer) => max === null || offer.price <= max)
    .sort(
      (a, b) =>
        direction * (a.price - b.price) || a.retailer.localeCompare(b.retailer),
    );
}
