/** Decorative blueprint grid — scientific / technical drawing aesthetic */
export default function BlueprintGrid({
  className = "",
  opacity = 0.35,
}: {
  className?: string;
  opacity?: number;
}) {
  return (
    <svg
      className={className}
      aria-hidden
      xmlns="http://www.w3.org/2000/svg"
      width="100%"
      height="100%"
      preserveAspectRatio="xMidYMid slice"
    >
      <defs>
        <pattern id="bp-grid" width="24" height="24" patternUnits="userSpaceOnUse">
          <path
            d="M 24 0 L 0 0 0 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="0.5"
            opacity={opacity}
          />
        </pattern>
        <pattern id="bp-grid-major" width="120" height="120" patternUnits="userSpaceOnUse">
          <rect width="120" height="120" fill="url(#bp-grid)" />
          <path
            d="M 120 0 L 0 0 0 120"
            fill="none"
            stroke="currentColor"
            strokeWidth="1"
            opacity={opacity * 1.4}
          />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#bp-grid-major)" />
    </svg>
  );
}
