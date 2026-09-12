"use client";

import { usePreferencesStore, type ThemePreference } from "@/store/preferences-store";

import { MoonIcon, SunIcon, SystemIcon } from "./icons";
import { IconButton } from "./icon-button";

const next: Record<ThemePreference, ThemePreference> = { system: "light", light: "dark", dark: "system" };

export function ThemeToggle() {
  const theme = usePreferencesStore((state) => state.theme);
  const setTheme = usePreferencesStore((state) => state.setTheme);
  const label = `Thème ${theme}. Changer de thème`;
  return (
    <IconButton label={label} onClick={() => setTheme(next[theme])}>
      {theme === "light" ? <SunIcon /> : theme === "dark" ? <MoonIcon /> : <SystemIcon />}
    </IconButton>
  );
}
