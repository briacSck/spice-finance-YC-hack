import type { Config } from "tailwindcss";

// Tokens mirror DESIGN.md (the design-review source of truth).
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#FFFFFF", // app background — clean white (was warm beige)
        panel: "#FFFFFF", // cards
        hair: "#E6E6E6", // hairline borders — neutral grey (was warm beige)
        hair2: "#F0F0F0", // internal dividers — neutral grey
        inkdeep: "#141414", // climax banner — near-black (was forest-ink)
        ink: "#111111", // primary text — black
        dim: "#6B6B6B", // secondary text — neutral grey
        faint: "#9A9A9A", // labels / captions — neutral grey
        green: "#1B5E4C", // positive / gains / actions / brand
        terra: "#D33A2C", // negative / risk — red (was terracotta)
        greenon: "#5DD3A3", // positive numbers on near-black banner
        // commodity series — green → desaturated, never rainbow
        cwheat: "#1B5E4C",
        cenergy: "#5C7A6E",
        cfats: "#94A89E",
        cother: "#F0F0F0",
      },
      fontFamily: {
        sans: ["Satoshi", "system-ui", "sans-serif"],
        mono: ["'Spline Sans Mono'", "ui-monospace", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(17,17,17,.04), 0 10px 28px -14px rgba(17,17,17,.10)",
        board: "0 18px 50px -24px rgba(17,17,17,.22)",
      },
      letterSpacing: {
        label: ".14em",
      },
      maxWidth: {
        stage: "1280px",
      },
    },
  },
  plugins: [],
};
export default config;
