import type { ReactNode } from "react"
import { Navigate } from "react-router-dom"

interface ProtectedRouteProps {
  children: ReactNode
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  // Check for user info and access token
  const user = localStorage.getItem("user")
  const accessToken = localStorage.getItem("accessToken")

  if (!user || !accessToken) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
