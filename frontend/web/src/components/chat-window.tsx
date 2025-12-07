"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Send } from "lucide-react"
import ChatHeader from "./chat-header"
import TypingIndicator from "./typing-indicator"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

interface ChatWindowProps {
  messages: Message[]
  conversationTitle: string
  onSendMessage: (content: string) => void
}

export default function ChatWindow({ messages, conversationTitle, onSendMessage }: ChatWindowProps) {
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    console.log("💬 ChatWindow received messages:", messages)
    console.log("💬 Messages count:", messages.length)
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLoading])

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + "px"
    }
  }

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault()
    if (input.trim() && !isLoading) {
      setIsLoading(true)
      onSendMessage(input)
      setInput("")
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto"
      }
      // Loading will be set to false after AI response is received
      setTimeout(() => setIsLoading(false), 1500)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Ctrl+Enter or Cmd+Enter
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault()
      handleSubmit()
    }
    // Submit on Enter (without Shift)
    else if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="flex-1 flex flex-col bg-background h-screen">
      <ChatHeader conversationTitle={conversationTitle} />

      <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-muted-foreground space-y-4">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-primary/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
            </div>
            <div className="text-center space-y-2">
              <p className="text-lg font-semibold">Bắt đầu cuộc trò chuyện</p>
              <p className="text-sm max-w-md text-muted-foreground">
                Gửi tin nhắn để bắt đầu chat với UIT AI Assistant
              </p>
            </div>
            <div className="mt-4 text-xs text-muted-foreground/70 space-y-1">
              <p>💡 Mẹo: Nhấn <kbd className="px-2 py-0.5 bg-muted rounded text-foreground font-mono">Enter</kbd> để gửi</p>
              <p>💡 Hoặc <kbd className="px-2 py-0.5 bg-muted rounded text-foreground font-mono">Shift + Enter</kbd> để xuống dòng</p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-4 ${message.role === "user" ? "justify-end" : "justify-start"} animate-in fade-in duration-300`}
              >
                {message.role === "assistant" && (
                  <div className="flex gap-3 max-w-3xl">
                    <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M13 10V3L4 14h7v7l9-11h-7z"
                        />
                      </svg>
                    </div>
                    <div className="text-foreground leading-relaxed space-y-2">
                      <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                      <p className="text-xs text-muted-foreground">
                        {message.timestamp.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })}
                      </p>
                    </div>
                  </div>
                )}

                {message.role === "user" && (
                  <div className="max-w-3xl space-y-1">
                    <div className="bg-primary text-primary-foreground rounded-2xl px-4 py-2.5 shadow-sm">
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    </div>
                    <p className="text-xs text-muted-foreground text-right px-2">
                      {message.timestamp.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })}
                    </p>
                  </div>
                )}
              </div>
            ))}
            {isLoading && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      <div className="border-t border-border bg-card/50 backdrop-blur-sm px-4 md:px-8 py-4">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="flex gap-2 md:gap-3 items-end">
            <div className="flex-1 bg-background rounded-2xl px-4 py-2 border border-border focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/20 transition-all shadow-sm">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder="Nhập tin nhắn... (Enter để gửi, Shift+Enter để xuống dòng)"
                disabled={isLoading}
                rows={1}
                className="w-full bg-transparent text-foreground placeholder-muted-foreground focus:outline-none resize-none max-h-32 text-sm py-1"
              />
            </div>
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="w-10 h-10 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground flex items-center justify-center transition-all disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0 shadow-md hover:shadow-lg active:scale-95"
              title="Gửi tin nhắn (Enter)"
            >
              {isLoading ? (
                <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              ) : (
                <Send size={18} />
              )}
            </button>
          </div>
          <p className="text-xs text-muted-foreground mt-2 text-center">
            UIT AI Assistant có thể mắc lỗi. Hãy kiểm tra thông tin quan trọng.
          </p>
        </form>
      </div>
    </div>
  )
}
