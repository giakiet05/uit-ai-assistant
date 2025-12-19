"use client"

import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"

export default function AuthErrorPage() {
  const navigate = useNavigate()
  const [errorMessage, setErrorMessage] = useState<string>("Đã xảy ra lỗi trong quá trình đăng nhập")

  useEffect(() => {
    // Parse error message from URL hash
    const hash = window.location.hash.substring(1) // Remove #
    const params = new URLSearchParams(hash.split("?")[1] || "")
    const message = params.get("message")

    if (message) {
      // Decode the error message
      const decodedMessage = decodeURIComponent(message)

      // Map error codes to user-friendly messages
      const errorMessages: { [key: string]: string } = {
        missing_auth_code: "Không nhận được mã xác thực từ Google",
        invalid_credentials: "Thông tin xác thực không hợp lệ",
        email_exists: "Email này đã được sử dụng với phương thức đăng nhập khác",
        login_method_mismatch: "Email này đã được đăng ký bằng phương thức khác. Vui lòng sử dụng cùng phương thức đăng nhập.",
        user_inactive: "Tài khoản của bạn đã bị vô hiệu hóa",
        unknown_error: "Đã xảy ra lỗi không xác định",
      }

      setErrorMessage(errorMessages[decodedMessage] || decodedMessage)
    }

    // Auto redirect after 5 seconds
    const timer = setTimeout(() => {
      navigate("/login", { replace: true })
    }, 5000)

    return () => clearTimeout(timer)
  }, [navigate])

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,var(--border)_1px,transparent_1px),linear-gradient(to_bottom,var(--border)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black_100%)] opacity-30"></div>
      </div>

      <div className="max-w-md w-full relative z-10">
        <div className="bg-card border border-destructive/50 rounded-xl shadow-lg p-8 space-y-6">
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

            <div className="space-y-2">
              <h2 className="text-xl font-semibold text-foreground">Đăng nhập thất bại</h2>
              <p className="text-sm text-muted-foreground">{errorMessage}</p>
            </div>

            <div className="w-full pt-4 space-y-3">
              <button
                onClick={() => navigate("/login", { replace: true })}
                className="w-full py-2.5 px-4 rounded-lg font-semibold text-primary-foreground bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-1 transform hover:scale-[1.01] active:scale-[0.99] transition-all duration-200"
              >
                Quay lại trang đăng nhập
              </button>

              <p className="text-xs text-muted-foreground text-center">
                Tự động chuyển hướng sau 5 giây...
              </p>
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-muted-foreground mt-6">
          Powered by <span className="font-semibold text-foreground">UIT AI Team</span>
        </p>
      </div>
    </div>
  )
}
