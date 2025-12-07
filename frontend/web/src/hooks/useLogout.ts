"use client"

import { useState } from "react"

export function useLogout() {
  const [isPending, setIsPending] = useState(false)

  const mutate = async () => {
    setIsPending(true)
    try {
      // Clear local storage
      localStorage.removeItem("user")
      localStorage.removeItem("token")

      // Có thể gọi API logout nếu cần
      // await fetch("/api/auth/logout", { method: "POST" })

      // Redirect to login
      window.location.href = "/login"
    } catch (err) {
      console.error("Logout error:", err)
      localStorage.removeItem("user")
      localStorage.removeItem("token")
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
