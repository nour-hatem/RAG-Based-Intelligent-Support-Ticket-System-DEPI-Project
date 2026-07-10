"use client";

import { Button, useTheme } from "@heroui/react";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme("light");

  return (
    <Button
      variant="ghost"
      size="sm"
      onPress={() => setTheme(theme === "dark" ? "light" : "dark")}
      aria-label="Toggle dark mode"
    >
      {theme === "dark" ? "🌙 Dark" : "☀️ Light"}
    </Button>
  );
}
