'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useLoading } from '@/contexts/LoadingContext'

export function NavigationLink({ href, children, className, onClick, ...props }) {
  const router = useRouter()
  const { startLoading, stopLoading } = useLoading()

  const handleClick = async (e) => {
    if (onClick) {
      onClick(e)
    }
    
    // Only show loading for different routes
    if (href && window.location.pathname !== href) {
      startLoading()
      
      // Use router.push for programmatic navigation
      e.preventDefault()
      
      try {
        await router.push(href)
      } finally {
        // Stop loading after a short delay to ensure page has rendered
        setTimeout(() => {
          stopLoading()
        }, 100)
      }
    }
  }

  return (
    <Link href={href} className={className} onClick={handleClick} {...props}>
      {children}
    </Link>
  )
}