"use client"

import { useState } from "react"
import { apiClient } from "@/lib/api"

const USE_MOCK_AUTH = import.meta.env.VITE_AUTH_MODE === "mock"

export function useLogout() {
  const [isPending, setIsPending] = useState(false)

  const mutate = async () => {
    setIsPending(true)
    try {
      const accessToken = localStorage.getItem("accessToken")
      const refreshToken = localStorage.getItem("refreshToken")

      // Call logout API if not in mock mode and tokens exist
      if (!USE_MOCK_AUTH && accessToken && refreshToken) {
        try {
          await apiClient.logout({
            access_token: accessToken,
            refresh_token: refreshToken,
          })
        } catch (err) {
          // Log error but continue with logout
          console.error("Logout API error:", err)
        }
      }

      // Clear local storage
      localStorage.removeItem("user")
      localStorage.removeItem("accessToken")
      localStorage.removeItem("refreshToken")

      // Redirect to login
      window.location.href = "/login"
    } catch (err) {
      console.error("Logout error:", err)
      // Clear storage and redirect anyway
      localStorage.removeItem("user")
      localStorage.removeItem("accessToken")
      localStorage.removeItem("refreshToken")
      window.location.href = "/login"
    } finally {
      setIsPending(false)
    }
  }

  return {
    mutate,
    isPending,
  }
}
