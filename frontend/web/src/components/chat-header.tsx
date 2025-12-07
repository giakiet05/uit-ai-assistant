"use client"

import { LogOut, User } from "lucide-react"
import { useLogout } from "@/hooks/useLogout"
import { useState, useEffect } from "react"
import ThemeToggle from "./theme-toggle"

interface ChatHeaderProps {
  conversationTitle: string
}

export default function ChatHeader({ conversationTitle }: ChatHeaderProps) {
  const logout = useLogout()
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    const userStr = localStorage.getItem("user")
    if (userStr) {
      try {
        setUser(JSON.parse(userStr))
      } catch (e) {
        console.error("Failed to parse user data:", e)
      }
    }
  }, [])

  const handleLogout = () => {
    if (confirm("Bạn có chắc muốn đăng xuất?")) {
      logout.mutate()
    }
  }

  return (
    <div className="border-b border-border bg-card">
      <div className="px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-semibold text-foreground">{conversationTitle}</h1>
        </div>

        <div className="flex items-center gap-3">
          {/* Theme Toggle */}
          <ThemeToggle />

          {/* User Info */}
          {user && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-muted rounded-lg">
              <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center">
                <User size={16} className="text-primary" />
              </div>
              <span className="text-sm font-medium text-foreground">{user.username || user.name}</span>
            </div>
          )}

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            disabled={logout.isPending}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-destructive hover:bg-destructive/10 rounded-lg transition-colors disabled:opacity-50"
          >
            <LogOut size={16} />
            <span>Đăng xuất</span>
          </button>
        </div>
      </div>
    </div>
  )
}
