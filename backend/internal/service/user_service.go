package service

import (
	"errors"
	"fmt"
	"time"

	"github.com/giakiet05/uit-ai-assistant/backend/internal/apperror"
	"github.com/giakiet05/uit-ai-assistant/backend/internal/dto"
	"github.com/giakiet05/uit-ai-assistant/backend/internal/model"
	"github.com/giakiet05/uit-ai-assistant/backend/internal/platform/bus"
	"github.com/giakiet05/uit-ai-assistant/backend/internal/repo"
	"github.com/giakiet05/uit-ai-assistant/backend/internal/util"
	"github.com/redis/go-redis/v9"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"golang.org/x/crypto/bcrypt"
)

// UserService handles business logic related to user management.
type UserService interface {
	UpdateUser(userID string, req *dto.UpdateUserRequest) (*dto.UserResponse, error)
	UpdateAvatar(userID string, imageURL string, publicID string) (*dto.UserResponse, error)
	DeleteAvatar(userID string) (*dto.UserResponse, error)
	DeleteUser(id string) error
	ChangePassword(userID, oldPassword, newPassword string) error

	GetUserByID(id string) (*dto.UserResponse, error)
	GetUserByUsername(username string, requesterID string) (*dto.UserResponse, error)
	GetUserByEmail(email string) (*dto.UserResponse, error)
	GetUsers(query *dto.GetUsersQuery) (*dto.PaginatedUsersResponse, error)

	GetSettings(userID string) (*dto.UserSettingsResponse, error)
	UpdateSettings(userID string, req *dto.UpdateSettingsRequest) (*dto.UserSettingsResponse, error)

	CheckUsernameAvailability(username string) (bool, error)
}

type userService struct {
	userRepo    repo.UserRepo
	eventBus    bus.EventBus
	redisClient *redis.Client
}

func NewUserService(userRepo repo.UserRepo, bus bus.EventBus, redisClient *redis.Client) UserService {
	return &userService{
		userRepo:    userRepo,
		eventBus:    bus,
		redisClient: redisClient,
	}
}

func (s *userService) UpdateUser(userID string, req *dto.UpdateUserRequest) (*dto.UserResponse, error) {
	ctx, cancel := util.NewDefaultDBContext()
	defer cancel()

	user, err := s.userRepo.GetByID(ctx, userID)
	if err != nil {
		return nil, err
	}

	// Update username if provided
	if req.Username != "" {
		// Check username availability
		existing, _ := s.userRepo.GetByUsername(ctx, req.Username)
		if existing != nil && existing.ID != user.ID {
			return nil, apperror.ErrUsernameExists
		}
		user.Username = req.Username
	}

	// Update timestamp
	user.UpdatedAt = time.Now()

	// Save
	updatedUser, err := s.userRepo.Update(ctx, user)
	if err != nil {
		return nil, err
	}

	return dto.FromUser(updatedUser), nil
}

func (s *userService) UpdateAvatar(userID string, imageURL string, publicID string) (*dto.UserResponse, error) {
	ctx, cancel := util.NewDefaultDBContext()
	defer cancel()

	user, err := s.userRepo.GetByID(ctx, userID)
	if err != nil {
		return nil, err
	}

	// Update avatar
	user.Avatar = &model.Image{
		URL:      imageURL,
		PublicID: publicID,
	}
	user.UpdatedAt = time.Now()

	updatedUser, err := s.userRepo.Update(ctx, user)
	if err != nil {
		return nil, err
	}

	return dto.FromUser(updatedUser), nil
}

func (s *userService) DeleteAvatar(userID string) (*dto.UserResponse, error) {
	ctx, cancel := util.NewDefaultDBContext()
	defer cancel()

	// Use UpdateAvatarField to properly unset the avatar field
	updatedUser, err := s.userRepo.UpdateAvatarField(ctx, userID, nil)
	if err != nil {
		return nil, err
	}

	return dto.FromUser(updatedUser), nil
}

func (s *userService) DeleteUser(id string) error {
	ctx, cancel := util.NewDefaultDBContext()
	defer cancel()

	return s.userRepo.Delete(ctx, id)
}

func (s *userService) ChangePassword(userID, oldPassword, newPassword string) error {
	ctx, cancel := util.NewDefaultDBContext()
	defer cancel()

	user, err := s.userRepo.GetByID(ctx, userID)
	if err != nil {
		return err
	}

	// Check old password
	if err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(oldPassword)); err != nil {
		return apperror.ErrInvalidCredentials
	}

	// Hash new password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(newPassword), bcrypt.DefaultCost)
	if err != nil {
		return err
	}

	user.Password = string(hashedPassword)
	user.UpdatedAt = time.Now()
	_, err = s.userRepo.Update(ctx, user)
	return err
}

func (s *userService) GetUserByID(id string) (*dto.UserResponse, error) {
	ctx, cancel := util.NewDefaultDBContext()
	defer cancel()

	user, err := s.userRepo.GetByID(ctx, id)
	if err != nil {
		return nil, err
	}

	return dto.FromUser(user), nil
}

func (s *userService) GetUserByUsername(username string, requesterID string) (*dto.UserResponse, error) {
	ctx, cancel := util.NewDefaultDBContext()
	defer cancel()

	user, err := s.userRepo.GetByUsername(ctx, username)
	if err != nil {
		return nil, err
	}

	return dto.FromUser(user), nil
}

func (s *userService) GetUserByEmail(email string) (*dto.UserResponse, error) {
	ctx, cancel := util.NewDefaultDBContext()
	defer cancel()

	user, err := s.userRepo.GetByEmail(ctx, email)
	if err != nil {
		return nil, err
	}

	return dto.FromUser(user), nil
}

func (s *userService) GetUsers(query *dto.GetUsersQuery) (*dto.PaginatedUsersResponse, error) {
	ctx, cancel := util.NewDefaultDBContext()
	defer cancel()

	filter := repo.Filter{"deleted_at": nil}
	if query.Username != "" {
		filter["username"] = bson.M{"$regex": query.Username, "$options": "i"}
	}

	page := query.Page
	if page < 1 {
		page = 1
	}

	pageSize := query.PageSize
	if pageSize < 1 {
		pageSize = 20
	}
	if pageSize > 100 {
		pageSize = 100
	}

	findOptions := &repo.FindOptions{
		Skip:  int64((page - 1) * pageSize),
		Limit: int64(pageSize),
		Sort:  map[string]int{"created_at": -1},
	}

	users, total, err := s.userRepo.Find(ctx, filter, findOptions)
	if err != nil {
		return nil, err
	}

	userResponses := dto.FromUsers(users)

	return &dto.PaginatedUsersResponse{
		Users: userResponses,
		Pagination: dto.Pagination{
			Page:     page,
			PageSize: pageSize,
			Total:    total,
		},
	}, nil
}

func (s *userService) GetSettings(userID string) (*dto.UserSettingsResponse, error) {
	ctx, cancel := util.NewDefaultDBContext()
	defer cancel()

	user, err := s.userRepo.GetByID(ctx, userID)
	if err != nil {
		if errors.Is(err, mongo.ErrNoDocuments) {
			return nil, apperror.ErrUserNotFound
		}
		return nil, err
	}

	// Return user settings
	return &dto.UserSettingsResponse{
		Language:          user.Settings.Language,
		Theme:             user.Settings.Theme,
		NotifyNewFeatures: user.Settings.NotifyNewFeatures,
	}, nil
}

func (s *userService) UpdateSettings(userID string, req *dto.UpdateSettingsRequest) (*dto.UserSettingsResponse, error) {
	ctx, cancel := util.NewDefaultDBContext()
	defer cancel()

	user, err := s.userRepo.GetByID(ctx, userID)
	if err != nil {
		if errors.Is(err, mongo.ErrNoDocuments) {
			return nil, apperror.ErrUserNotFound
		}
		return nil, err
	}

	// Update settings fields
	if req.Language != nil {
		user.Settings.Language = *req.Language
	}
	if req.Theme != nil {
		user.Settings.Theme = *req.Theme
	}
	if req.NotifyNewFeatures != nil {
		user.Settings.NotifyNewFeatures = *req.NotifyNewFeatures
	}

	// Save updated user
	user.UpdatedAt = time.Now()
	updatedUser, err := s.userRepo.Update(ctx, user)
	if err != nil {
		return nil, err
	}

	return &dto.UserSettingsResponse{
		Language:          updatedUser.Settings.Language,
		Theme:             updatedUser.Settings.Theme,
		NotifyNewFeatures: updatedUser.Settings.NotifyNewFeatures,
	}, nil
}

func (s *userService) CheckUsernameAvailability(username string) (bool, error) {
	// Try cache first
	if s.redisClient != nil {
		ctx, cancel := util.NewDefaultRedisContext()
		defer cancel()

		cacheKey := fmt.Sprintf("username_exists:%s", username)
		cached, err := s.redisClient.Get(ctx, cacheKey).Result()
		if err == nil {
			// Cache hit - "false" means available, "true" means taken
			return cached == "false", nil
		}
	}

	// Cache miss - query database
	dbCtx, cancel := util.NewDefaultDBContext()
	defer cancel()

	_, err := s.userRepo.GetByUsername(dbCtx, username)
	exists := !errors.Is(err, mongo.ErrNoDocuments)

	// Cache the result (5 minutes TTL)
	if s.redisClient != nil {
		ctx, cancel := util.NewDefaultRedisContext()
		defer cancel()

		cacheKey := fmt.Sprintf("username_exists:%s", username)
		value := "false"
		if exists {
			value = "true"
		}
		// Ignore cache write errors, not critical
		_ = s.redisClient.Set(ctx, cacheKey, value, 5*time.Minute).Err()
	}

	return !exists, nil
}
