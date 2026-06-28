import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Spice — autonomous hedging desk",
  description: "The Exotic Asset Company",
  icons: { icon: "/pepperLogo.png" },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        {/* Satoshi + Spline Sans Mono — DESIGN.md typefaces (Fontshare) */}
        <link
          href="https://api.fontshare.com/v2/css?f[]=satoshi@300,400,500,600,700&f[]=spline-sans-mono@300,400,500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
