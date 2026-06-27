import type { Config } from "tailwindcss";

// Tokens mirror DESIGN.md (the design-review source of truth).
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F4F3EF",
        panel: "#FFFFFF",
        hair: "#ECEAE3",
        hair2: "#F2F0EA",
        inkdeep: "#13231D",
        ink: "#1A1916",
        dim: "#797469",
        faint: "#ABA59A",
        green: "#1B5E4C",
        terra: "#A85436",
        greenon: "#5DD3A3", // positive numbers on deep-ink banner
        // commodity series — green → desaturated, never rainbow
        cwheat: "#1B5E4C",
        cenergy: "#5C7A6E",
        cfats: "#94A89E",
        cother: "#F2F0EA",
      },
      fontFamily: {
        sans: ["Satoshi", "system-ui", "sans-serif"],
        mono: ["'Spline Sans Mono'", "ui-monospace", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(40,36,28,.04), 0 12px 32px -12px rgba(40,36,28,.10)",
        board: "0 18px 50px -24px rgba(40,36,28,.25)",
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
