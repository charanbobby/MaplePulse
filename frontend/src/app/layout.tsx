import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MaplePulse — Synthetic Focus Group for Canada",
  description:
    "Test marketing messages with AI-powered Canadian personas. Get real-time reactions, cultural feedback, and optimized messaging.",
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/favicon.svg", type: "image/svg+xml" },
      { url: "/favicon-96x96.png", sizes: "96x96", type: "image/png" },
    ],
    apple: "/apple-touch-icon.png",
  },
  manifest: "/site.webmanifest",
  openGraph: {
    title: "MaplePulse — Synthetic Focus Group for Canada",
    description:
      "Test marketing messages with AI-powered Canadian personas. Get real-time reactions, cultural feedback, and optimized messaging.",
    images: [{ url: "/logo-full.png", width: 1408, height: 768 }],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
