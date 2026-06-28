"use client";

// Spice logomark — vector, theme-aware (tile = brand green, mark = white).
// Three variants so the brand can be tuned live:
//   "seed"     — two crossed seed/spice shapes (default; the "exotic asset")
//   "spark"    — a 4-point spark (intelligence / the AI)
//   "monogram" — a typographic S (the safe fallback)
// Sizes cleanly from a 16px favicon to a 200px deck lockup.

export type LogoVariant = "seed" | "spark" | "monogram";

export function LogoMark({
  size = 34,
  variant = "seed",
  tile = "var(--green)",
  mark = "var(--panel)",
  rounded = 9,
}: {
  size?: number;
  variant?: LogoVariant;
  tile?: string;
  mark?: string;
  rounded?: number;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      role="img"
      aria-label="Spice"
    >
      <rect width="32" height="32" rx={rounded} style={{ fill: tile }} />
      {variant === "seed" && (
        <g style={{ fill: mark }}>
          <path d="M16 5C18.4 10.8 18.4 21.2 16 27C13.6 21.2 13.6 10.8 16 5Z" />
          <path d="M5 16C10.8 13.6 21.2 13.6 27 16C21.2 18.4 10.8 18.4 5 16Z" />
        </g>
      )}
      {variant === "spark" && (
        <path
          style={{ fill: mark }}
          d="M16 5.5C16.9 12.7 19.3 15.1 26.5 16C19.3 16.9 16.9 19.3 16 26.5C15.1 19.3 12.7 16.9 5.5 16C12.7 15.1 15.1 12.7 16 5.5Z"
        />
      )}
      {variant === "monogram" && (
        <text
          x="16"
          y="22.5"
          textAnchor="middle"
          fontFamily="Satoshi, system-ui, sans-serif"
          fontSize="19"
          fontWeight={600}
          style={{ fill: mark }}
        >
          S
        </text>
      )}
    </svg>
  );
}

// Full horizontal lockup — mark + wordmark + tagline. For splash / about / deck.
export function LogoFull({ size = 34, variant = "seed" }: { size?: number; variant?: LogoVariant }) {
  return (
    <div className="flex items-center gap-3">
      <LogoMark size={size} variant={variant} />
      <div className="flex items-baseline">
        <span className="text-[18px] font-semibold tracking-tight">Spice</span>
        <span className="ml-3 text-[11px] font-normal uppercase tracking-label text-faint">
          The Exotic Asset Company
        </span>
      </div>
    </div>
  );
}
