import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Chess Platoon Command Center",
  description:
    "Psychological warfare chess trainer — FIELD MARSHAL VOSS commanding.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="scanlines font-mono antialiased text-warroom-muted">
        {children}
      </body>
    </html>
  );
}
