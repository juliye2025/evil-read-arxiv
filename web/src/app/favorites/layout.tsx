"use client";

import { FavoritesProvider } from "@/components/FavoritesContext";

export default function FavoritesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <FavoritesProvider>{children}</FavoritesProvider>;
}
