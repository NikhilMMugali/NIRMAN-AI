import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NIRMAN AI",
  description: "National Infrastructure Risk & Monitoring Intelligence Network",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
