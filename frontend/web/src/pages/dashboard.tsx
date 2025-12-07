"use client"

import { useNavigate } from "react-router-dom"
import { useLogout } from "@/hooks/useLogout"
import { Button } from "@/components/ui/button"

export default function DashboardPage() {
  const navigate = useNavigate()
  const { mutate: logout, isPending } = useLogout()

  const handleLogout = async () => {
    await logout()
    navigate("/login")
  }

  const user = JSON.parse(localStorage.getItem("user") || "{}")

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
          <Button onClick={handleLogout} disabled={isPending} variant="destructive">
            {isPending ? "Logging out..." : "Logout"}
          </Button>
        </div>

        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-xl font-semibold text-foreground mb-4">Welcome back!</h2>
          <p className="text-muted-foreground">
            Username: <span className="font-semibold text-foreground">{user.username}</span>
          </p>
        </div>
      </div>
    </div>
  )
}
