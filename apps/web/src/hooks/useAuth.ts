"use client"

import { useState } from "react"
import { apiClient } from "@/lib/api"

interface LoginCredentials {
  username: string
  password: string
}

// Đọc từ environment variable để xác định auth mode
const USE_MOCK_AUTH = import.meta.env.VITE_AUTH_MODE === "mock"

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
            full_name: "Test User",
          }
          localStorage.setItem("user", JSON.stringify(mockUser))
          localStorage.setItem("accessToken", "mock-jwt-token")
          localStorage.setItem("refreshToken", "mock-refresh-token")
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
      const response = await apiClient.login({
        identifier: credentials.username,
        password: credentials.password,
      })

      if (response.success && response.data) {
        // Lưu user info và tokens vào localStorage
        localStorage.setItem("user", JSON.stringify(response.data.user))
        localStorage.setItem("accessToken", response.data.access_token)
        localStorage.setItem("refreshToken", response.data.refresh_token)

        // Successfully logged in
        setIsPending(false)
        window.location.href = "/chat"
      } else {
        setIsError(true)
        setError(response.message || "Đăng nhập thất bại")
        setIsPending(false)
      }
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
