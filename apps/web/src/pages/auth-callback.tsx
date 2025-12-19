"use client"

import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"

export default function AuthCallbackPage() {
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Parse tokens from URL hash
    const hash = window.location.hash.substring(1) // Remove #
    const params = new URLSearchParams(hash.split("?")[1] || "")

    const accessToken = params.get("access_token")
    const refreshToken = params.get("refresh_token")

    if (accessToken && refreshToken) {
      // Save tokens to localStorage
      localStorage.setItem("access_token", accessToken)
      localStorage.setItem("refresh_token", refreshToken)

      // Redirect to chat
      navigate("/chat", { replace: true })
    } else {
      setError("Không tìm thấy thông tin đăng nhập. Vui lòng thử lại.")
      setTimeout(() => {
        navigate("/login", { replace: true })
      }, 3000)
    }
  }, [navigate])

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <div className="max-w-md w-full bg-card border border-destructive/50 rounded-xl shadow-lg p-8">
          <div className="flex flex-col items-center text-center space-y-4">
            <div className="w-16 h-16 bg-destructive/10 rounded-full flex items-center justify-center">
              <svg
                className="w-8 h-8 text-destructive"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-foreground">Đăng nhập thất bại</h2>
            <p className="text-sm text-muted-foreground">{error}</p>
            <p className="text-xs text-muted-foreground">Đang chuyển hướng về trang đăng nhập...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="max-w-md w-full bg-card border border-border rounded-xl shadow-lg p-8">
        <div className="flex flex-col items-center text-center space-y-4">
          <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
            <svg className="animate-spin h-8 w-8 text-primary" fill="none" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-foreground">Đang xử lý đăng nhập...</h2>
          <p className="text-sm text-muted-foreground">Vui lòng chờ trong giây lát</p>
        </div>
      </div>
    </div>
  )
}
