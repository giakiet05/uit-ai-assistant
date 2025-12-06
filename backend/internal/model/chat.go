package model

import (
	"time"

	"go.mongodb.org/mongo-driver/bson/primitive"
)

// ChatSession represents a conversation session
type ChatSession struct {
	ID        primitive.ObjectID `bson:"_id,omitempty" json:"id"`
	UserID    primitive.ObjectID `bson:"user_id" json:"user_id"`
	Title     string             `bson:"title" json:"title"` // Auto-generated or user-set
	CreatedAt time.Time          `bson:"created_at" json:"created_at"`
	UpdatedAt time.Time          `bson:"updated_at" json:"updated_at"`
	DeletedAt *time.Time         `bson:"deleted_at,omitempty" json:"deleted_at,omitempty"` // Soft delete
}

// ChatMessage represents a single message in a chat session
type ChatMessage struct {
	ID        primitive.ObjectID `bson:"_id,omitempty" json:"id"`
	SessionID primitive.ObjectID `bson:"session_id" json:"session_id"`
	Role      MessageRole        `bson:"role" json:"role"`
	Content   string             `bson:"content" json:"content"`
	Metadata  map[string]any     `bson:"metadata,omitempty" json:"metadata,omitempty"` // RAG sources, tool calls, tokens, etc.
	CreatedAt time.Time          `bson:"created_at" json:"created_at"`
}

// MessageRole defines the sender of a message
type MessageRole string

const (
	RoleUser      MessageRole = "user"
	RoleAssistant MessageRole = "assistant"
)

// IsValidRole checks if the role is valid
func IsValidRole(role MessageRole) bool {
	return role == RoleUser || role == RoleAssistant
}

// CloneChatSession creates a deep copy of a chat session
func CloneChatSession(s *ChatSession) *ChatSession {
	if s == nil {
		return nil
	}

	clone := *s

	// Deep copy DeletedAt
	if s.DeletedAt != nil {
		t := *s.DeletedAt
		clone.DeletedAt = &t
	}

	return &clone
}

// CloneChatMessage creates a deep copy of a chat message
func CloneChatMessage(m *ChatMessage) *ChatMessage {
	if m == nil {
		return nil
	}

	clone := *m

	// Deep copy Metadata
	if m.Metadata != nil {
		clone.Metadata = make(map[string]any, len(m.Metadata))
		for k, v := range m.Metadata {
			clone.Metadata[k] = v
		}
	}

	return &clone
}
