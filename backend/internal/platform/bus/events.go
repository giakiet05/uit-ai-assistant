package bus

import (
	"github.com/giakiet05/uit-ai-assistant/backend/internal/dto"
)

// Event Topics
const (
	TopicBroadcast           = "broadcast"
	TopicNotificationCreated = "notification.created"
)

type BroadcastEventType string

const (
	// ---- Message-related ----
	BroadcastEventMessageCreated BroadcastEventType = "message_created"
	BroadcastEventMessageDeleted BroadcastEventType = "message_deleted"
	BroadcastEventTypingStart    BroadcastEventType = "typing_start"
	BroadcastEventTypingStop     BroadcastEventType = "typing_stop"
	BroadcastEventMessageRead    BroadcastEventType = "message_read"

	// ---- Notification-related ----
	BroadcastEventMessageNotification BroadcastEventType = "message_notification"
)

type BroadcastEvent struct {
	RecipientIDs []string           `json:"recipient_ids"`
	EventType    BroadcastEventType `json:"event_type"`
	TempID       string             `json:"temp_id"`
	Data         interface{}        `json:"data"`
}

func (e BroadcastEvent) Topic() string { return TopicBroadcast }
func (e BroadcastEvent) Payload() map[string]interface{} {
	return map[string]interface{}{
		"recipient_ids": e.RecipientIDs,
		"event_type":    e.EventType,
		"temp_id":       e.TempID,
		"data":          e.Data,
	}
}

// --- Notification Events ---

type NotificationCreatedEvent struct {
	RecipientID  string
	Notification dto.NotificationResponse
}

func (e NotificationCreatedEvent) Topic() string { return TopicNotificationCreated }
func (e NotificationCreatedEvent) Payload() map[string]interface{} {
	return map[string]interface{}{"recipient_id": e.RecipientID, "notification": e.Notification}
}
