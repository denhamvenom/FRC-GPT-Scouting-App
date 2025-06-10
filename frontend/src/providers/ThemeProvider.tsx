import React, { createContext, useContext, useEffect, ReactNode } from 'react';
import { useLocalStorage } from '../hooks/useLocalStorage';

// Types for theme management
export type Theme = 'light' | 'dark' | 'system';
export type ResolvedTheme = 'light' | 'dark';

export interface ThemeState {
  theme: Theme;
  resolvedTheme: ResolvedTheme;
  systemTheme: ResolvedTheme;
}

export interface ThemeContextType {
  // Current theme state
  theme: Theme;
  resolvedTheme: ResolvedTheme;
  systemTheme: ResolvedTheme;
  
  // Theme actions
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
  
  // Utilities
  isDark: boolean;
  isLight: boolean;
  isSystemTheme: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// Provider component
export interface ThemeProviderProps {
  children: ReactNode;
  defaultTheme?: Theme;
  enableSystem?: boolean;
  storageKey?: string;
}

export function ThemeProvider({ 
  children, 
  defaultTheme = 'system',
  enableSystem = true,
  storageKey = 'theme'
}: ThemeProviderProps) {
  // Detect system theme
  const getSystemTheme = (): ResolvedTheme => {
    if (typeof window === 'undefined') return 'light';
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  };
  
  const [systemTheme, setSystemTheme] = React.useState<ResolvedTheme>(getSystemTheme);
  const [theme, setStoredTheme] = useLocalStorage<Theme>(storageKey, defaultTheme);
  
  // Listen for system theme changes
  useEffect(() => {
    if (!enableSystem) return;
    
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      setSystemTheme(e.matches ? 'dark' : 'light');
    };
    
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [enableSystem]);
  
  // Resolve the actual theme to use
  const resolvedTheme: ResolvedTheme = React.useMemo(() => {
    if (theme === 'system') {
      return systemTheme;
    }
    return theme as ResolvedTheme;
  }, [theme, systemTheme]);
  
  // Apply theme to document
  useEffect(() => {
    const root = window.document.documentElement;
    
    // Remove previous theme classes
    root.classList.remove('light', 'dark');
    
    // Add current theme class
    root.classList.add(resolvedTheme);
    
    // Set CSS custom properties for theme
    if (resolvedTheme === 'dark') {
      root.style.setProperty('--color-scheme', 'dark');
    } else {
      root.style.setProperty('--color-scheme', 'light');
    }
    
    // Update meta theme-color for mobile browsers
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      metaThemeColor.setAttribute(
        'content',
        resolvedTheme === 'dark' ? '#1f2937' : '#ffffff'
      );
    }
  }, [resolvedTheme]);
  
  // Theme management functions
  const setTheme = React.useCallback((newTheme: Theme) => {
    setStoredTheme(newTheme);
  }, [setStoredTheme]);
  
  const toggleTheme = React.useCallback(() => {
    if (theme === 'system') {
      // If currently system, toggle to opposite of system theme
      setTheme(systemTheme === 'dark' ? 'light' : 'dark');
    } else if (theme === 'light') {
      setTheme('dark');
    } else {
      setTheme('light');
    }
  }, [theme, systemTheme, setTheme]);
  
  // Utility values
  const isDark = resolvedTheme === 'dark';
  const isLight = resolvedTheme === 'light';
  const isSystemTheme = theme === 'system';
  
  const contextValue: ThemeContextType = {
    theme,
    resolvedTheme,
    systemTheme,
    setTheme,
    toggleTheme,
    isDark,
    isLight,
    isSystemTheme,
  };
  
  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
}

// Hook to use the ThemeContext
export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

// Additional utility hooks
export function useThemeClass(lightClass: string, darkClass: string): string {
  const { isDark } = useTheme();
  return isDark ? darkClass : lightClass;
}

export function useThemeValue<T>(lightValue: T, darkValue: T): T {
  const { isDark } = useTheme();
  return isDark ? darkValue : lightValue;
}

// CSS-in-JS style helpers
export function useThemeStyles() {
  const { isDark, resolvedTheme } = useTheme();
  
  return {
    isDark,
    theme: resolvedTheme,
    bg: isDark ? 'bg-gray-900' : 'bg-white',
    text: isDark ? 'text-white' : 'text-gray-900',
    border: isDark ? 'border-gray-700' : 'border-gray-200',
    card: isDark ? 'bg-gray-800' : 'bg-white',
    input: isDark ? 'bg-gray-700 text-white' : 'bg-white text-gray-900',
    button: {
      primary: isDark 
        ? 'bg-blue-600 hover:bg-blue-700 text-white' 
        : 'bg-blue-600 hover:bg-blue-700 text-white',
      secondary: isDark 
        ? 'bg-gray-700 hover:bg-gray-600 text-white' 
        : 'bg-gray-200 hover:bg-gray-300 text-gray-900',
      danger: isDark 
        ? 'bg-red-600 hover:bg-red-700 text-white' 
        : 'bg-red-600 hover:bg-red-700 text-white',
    },
  };
}

// Theme transition component
export interface ThemeTransitionProps {
  children: ReactNode;
  className?: string;
}

export function ThemeTransition({ children, className = '' }: ThemeTransitionProps) {
  return (
    <div 
      className={`transition-colors duration-200 ease-in-out ${className}`}
    >
      {children}
    </div>
  );
}