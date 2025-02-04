'use client'

import { useTheme } from 'next-themes'
import { useEffect } from 'react'

export function ThemeColor() {
  const { theme } = useTheme()

  useEffect(() => {
    const metaThemeColor = document.querySelector('meta[name="theme-color"]')
    
    if (!metaThemeColor) return
    
    if (theme === 'dark') {
      metaThemeColor.setAttribute('content', 'hsl(0, 0%, 3.9%)')
    } else {
      metaThemeColor.setAttribute('content', 'hsl(0, 0%, 100%)')
    }
  }, [theme])

  return null
}
