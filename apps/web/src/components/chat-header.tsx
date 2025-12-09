"use client"

import ThemeToggle from "./theme-toggle"
import { UserMenu } from "./user-menu"
import { useUserProfile } from "@/hooks/useUserProfile"

interface ChatHeaderProps {
  conversationTitle: string
}

export default function ChatHeader({ conversationTitle }: ChatHeaderProps) {
  const { user } = useUserProfile()

  return (
    <div className="border-b border-border bg-card">
      <div className="px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-semibold text-foreground">{conversationTitle}</h1>
        </div>

        <div className="flex items-center gap-3">
          {/* Theme Toggle */}
          <ThemeToggle />

          {/* User Menu */}
          {user && (
            <UserMenu
              username={user.username || user.name}
              email={user.email}
              avatarUrl={user.avatar?.url || user.avatar_url}
            />
          )}
        </div>
      </div>
    </div>
  )
}
