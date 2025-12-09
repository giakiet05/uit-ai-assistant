"use client"

import { Plus, Trash2 } from "lucide-react"
import { useState } from "react"

interface Conversation {
  id: string
  title: string
  createdAt: Date
}

interface ChatSidebarProps {
  conversations: Conversation[]
  activeConversationId: string
  onSelectConversation: (id: string) => void
  onNewConversation: () => void
  onDeleteConversation?: (id: string) => void
}

export default function ChatSidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
}: ChatSidebarProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null)

  return (
    <div className="w-64 bg-card border-r border-border flex flex-col h-screen">
      <div className="p-6 border-b border-border">
        <button
          onClick={() => {
            console.log("New conversation button clicked")
            onNewConversation()
          }}
          className="w-full flex items-center justify-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground font-medium py-2 px-4 rounded-lg transition-colors"
        >
          <Plus size={18} />
          Cuộc trò chuyện mới
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {conversations.map((conversation) => (
          <div
            key={conversation.id}
            onMouseEnter={() => setHoveredId(conversation.id)}
            onMouseLeave={() => setHoveredId(null)}
            onClick={() => onSelectConversation(conversation.id)}
            className={`w-full text-left px-4 py-3 rounded-lg text-sm transition-all cursor-pointer ${
              activeConversationId === conversation.id
                ? "bg-primary/10 text-primary font-medium"
                : "text-foreground hover:bg-muted/50"
            }`}
          >
            <div className="flex items-center justify-between gap-2">
              <div className="truncate flex-1">{conversation.title}</div>
              {hoveredId === conversation.id && onDeleteConversation && (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onDeleteConversation(conversation.id)
                  }}
                  className="p-1 hover:bg-destructive/10 rounded transition-colors flex-shrink-0"
                >
                  <Trash2 size={16} className="text-destructive" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="border-t border-border p-4">
        <p className="text-xs text-muted-foreground px-2">v1.0.0</p>
      </div>
    </div>
  )
}
