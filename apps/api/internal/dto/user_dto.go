package dto

import (
	"time"

	"github.com/giakiet05/uit-ai-assistant/backend/internal/model"
)

// --- Request DTOs ---

// GetUsersQuery contains query parameters for searching and paginating users
type GetUsersQuery struct {
	Username string `form:"username"`
	Page     int    `form:"page"`
	PageSize int    `form:"pageSize"`
}

// UpdateUserRequest defines the fields a user can update
type UpdateUserRequest struct {
	Username string `json:"username" binding:"omitempty,min=3,max=30"`
}

// UpdateSettingsRequest allows updating user settings
type UpdateSettingsRequest struct {
	Language          *string `json:"language" binding:"omitempty,oneof=vi en"`
	Theme             *string `json:"theme" binding:"omitempty,oneof=light dark"`
	NotifyNewFeatures *bool   `json:"notify_new_features"`
}

// ChangePasswordRequest for changing user password
type ChangePasswordRequest struct {
	OldPassword string `json:"old_password" binding:"required"`
	NewPassword string `json:"new_password" binding:"required,min=6"`
}

// --- Response DTOs ---

// UserSettingsResponse contains user settings
type UserSettingsResponse struct {
	Language          string `json:"language"`
	Theme             string `json:"theme"`
	NotifyNewFeatures bool   `json:"notify_new_features"`
}

// UserResponse is the main user object returned in API responses
type UserResponse struct {
	ID         string               `json:"id"`
	Username   string               `json:"username"`
	Email      string               `json:"email,omitempty"`
	Role       model.Role           `json:"role"`
	Provider   model.AuthProvider   `json:"provider"`
	IsVerified bool                 `json:"is_verified"`
	IsActive   bool                 `json:"is_active"`
	Avatar     *model.Image         `json:"avatar,omitempty"`
	Settings   UserSettingsResponse `json:"settings"`
	CreatedAt  time.Time            `json:"created_at"`
}

// PaginatedUsersResponse for paginated user lists
type PaginatedUsersResponse struct {
	Users      []*UserResponse `json:"users"`
	Pagination Pagination      `json:"pagination"`
}

// FromUser converts model.User to UserResponse
func FromUser(u *model.User) *UserResponse {
	if u == nil {
		return nil
	}

	return &UserResponse{
		ID:         u.ID.Hex(),
		Username:   u.Username,
		Email:      u.Email,
		Role:       u.Role,
		Provider:   u.Provider,
		IsVerified: u.IsVerified,
		IsActive:   u.IsActive,
		Avatar:     u.Avatar,
		Settings: UserSettingsResponse{
			Language:          u.Settings.Language,
			Theme:             u.Settings.Theme,
			NotifyNewFeatures: u.Settings.NotifyNewFeatures,
		},
		CreatedAt: u.CreatedAt,
	}
}

// FromUsers converts multiple users to response DTOs
func FromUsers(users []*model.User) []*UserResponse {
	responses := make([]*UserResponse, len(users))
	for i, u := range users {
		userResponse := FromUser(u)
		userResponse.Email = "" // Hide email in list views
		responses[i] = userResponse
	}
	return responses
}
