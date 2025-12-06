package dto

import (
	"time"

	"github.com/giakiet05/uit-ai-assistant/internal/model"
)

// --- Request DTOs ---

// CreateChatSessionRequest for creating a new chat session
type CreateChatSessionRequest struct {
	Title *string `json:"title" binding:"omitempty,max=100"` // Optional, auto-gen from first message if nil
}

// SendMessageRequest for sending a message in a chat session
type SendMessageRequest struct {
	Message string `json:"message" binding:"required,min=1,max=5000"`
}

// UpdateSessionTitleRequest for updating session title
type UpdateSessionTitleRequest struct {
	Title string `json:"title" binding:"required,min=1,max=100"`
}

// GetSessionsQuery for querying chat sessions with pagination
type GetSessionsQuery struct {
	Page     int `form:"page" binding:"omitempty,min=1"`
	PageSize int `form:"page_size" binding:"omitempty,min=1,max=100"`
}

// GetMessagesQuery for querying messages with pagination
type GetMessagesQuery struct {
	Limit int `form:"limit" binding:"omitempty,min=1,max=100"` // Last N messages
}

// --- Response DTOs ---

// ChatSessionResponse represents a chat session
type ChatSessionResponse struct {
	ID        string    `json:"id"`
	Title     string    `json:"title"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

// ChatMessageResponse represents a single chat message
type ChatMessageResponse struct {
	ID        string       `json:"id"`
	Role      string       `json:"role"` // "user" | "assistant"
	Content   string       `json:"content"`
	Sources   []SourceInfo `json:"sources,omitempty"` // Only for assistant messages
	CreatedAt time.Time    `json:"created_at"`
}

// SourceInfo represents a RAG source citation
type SourceInfo struct {
	Title   string `json:"title"`
	URL     string `json:"url,omitempty"`
	Snippet string `json:"snippet,omitempty"` // Truncated content
}

// PaginatedSessionsResponse for paginated session list
type PaginatedSessionsResponse struct {
	Sessions   []ChatSessionResponse `json:"sessions"`
	Pagination Pagination            `json:"pagination"`
}

// PaginatedMessagesResponse for paginated message list
type PaginatedMessagesResponse struct {
	Messages []ChatMessageResponse `json:"messages"`
}

// --- Converter Functions ---

// FromChatSession converts model.ChatSession to ChatSessionResponse
func FromChatSession(s *model.ChatSession) *ChatSessionResponse {
	if s == nil {
		return nil
	}

	return &ChatSessionResponse{
		ID:        s.ID.Hex(),
		Title:     s.Title,
		CreatedAt: s.CreatedAt,
		UpdatedAt: s.UpdatedAt,
	}
}

// FromChatSessions converts multiple sessions to response DTOs
func FromChatSessions(sessions []*model.ChatSession) []ChatSessionResponse {
	responses := make([]ChatSessionResponse, len(sessions))
	for i, s := range sessions {
		resp := FromChatSession(s)
		if resp != nil {
			responses[i] = *resp
		}
	}
	return responses
}

// FromChatMessage converts model.ChatMessage to ChatMessageResponse
func FromChatMessage(m *model.ChatMessage) *ChatMessageResponse {
	if m == nil {
		return nil
	}

	resp := &ChatMessageResponse{
		ID:        m.ID.Hex(),
		Role:      string(m.Role),
		Content:   m.Content,
		CreatedAt: m.CreatedAt,
	}

	// Extract sources from metadata (only for assistant messages)
	if m.Role == model.RoleAssistant && m.Metadata != nil {
		if sources, ok := m.Metadata["sources"].([]interface{}); ok {
			resp.Sources = extractSources(sources)
		}
	}

	return resp
}

// FromChatMessages converts multiple messages to response DTOs
func FromChatMessages(messages []*model.ChatMessage) []ChatMessageResponse {
	responses := make([]ChatMessageResponse, len(messages))
	for i, m := range messages {
		resp := FromChatMessage(m)
		if resp != nil {
			responses[i] = *resp
		}
	}
	return responses
}

// extractSources extracts and formats source information from metadata
func extractSources(raw []interface{}) []SourceInfo {
	sources := make([]SourceInfo, 0, len(raw))

	for _, s := range raw {
		if src, ok := s.(map[string]interface{}); ok {
			info := SourceInfo{
				Title: getStringFromMap(src, "title"),
				URL:   getStringFromMap(src, "url"),
			}

			// Truncate snippet to 200 chars
			if content := getStringFromMap(src, "content"); content != "" {
				if len(content) > 200 {
					info.Snippet = content[:200] + "..."
				} else {
					info.Snippet = content
				}
			}

			sources = append(sources, info)
		}
	}

	return sources
}

// getStringFromMap safely extracts a string value from a map
func getStringFromMap(m map[string]interface{}, key string) string {
	if v, ok := m[key].(string); ok {
		return v
	}
	return ""
}

// GenerateSessionTitle generates a title from the first message
func GenerateSessionTitle(firstMessage string) string {
	maxLen := 50

	// Remove leading/trailing whitespace
	title := firstMessage

	// Truncate to maxLen
	if len(title) > maxLen {
		// Try to truncate at word boundary
		title = title[:maxLen]
		if lastSpace := len(title) - 1; lastSpace > 0 {
			for i := len(title) - 1; i >= 0; i-- {
				if title[i] == ' ' {
					title = title[:i]
					break
				}
			}
		}
		title = title + "..."
	}

	return title
}
