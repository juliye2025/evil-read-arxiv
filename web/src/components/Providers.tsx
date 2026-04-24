"use client";

import { PapersProvider } from "@/components/PapersContext";
import { LanguageProvider } from "@/components/LanguageContext";

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <LanguageProvider>
      <PapersProvider>
        {children}
      </PapersProvider>
    </LanguageProvider>
  );
}
