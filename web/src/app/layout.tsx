import type { Metadata } from "next";
import "./globals.css";
import NavBar from "@/components/NavBar";
import Providers from "@/components/Providers";

export const metadata: Metadata = {
  title: "evil-read-arxiv",
  description: "Daily arXiv paper recommendations with preference learning",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh" className="dark">
      <body className="h-dvh flex flex-col">
        <Providers>
          <main className="flex-1 min-h-0 overflow-hidden">{children}</main>
          <NavBar />
        </Providers>
      </body>
    </html>
  );
}
