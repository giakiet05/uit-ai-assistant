"use client"

import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"

export default function GoogleSetupPage() {
  const navigate = useNavigate()
  const [username, setUsername] = useState("")
  const [setupToken, setSetupToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Parse setup_token from URL hash
    const hash = window.location.hash.substring(1) // Remove #
    const params = new URLSearchParams(hash.split("?")[1] || "")
    const token = params.get("setup_token")

    if (!token) {
      setError("Không tìm thấy thông tin thiết lập. Vui lòng thử lại.")
      setTimeout(() => {
        navigate("/login", { replace: true })
      }, 3000)
    } else {
      setSetupToken(token)
    }
  }, [navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)

    try {
      const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080"
      const response = await fetch(`${API_URL}/api/auth/google/complete-setup`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          setup_token: setupToken,
          username: username,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        setError(data.message || "Có lỗi xảy ra. Vui lòng thử lại.")
        setIsLoading(false)
        return
      }

      // Save tokens
      if (data.data?.access_token && data.data?.refresh_token) {
        localStorage.setItem("access_token", data.data.access_token)
        localStorage.setItem("refresh_token", data.data.refresh_token)
      }

      // Redirect to chat
      navigate("/chat", { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : "Có lỗi xảy ra")
      setIsLoading(false)
    }
  }

  if (!setupToken && !error) {
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
            <h2 className="text-xl font-semibold text-foreground">Đang tải...</h2>
          </div>
        </div>
      </div>
    )
  }

  if (error && !setupToken) {
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
            <h2 className="text-xl font-semibold text-foreground">Có lỗi xảy ra</h2>
            <p className="text-sm text-muted-foreground">{error}</p>
            <p className="text-xs text-muted-foreground">Đang chuyển hướng về trang đăng nhập...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 py-8">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,var(--border)_1px,transparent_1px),linear-gradient(to_bottom,var(--border)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black_100%)] opacity-30"></div>
      </div>

      <div className="w-full max-w-md relative z-10">
        <div className="bg-card border border-border rounded-xl shadow-lg p-8 space-y-6">
          <div className="space-y-3 text-center">
            <div className="flex justify-center">
              <div className="w-14 h-14 bg-primary/10 rounded-lg flex items-center justify-center">
                <svg className="w-7 h-7 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                  />
                </svg>
              </div>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">Hoàn tất đăng ký</h1>
              <p className="text-sm text-muted-foreground mt-1">Chọn tên người dùng của bạn</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <label htmlFor="username" className="block text-sm font-semibold text-foreground/90">
                Tên người dùng
              </label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <svg
                    className="h-5 w-5 text-muted-foreground group-focus-within:text-primary transition-colors duration-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                    />
                  </svg>
                </div>
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="block w-full pl-11 pr-4 py-2.5 bg-card border border-border rounded-lg placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-200"
                  placeholder="Nhập tên người dùng"
                  minLength={3}
                  maxLength={30}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                Tên người dùng phải có từ 3-30 ký tự
              </p>
            </div>

            {error && (
              <div className="rounded-lg bg-destructive/5 border border-destructive/20 p-3.5 flex items-start gap-3 animate-in fade-in duration-300">
                <svg
                  className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5"
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
                <p className="text-sm text-destructive/90 font-medium">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 rounded-lg font-semibold text-primary-foreground bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.01] active:scale-[0.99] transition-all duration-200"
            >
              {isLoading ? (
                <div className="flex justify-center items-center gap-2">
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
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
                  <span>Đang xử lý...</span>
                </div>
              ) : (
                <span>Hoàn tất</span>
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-muted-foreground mt-6">
          Powered by <span className="font-semibold text-foreground">UIT AI Team</span>
        </p>
      </div>
    </div>
  )
}
