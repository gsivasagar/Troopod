import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Troopod Ad-to-LP Harmonizer | AI Landing Page Personalization",
  description:
    "Personalize landing pages to match your ad creatives using AI. Upload an ad, enter a landing page URL, and get CRO-optimized copy in seconds.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
