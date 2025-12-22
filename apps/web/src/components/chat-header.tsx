"use client"

import { Menu } from "lucide-react"
import { UserMenu } from "./user-menu"
import { useUserProfile } from "@/hooks/useUserProfile"

interface ChatHeaderProps {
  conversationTitle: string
  onToggleSidebar?: () => void
}

export default function ChatHeader({ conversationTitle, onToggleSidebar }: ChatHeaderProps) {
  const { user } = useUserProfile()

  return (
    <div className="border-b border-border bg-card">
      <div className="px-4 md:px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Hamburger Menu Button - Only visible on mobile */}
          {onToggleSidebar && (
            <button
              onClick={onToggleSidebar}
              className="lg:hidden p-2 hover:bg-muted rounded-lg transition-colors"
              aria-label="Toggle sidebar"
            >
              <Menu className="w-5 h-5 text-foreground" />
            </button>
          )}
          <h1 className="text-lg md:text-xl font-semibold text-foreground truncate">{conversationTitle}</h1>
        </div>

        <div className="flex items-center gap-3">
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
