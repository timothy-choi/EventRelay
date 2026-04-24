import type { Metadata } from "next";
import { Nav } from "../components/Nav";
import "./globals.css";

export const metadata: Metadata = {
  title: "EventRelay Dashboard",
  description: "Minimal dashboard for endpoints, deliveries, and reliability stats.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <div className="shell">
          <Nav />
          {children}
        </div>
      </body>
    </html>
  );
}
