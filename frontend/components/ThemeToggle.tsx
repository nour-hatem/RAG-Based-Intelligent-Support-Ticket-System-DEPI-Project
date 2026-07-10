"use client";

import { Button } from "@heroui/react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "@heroui/react";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme("light");
  const isDark = theme === "dark";

  return (
    <Button
      variant="ghost"
      size="sm"
      isIconOnly
      onPress={() => setTheme(isDark ? "light" : "dark")}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className="text-blue-500 hover:text-blue-600"
    >
      {isDark ? <Moon size={17} /> : <Sun size={17} />}
    </Button>
  );
}
