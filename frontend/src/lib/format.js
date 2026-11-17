const usd = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});

export function formatPrice(value) {
  return usd.format(value);
}

// Until 30 days of history exist, say so instead of implying a full month.
export function formatWindow(trackingDays) {
  if (trackingDays >= 30) return "Last 30 days";
  const unit = trackingDays === 1 ? "day" : "days";
  return `Since tracking began (${trackingDays} ${unit})`;
}
