import { useState } from "react";

export function useTheme() {
  const colorSchemeQueryList = window.matchMedia('(prefers-color-scheme: dark)');
  const [isDarkTheme, setIsDarkTheme] = useState(colorSchemeQueryList.matches);
  colorSchemeQueryList.addEventListener('change', (event) => {
    setIsDarkTheme(event.matches);
  });

  return { 
    isDarkTheme,
  }
}
