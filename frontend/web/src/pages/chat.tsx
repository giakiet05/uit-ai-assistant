"use client"

import { useState, useEffect } from "react"
import ChatSidebar from "@/components/chat-sidebar"
import ChatWindow from "@/components/chat-window"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
}

const STORAGE_KEY = "uit-ai-conversations"

// Helper function to generate title from first message
function generateTitle(content: string): string {
  const maxLength = 30
  if (content.length <= maxLength) return content
  return content.substring(0, maxLength) + "..."
}

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string>("")
  const [isInitialized, setIsInitialized] = useState(false)

  // Initialize default conversation
  const initializeDefaultConversation = () => {
    const defaultConv: Conversation = {
      id: Date.now().toString(),
      title: "Cuộc trò chuyện mới",
      messages: [],
      createdAt: new Date(),
    }
    setConversations([defaultConv])
    setActiveConversationId(defaultConv.id)
    setIsInitialized(true)
  }

  // Load conversations from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        // Convert date strings back to Date objects
        const conversationsWithDates = parsed.map((conv: any) => ({
          ...conv,
          createdAt: new Date(conv.createdAt),
          messages: conv.messages.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
          })),
        }))
        setConversations(conversationsWithDates)
        if (conversationsWithDates.length > 0) {
          setActiveConversationId(conversationsWithDates[0].id)
        }
        setIsInitialized(true)
      } catch (e) {
        console.error("Failed to load conversations:", e)
        initializeDefaultConversation()
      }
    } else {
      initializeDefaultConversation()
    }
  }, [])

  // Save conversations to localStorage whenever they change (but not on initial load)
  useEffect(() => {
    if (isInitialized && conversations.length > 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations))
    }
  }, [conversations, isInitialized])

  const activeConversation = conversations.find((c) => c.id === activeConversationId)

  const handleSendMessage = async (content: string) => {
    console.log("📤 handleSendMessage called with:", content)
    console.log("Current activeConversationId:", activeConversationId)
    console.log("Current conversations:", conversations)

    if (!activeConversationId) {
      console.error("❌ No active conversation ID!")
      return
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
      timestamp: new Date(),
    }

    console.log("📝 Created user message:", userMessage)

    // Update conversation with user message
    setConversations((prev) => {
      console.log("Previous conversations:", prev)
      const updated = prev.map((conv) => {
        if (conv.id === activeConversationId) {
          const updatedMessages = [...conv.messages, userMessage]
          // Auto-generate title from first user message
          const newTitle = conv.messages.length === 0 ? generateTitle(content) : conv.title
          console.log("✅ Updated conversation:", {
            ...conv,
            title: newTitle,
            messages: updatedMessages,
          })
          return {
            ...conv,
            title: newTitle,
            messages: updatedMessages,
          }
        }
        return conv
      })
      console.log("New conversations state:", updated)
      return updated
    })

    // Simulate AI response (replace with real API call)
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Đây là câu trả lời mô phỏng cho: "${content}"\n\nĐể kết nối với AI thật, bạn cần:\n1. Cấu hình VITE_API_URL trong .env\n2. Implement API endpoint /api/chat\n3. Update hàm handleSendMessage để gọi API thật`,
        timestamp: new Date(),
      }

      console.log("🤖 Adding AI response:", assistantMessage)

      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === activeConversationId
            ? { ...conv, messages: [...conv.messages, assistantMessage] }
            : conv,
        ),
      )
    }, 1500)
  }

  const handleNewConversation = () => {
    const newConversation: Conversation = {
      id: Date.now().toString(),
      title: "Cuộc trò chuyện mới",
      messages: [],
      createdAt: new Date(),
    }
    setConversations((prev) => [newConversation, ...prev])
    setActiveConversationId(newConversation.id)
  }

  const handleSelectConversation = (id: string) => {
    setActiveConversationId(id)
  }

  const handleDeleteConversation = (id: string) => {
    if (conversations.length === 1) {
      // Don't delete if it's the last conversation, just clear it
      setConversations([
        {
          id: Date.now().toString(),
          title: "Cuộc trò chuyện mới",
          messages: [],
          createdAt: new Date(),
        },
      ])
      return
    }

    setConversations((prev) => {
      const filtered = prev.filter((c) => c.id !== id)
      // If deleting active conversation, switch to the first one
      if (id === activeConversationId && filtered.length > 0) {
        setActiveConversationId(filtered[0].id)
      }
      return filtered
    })
  }

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <ChatSidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
      />
      <ChatWindow
        messages={activeConversation?.messages || []}
        conversationTitle={activeConversation?.title || "Chat"}
        onSendMessage={handleSendMessage}
      />
    </div>
  )
}
