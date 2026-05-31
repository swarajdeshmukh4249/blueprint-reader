import type { CSSProperties } from "react";

/** Minimal floor-plan schematic for hero / empty states */
export default function FloorPlanSchematic({
  className = "",
  style,
}: {
  className?: string;
  style?: CSSProperties;
}) {
  return (
    <svg
      className={className}
      style={style}
      viewBox="0 0 320 240"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <rect x="20" y="20" width="280" height="200" rx="2" stroke="currentColor" strokeWidth="1.5" opacity="0.9" />
      <line x1="20" y1="120" x2="300" y2="120" stroke="currentColor" strokeWidth="1" opacity="0.4" />
      <line x1="160" y1="20" x2="160" y2="220" stroke="currentColor" strokeWidth="1" opacity="0.4" />
      <rect x="28" y="28" width="120" height="84" stroke="currentColor" strokeWidth="1.2" opacity="0.7" />
      <rect x="168" y="28" width="124" height="84" stroke="currentColor" strokeWidth="1.2" opacity="0.7" />
      <rect x="28" y="128" width="80" height="84" stroke="currentColor" strokeWidth="1.2" opacity="0.7" />
      <rect x="168" y="128" width="124" height="84" stroke="currentColor" strokeWidth="1.2" opacity="0.7" />
      <text x="88" y="78" fill="currentColor" fontSize="10" fontFamily="monospace" opacity="0.5">
        BED
      </text>
      <text x="210" y="78" fill="currentColor" fontSize="10" fontFamily="monospace" opacity="0.5">
        LIVING
      </text>
      <text x="52" y="178" fill="currentColor" fontSize="10" fontFamily="monospace" opacity="0.5">
        KIT
      </text>
      <circle cx="260" cy="170" r="18" stroke="var(--coral, #e8a598)" strokeWidth="1.5" opacity="0.8" />
      <path d="M 248 170 L 272 170 M 260 158 L 260 182" stroke="var(--coral, #e8a598)" strokeWidth="1" opacity="0.6" />
    </svg>
  );
}
