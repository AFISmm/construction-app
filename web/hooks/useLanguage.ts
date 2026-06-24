"use client";
import { useState, useEffect } from "react";
import { getLang, Lang, STORAGE_KEY } from "@/lib/lang";

export function useLanguage(): Lang {
  const [lang, setLangState] = useState<Lang>("en");

  useEffect(() => {
    setLangState(getLang());
    function onStorage(e: StorageEvent) {
      if (e.key === STORAGE_KEY) setLangState((e.newValue as Lang) ?? "en");
    }
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  return lang;
}
