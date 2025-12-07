import { useState } from "react"
import { apiClient } from "@/lib/api"
import type { ChangePasswordRequest } from "@/lib/api"
import { toast } from "sonner"

export function useChangePassword() {
  const [loading, setLoading] = useState(false)

  const changePassword = async (data: ChangePasswordRequest) => {
    console.log("🔐 Change password called with:", { ...data, old_password: "***", new_password: "***" })

    try {
      setLoading(true)
      console.log("📡 Calling API...")
      const response = await apiClient.changePassword(data)
      console.log("✅ API response:", response)

      if (response.success) {
        toast.success("Password changed successfully")
        return true
      }

      toast.error(response.message || "Failed to change password")
      return false
    } catch (err) {
      console.error("❌ Change password error:", err)
      const errorMessage = err instanceof Error ? err.message : "Failed to change password"
      toast.error(errorMessage)
      throw err
    } finally {
      setLoading(false)
      console.log("🏁 Change password completed")
    }
  }

  return {
    changePassword,
    loading,
  }
}
