package dto

type WebSocketMessageType string

const (
	NewNotification WebSocketMessageType = "new_notification"
	ACKMessage      WebSocketMessageType = "ack_message"
	NewMessage      WebSocketMessageType = "new_message"
	SendMessage     WebSocketMessageType = "send_message"
	TypingIndicator WebSocketMessageType = "typing"
	InChatIndicator WebSocketMessageType = "in_chat"
	ErrorMessage    WebSocketMessageType = "error"
)

type WebSocketMessage struct {
	Type    WebSocketMessageType `json:"type"`
	Payload interface{}          `json:"payload"`
}
type ErrorPayload struct {
	TempMessageID *string `json:"temp_message_id,omitempty"`
	ErrorCode     *string `json:"error_code,omitempty"`
	ErrorMsg      string  `json:"error_msg"`
}

type ChatPresenceKey struct {
	UserID    string
	ChannelID string
}
