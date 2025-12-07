"use client"

import { useState } from "react"

interface LoginCredentials {
  username: string
  password: string
}

interface LoginResponse {
  success: boolean
  message?: string
  user?: any
}

// Cấu hình: Đổi USE_MOCK_AUTH = false khi backend API đã sẵn sàng
const USE_MOCK_AUTH = true
const BACKEND_API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

export function useLogin() {
  const [isPending, setIsPending] = useState(false)
  const [isError, setIsError] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const mutate = async (credentials: LoginCredentials) => {
    setIsPending(true)
    setIsError(false)
    setError(null)

    try {
      if (USE_MOCK_AUTH) {
        // Mock authentication cho development
        await new Promise((resolve) => setTimeout(resolve, 800)) // Giả lập network delay

        if (credentials.username === "test" && credentials.password === "test") {
          const mockUser = {
            id: "1",
            username: "test",
            email: "test@uit.edu.vn",
            name: "Test User",
          }
          localStorage.setItem("user", JSON.stringify(mockUser))
          localStorage.setItem("token", "mock-jwt-token")
          setIsPending(false)
          window.location.href = "/chat"
          return
        } else {
          setIsError(true)
          setError("Tên đăng nhập hoặc mật khẩu không đúng")
          setIsPending(false)
          return
        }
      }

      // Real API call
      const response = await fetch(`${BACKEND_API_URL}/api/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(credentials),
      })

      const data: LoginResponse = await response.json()

      if (!response.ok) {
        setIsError(true)
        setError(data.message || "Đăng nhập thất bại")
        setIsPending(false)
        return
      }

      if (data.user) {
        localStorage.setItem("user", JSON.stringify(data.user))
      }

      // Successfully logged in
      setIsPending(false)
      window.location.href = "/chat"
    } catch (err) {
      setIsError(true)
      setError(err instanceof Error ? err.message : "Có lỗi xảy ra")
      setIsPending(false)
    }
  }

  return {
    mutate,
    isPending,
    isError,
    error,
  }
}
