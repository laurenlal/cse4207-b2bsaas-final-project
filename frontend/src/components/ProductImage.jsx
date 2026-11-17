export default function ProductImage({ src, className = "" }) {
  if (!src)
    return (
      <span
        className={`product-image product-image-empty ${className}`}
        aria-hidden="true"
      />
    );
  return (
    <img
      className={`product-image ${className}`}
      src={src}
      alt=""
      loading="lazy"
    />
  );
}
