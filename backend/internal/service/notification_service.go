package service

import (
	"log"

	"github.com/giakiet05/uit-ai-assistant/backend/internal/dto"
	"github.com/giakiet05/uit-ai-assistant/backend/internal/platform/bus"
	"github.com/giakiet05/uit-ai-assistant/backend/internal/repo"
	"github.com/giakiet05/uit-ai-assistant/backend/internal/util"
	"github.com/redis/go-redis/v9"
)

type NotificationService interface {
	Start()
	GetNotifications(recipientID string, page, pageSize int) (*dto.PaginatedNotificationsResponse, error)
	MarkAllAsRead(recipientID string) (int64, error)
}

type notificationService struct {
	notificationRepo repo.NotificationRepo
	userRepo         repo.UserRepo
	eventBus         bus.EventBus
	redisClient      *redis.Client
}

func NewNotificationService(
	notificationRepo repo.NotificationRepo,
	userRepo repo.UserRepo,
	bus bus.EventBus,
	redis *redis.Client,
) NotificationService {
	return &notificationService{
		notificationRepo: notificationRepo,
		userRepo:         userRepo,
		eventBus:         bus,
		redisClient:      redis,
	}
}

func (s *notificationService) Start() {
	eventChannel := make(bus.EventListener, 100)

	s.eventBus.Subscribe(bus.TopicBroadcast, eventChannel)

	log.Println("NotificationService started and subscribed to events.")

	go s.processEvents(eventChannel)
}

func (s *notificationService) processEvents(ch bus.EventListener) {
	for event := range ch {
		switch event.Topic() {
		case bus.TopicBroadcast:
			s.handleBroadcast(event)
		}
	}
}

func (s *notificationService) GetNotifications(recipientID string, page, pageSize int) (*dto.PaginatedNotificationsResponse, error) {
	ctx, cancel := util.NewDefaultDBContext()
	defer cancel()

	notifications, total, err := s.notificationRepo.GetByRecipientID(ctx, recipientID, page, pageSize)
	if err != nil {
		return nil, err
	}

	return &dto.PaginatedNotificationsResponse{
		Notifications: dto.FromNotifications(notifications),
		Pagination: dto.Pagination{
			Total: total,
			Page:  page,
		},
	}, nil
}

func (s *notificationService) MarkAllAsRead(recipientID string) (int64, error) {
	ctx, cancel := util.NewDefaultDBContext()
	defer cancel()

	return s.notificationRepo.MarkAllAsRead(ctx, recipientID)
}

func (s *notificationService) handleBroadcast(event bus.Event) {
	panic("not implemented")
}
