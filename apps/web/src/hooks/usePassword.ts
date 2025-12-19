import { useState } from "react"
import { apiClient } from "@/lib/api"
import type { ChangePasswordRequest } from "@/lib/api"
import { toast } from "sonner"

export function useChangePassword() {
  const [loading, setLoading] = useState(false)

  const changePassword = async (data: ChangePasswordRequest) => {
    try {
      setLoading(true)
      const response = await apiClient.changePassword(data)

      if (response.success) {
        toast.success("Password changed successfully")
        return true
      }

      toast.error(response.message || "Failed to change password")
      return false
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to change password"
      toast.error(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }

  return {
    changePassword,
    loading,
  }
}
