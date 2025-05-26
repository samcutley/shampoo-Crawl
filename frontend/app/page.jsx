'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function Home() {
  const router = useRouter()

  useEffect(() => {
    // Redirect to dashboard on home page load
    router.push('/dashboard')
  }, [router])

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          Cybersecurity Intelligence Platform
        </h1>
        <p className="text-gray-600">Redirecting to dashboard...</p>
      </div>
    </div>
  )
}