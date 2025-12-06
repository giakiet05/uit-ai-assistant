package ws

import (
	"bytes"
	"encoding/json"
	"log"

	"github.com/giakiet05/uit-ai-assistant/internal/dto"
	"github.com/giakiet05/uit-ai-assistant/internal/platform/bus"
)

// Hub maintains the set of active clients and broadcasts messages to them.
type Hub struct {
	userClients map[string]*Client
	register    chan *Client
	unregister  chan *Client
	incoming    chan []byte
	eventBus    bus.EventBus
}

func NewHub(bus bus.EventBus) *Hub {
	return &Hub{
		incoming:    make(chan []byte),
		register:    make(chan *Client),
		unregister:  make(chan *Client),
		userClients: make(map[string]*Client),
		eventBus:    bus,
	}
}

// Start runs the hub's event loop and subscribes to the event eventBus.
func (h *Hub) Start() {
	eventChannel := make(bus.EventListener, 100)
	h.eventBus.Subscribe(bus.TopicNotificationCreated, eventChannel)
	h.eventBus.Subscribe(bus.TopicBroadcast, eventChannel)

	log.Println("WebSocket Hub started and subscribed to events.")

	go h.run(eventChannel)
}

// RegisterClient sends a client to the register channel.
func (h *Hub) RegisterClient(client *Client) {
	h.register <- client
}

func (h *Hub) run(eventChannel bus.EventListener) {
	for {
		select {
		case client := <-h.register:
			h.userClients[client.UserID] = client
			log.Printf("WebSocket client registered: %s", client.UserID)
		case client := <-h.unregister:
			if _, ok := h.userClients[client.UserID]; ok {
				delete(h.userClients, client.UserID)
				close(client.send)
				log.Printf("WebSocket client unregistered: %s", client.UserID)
			}
		case data := <-h.incoming:
			//Handle message receive from client
			parts := bytes.SplitN(data, []byte("|"), 2)
			if len(parts) != 2 {
				log.Println("Invalid incoming message format")
				continue
			}

			userID := string(parts[0])
			message := parts[1]
			h.handleIncoming(message, userID)
		case event := <-eventChannel:
			//Handle event
			switch event.Topic() {
			case bus.TopicNotificationCreated:
				payload := event.Payload()
				if recipientID, ok := payload["recipientId"].(string); ok {
					if notification, ok := payload["notification"].(interface{}); ok {
						h.sendToUser(recipientID, dto.NewNotification, notification)
					}
				}
			case bus.TopicBroadcast:
				payload := event.Payload()
				recipientIDs, _ := payload["recipient_ids"].([]string)
				data := payload["data"]

				h.broadcastToUsers(recipientIDs, dto.NewNotification, data)
			default:
				log.Printf("WebSocket client received unknown event: %s", event.Topic())
			}
		}
	}
}

// sendToUser is a private method to send a message to a specific user.
func (h *Hub) sendToUser(userID string, messageType dto.WebSocketMessageType, payload interface{}) {
	if client, ok := h.userClients[userID]; ok {
		msg := dto.WebSocketMessage{
			Type:    messageType,
			Payload: payload,
		}
		jsonMsg, err := json.Marshal(msg)
		if err != nil {
			log.Printf("Error marshalling websocket message: %v", err)
			return
		}

		select {
		case client.send <- jsonMsg:
		default:
			log.Printf("Warning: Client %s channel is full. Message dropped.", userID)
		}
	}
}

func (h *Hub) broadcastToUsers(userIDs []string, messageType dto.WebSocketMessageType, payload interface{}) {
	msg := dto.WebSocketMessage{
		Type:    messageType,
		Payload: payload,
	}

	jsonMsg, err := json.Marshal(msg)
	if err != nil {
		log.Printf("Error marshalling websocket broadcast message: %v", err)
		return
	}

	for _, userID := range userIDs {
		if client, ok := h.userClients[userID]; ok {
			select {
			case client.send <- jsonMsg:
			default:
				log.Printf("Warning: Client %s channel is full. Broadcast message dropped.", userID)
			}
		}
	}
}

func (h *Hub) handleIncoming(message []byte, id string) {
	panic("not implementedF")
}
