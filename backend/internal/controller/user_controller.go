package controller

import (
	"net/http"

	"github.com/giakiet05/uit-ai-assistant/internal/apperror"
	"github.com/giakiet05/uit-ai-assistant/internal/auth"
	"github.com/giakiet05/uit-ai-assistant/internal/dto"
	"github.com/giakiet05/uit-ai-assistant/internal/platform/cloudinary"
	"github.com/giakiet05/uit-ai-assistant/internal/service"
	"github.com/gin-gonic/gin"
)

// UserController handles requests related to user management.
type UserController struct {
	service service.UserService
}

// NewUserController creates a new UserController.
func NewUserController(service service.UserService) *UserController {
	return &UserController{service: service}
}

// GetUsers retrieves a paginated list of users with optional username search.
func (c *UserController) GetUsers(ctx *gin.Context) {
	var query dto.GetUsersQuery
	if err := ctx.ShouldBindQuery(&query); err != nil {
		dto.SendError(ctx, http.StatusBadRequest, "Invalid query parameters", apperror.ErrBadRequest.Code)
		return
	}

	response, err := c.service.GetUsers(&query)
	if err != nil {
		dto.SendError(ctx, apperror.StatusFromError(err), apperror.Message(err), apperror.Code(err))
		return
	}
	dto.SendSuccess(ctx, http.StatusOK, "Users retrieved successfully", response)
}

// GetUserByUsername retrieves a user's public profile by their username.
func (c *UserController) GetUserByUsername(ctx *gin.Context) {
	username := ctx.Param("username")

	// Get requester ID (may be empty for unauthenticated requests)
	requesterID, _ := ctx.Get("user_id")
	requesterIDStr := ""
	if id, ok := requesterID.(string); ok {
		requesterIDStr = id
	}

	user, err := c.service.GetUserByUsername(username, requesterIDStr)
	if err != nil {
		dto.SendError(ctx, apperror.StatusFromError(err), apperror.Message(err), apperror.Code(err))
		return
	}

	user.Email = "" // Hide email for public profile
	dto.SendSuccess(ctx, http.StatusOK, "User profile retrieved successfully", user)
}

// GetMyProfile retrieves the profile of the currently authenticated user.
func (c *UserController) GetMyProfile(ctx *gin.Context) {
	authUser, exists := ctx.Get("authUser")
	if !exists {
		dto.SendError(ctx, http.StatusUnauthorized, apperror.ErrForbidden.Message, apperror.ErrForbidden.Code)
		return
	}

	user, err := c.service.GetUserByID(authUser.(auth.AuthUser).ID)
	if err != nil {
		dto.SendError(ctx, apperror.StatusFromError(err), apperror.Message(err), apperror.Code(err))
		return
	}

	dto.SendSuccess(ctx, http.StatusOK, "Profile retrieved successfully", user)
}

// UpdateUser allows a user to update their own information (username).
func (c *UserController) UpdateUser(ctx *gin.Context) {
	authUser, exists := ctx.Get("authUser")
	if !exists {
		dto.SendError(ctx, http.StatusUnauthorized, apperror.ErrForbidden.Message, apperror.ErrForbidden.Code)
		return
	}

	var req dto.UpdateUserRequest
	if err := ctx.ShouldBindJSON(&req); err != nil {
		dto.SendError(ctx, http.StatusBadRequest, apperror.Message(apperror.ErrBadRequest), apperror.ErrBadRequest.Code)
		return
	}

	updatedUser, err := c.service.UpdateUser(authUser.(auth.AuthUser).ID, &req)
	if err != nil {
		dto.SendError(ctx, apperror.StatusFromError(err), apperror.Message(err), apperror.Code(err))
		return
	}

	dto.SendSuccess(ctx, http.StatusOK, "User updated successfully", updatedUser)
}

// UploadAvatar handles avatar image uploads.
func (c *UserController) UploadAvatar(ctx *gin.Context) {
	authUser, exists := ctx.Get("authUser")
	if !exists {
		dto.SendError(ctx, http.StatusUnauthorized, apperror.ErrForbidden.Message, apperror.ErrForbidden.Code)
		return
	}

	form, err := ctx.MultipartForm()
	if err != nil {
		dto.SendError(ctx, http.StatusBadRequest, "Invalid form data", "INVALID_FORM")
		return
	}

	images, err := cloudinary.UploadImages(form.File["avatar"])
	if err != nil {
		dto.SendError(ctx, http.StatusInternalServerError, "Failed to upload image", "UPLOAD_FAILED")
		return
	}

	updatedUser, err := c.service.UpdateAvatar(authUser.(auth.AuthUser).ID, images[0].URL, images[0].PublicID)
	if err != nil {
		dto.SendError(ctx, http.StatusInternalServerError, "Failed to update avatar", "DB_UPDATE_FAILED")
		return
	}

	dto.SendSuccess(ctx, http.StatusOK, "Avatar updated successfully", updatedUser)
}

// DeleteAvatar removes the user's avatar.
func (c *UserController) DeleteAvatar(ctx *gin.Context) {
	authUser, exists := ctx.Get("authUser")
	if !exists {
		dto.SendError(ctx, http.StatusUnauthorized, apperror.ErrForbidden.Message, apperror.ErrForbidden.Code)
		return
	}

	updatedUser, err := c.service.DeleteAvatar(authUser.(auth.AuthUser).ID)
	if err != nil {
		dto.SendError(ctx, apperror.StatusFromError(err), apperror.Message(err), apperror.Code(err))
		return
	}

	dto.SendSuccess(ctx, http.StatusOK, "Avatar deleted successfully", updatedUser)
}

func (c *UserController) ChangePassword(ctx *gin.Context) {
	authUser, exists := ctx.Get("authUser")
	if !exists {
		dto.SendError(ctx, http.StatusUnauthorized, apperror.ErrForbidden.Message, apperror.ErrForbidden.Code)
		return
	}

	var req dto.ChangePasswordRequest
	if err := ctx.ShouldBindJSON(&req); err != nil {
		dto.SendError(ctx, http.StatusBadRequest, apperror.Message(apperror.ErrBadRequest), apperror.ErrBadRequest.Code)
		return
	}

	err := c.service.ChangePassword(authUser.(auth.AuthUser).ID, req.OldPassword, req.NewPassword)
	if err != nil {
		dto.SendError(ctx, apperror.StatusFromError(err), apperror.Message(err), apperror.Code(err))
		return
	}

	dto.SendSuccess(ctx, http.StatusOK, "Password changed successfully", nil)
}

// GetSettings retrieves the current user's settings
func (c *UserController) GetSettings(ctx *gin.Context) {
	authUser, exists := ctx.Get("authUser")
	if !exists {
		dto.SendError(ctx, http.StatusUnauthorized, apperror.ErrForbidden.Message, apperror.ErrForbidden.Code)
		return
	}

	settings, err := c.service.GetSettings(authUser.(auth.AuthUser).ID)
	if err != nil {
		dto.SendError(ctx, apperror.StatusFromError(err), apperror.Message(err), apperror.Code(err))
		return
	}

	dto.SendSuccess(ctx, http.StatusOK, "Settings retrieved successfully", settings)
}

// UpdateSettings updates the current user's settings
func (c *UserController) UpdateSettings(ctx *gin.Context) {
	authUser, exists := ctx.Get("authUser")
	if !exists {
		dto.SendError(ctx, http.StatusUnauthorized, apperror.ErrForbidden.Message, apperror.ErrForbidden.Code)
		return
	}

	var req dto.UpdateSettingsRequest
	if err := ctx.ShouldBindJSON(&req); err != nil {
		dto.SendError(ctx, http.StatusBadRequest, apperror.Message(apperror.ErrBadRequest), apperror.ErrBadRequest.Code)
		return
	}

	settings, err := c.service.UpdateSettings(authUser.(auth.AuthUser).ID, &req)
	if err != nil {
		dto.SendError(ctx, apperror.StatusFromError(err), apperror.Message(err), apperror.Code(err))
		return
	}

	dto.SendSuccess(ctx, http.StatusOK, "Settings updated successfully", settings)
}

// CheckUsername checks if a username is available for registration.
// This is a public endpoint for real-time username availability checking.
func (c *UserController) CheckUsername(ctx *gin.Context) {
	var req struct {
		Username string `json:"username" binding:"required,min=3,max=20"`
	}

	if err := ctx.ShouldBindJSON(&req); err != nil {
		dto.SendError(ctx, http.StatusBadRequest, apperror.Message(apperror.ErrBadRequest), apperror.ErrBadRequest.Code)
		return
	}

	available, err := c.service.CheckUsernameAvailability(req.Username)
	if err != nil {
		dto.SendError(ctx, http.StatusInternalServerError, apperror.Message(apperror.ErrInternal), apperror.ErrInternal.Code)
		return
	}

	dto.SendSuccess(ctx, http.StatusOK, "", gin.H{"available": available})
}

// --- Admin-only actions ---

func (c *UserController) DeleteUser(ctx *gin.Context) {
	userID := ctx.Param("id")
	err := c.service.DeleteUser(userID)
	if err != nil {
		dto.SendError(ctx, apperror.StatusFromError(err), apperror.Message(err), apperror.Code(err))
		return
	}

	dto.SendSuccess(ctx, http.StatusOK, "User deleted successfully", gin.H{"id": userID})
}
