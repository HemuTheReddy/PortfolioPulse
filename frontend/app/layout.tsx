import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "Portfolio Pulse — AI-Powered Crypto Portfolio Advisor",
  description: "Portfolio Pulse — Get personalized cryptocurrency portfolio recommendations backed by machine learning and real-time market analysis.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Navbar />
        {children}
      </body>
    </html>
  );
}
