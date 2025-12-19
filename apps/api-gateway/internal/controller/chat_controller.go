package controller

import (
	"net/http"

	"github.com/giakiet05/uit-ai-assistant/backend/internal/apperror"
	"github.com/giakiet05/uit-ai-assistant/backend/internal/auth"
	"github.com/giakiet05/uit-ai-assistant/backend/internal/dto"
	"github.com/giakiet05/uit-ai-assistant/backend/internal/service"
	"github.com/giakiet05/uit-ai-assistant/backend/internal/util"
	"github.com/gin-gonic/gin"
)

// ChatController handles chat-related requests
type ChatController struct {
	chatService service.ChatService
}

// NewChatController creates a new ChatController
func NewChatController(chatService service.ChatService) *ChatController {
	return &ChatController{
		chatService: chatService,
	}
}

// Chat handles chat request
// POST /api/chat
func (c *ChatController) Chat(ctx *gin.Context) {
	// Get authenticated user
	authUser, exists := ctx.Get("authUser")
	if !exists {
		dto.SendError(ctx, http.StatusUnauthorized, apperror.ErrForbidden.Message, apperror.ErrForbidden.Code)
		return
	}
	userID := authUser.(auth.AuthUser).ID

	// Bind request
	var req dto.ChatRequest
	if err := ctx.ShouldBindJSON(&req); err != nil {
		dto.SendError(ctx, http.StatusBadRequest, "Invalid request body", apperror.ErrBadRequest.Code)
		return
	}

	// Validate message
	if req.Message == "" {
		dto.SendError(ctx, http.StatusBadRequest, "Message cannot be empty", apperror.ErrBadRequest.Code)
		return
	}

	// Call service
	dbCtx, cancel := util.NewDefaultDBContext()
	defer cancel()

	assistantMsg, err := c.chatService.Chat(dbCtx, userID, req.SessionID, req.Message)
	if err != nil {
		dto.SendError(ctx, apperror.StatusFromError(err), apperror.Message(err), apperror.Code(err))
		return
	}

	// Build response
	response := dto.ChatResponse{
		SessionID: assistantMsg.SessionID.Hex(),
		Message: dto.ChatMessageResponse{
			ID:        assistantMsg.ID.Hex(),
			Role:      string(assistantMsg.Role),
			Content:   assistantMsg.Content,
			Metadata:  assistantMsg.Metadata,
			CreatedAt: assistantMsg.CreatedAt,
		},
	}

	dto.SendSuccess(ctx, http.StatusOK, "Chat completed successfully", response)
}

// GetSessions retrieves all sessions for the authenticated user
// GET /api/chat/sessions
func (c *ChatController) GetSessions(ctx *gin.Context) {
	authUser, exists := ctx.Get("authUser")
	if !exists {
		dto.SendError(ctx, http.StatusUnauthorized, apperror.ErrForbidden.Message, apperror.ErrForbidden.Code)
		return
	}
	userID := authUser.(auth.AuthUser).ID

	// Parse query params
	var query dto.GetSessionsQuery
	if err := ctx.ShouldBindQuery(&query); err != nil {
		dto.SendError(ctx, http.StatusBadRequest, "Invalid query parameters", apperror.ErrBadRequest.Code)
		return
	}

	// Build options
	opts := query.ToFindOptions()

	// Call service
	dbCtx, cancel := util.NewDefaultDBContext()
	defer cancel()

	sessions, err := c.chatService.GetSessionsByUserID(dbCtx, userID, opts)
	if err != nil {
		dto.SendError(ctx, apperror.StatusFromError(err), apperror.Message(err), apperror.Code(err))
		return
	}

	// Convert to response
	response := make([]dto.SessionResponse, len(sessions))
	for i, session := range sessions {
		response[i] = dto.SessionResponse{
			ID:        session.ID.Hex(),
			Title:     session.Title,
			CreatedAt: session.CreatedAt,
			UpdatedAt: session.UpdatedAt,
		}
	}

	dto.SendSuccess(ctx, http.StatusOK, "Sessions retrieved successfully", response)
}

// GetSession retrieves a single session by ID
// GET /api/chat/sessions/:id
func (c *ChatController) GetSession(ctx *gin.Context) {
	authUser, exists := ctx.Get("authUser")
	if !exists {
		dto.SendError(ctx, http.StatusUnauthorized, apperror.ErrForbidden.Message, apperror.ErrForbidden.Code)
		return
	}
	userID := authUser.(auth.AuthUser).ID

	sessionID := ctx.Param("id")
	if sessionID == "" {
		dto.SendError(ctx, http.StatusBadRequest, "Session ID is required", apperror.ErrBadRequest.Code)
		return
	}

	// Call service
	dbCtx, cancel := util.NewDefaultDBContext()
	defer cancel()

	session, err := c.chatService.GetSessionByID(dbCtx, userID, sessionID)
	if err != nil {
		dto.SendError(ctx, apperror.StatusFromError(err), apperror.Message(err), apperror.Code(err))
		return
	}

	response := dto.SessionResponse{
		ID:        session.ID.Hex(),
		Title:     session.Title,
		CreatedAt: session.CreatedAt,
		UpdatedAt: session.UpdatedAt,
	}

	dto.SendSuccess(ctx, http.StatusOK, "Session retrieved successfully", response)
}

// GetMessages retrieves messages for a session
// GET /api/chat/sessions/:id/messages
func (c *ChatController) GetMessages(ctx *gin.Context) {
	authUser, exists := ctx.Get("authUser")
	if !exists {
		dto.SendError(ctx, http.StatusUnauthorized, apperror.ErrForbidden.Message, apperror.ErrForbidden.Code)
		return
	}
	userID := authUser.(auth.AuthUser).ID

	sessionID := ctx.Param("id")
	if sessionID == "" {
		dto.SendError(ctx, http.StatusBadRequest, "Session ID is required", apperror.ErrBadRequest.Code)
		return
	}

	// Parse query params
	var query dto.GetMessagesQuery
	if err := ctx.ShouldBindQuery(&query); err != nil {
		dto.SendError(ctx, http.StatusBadRequest, "Invalid query parameters", apperror.ErrBadRequest.Code)
		return
	}

	// Default limit
	limit := query.Limit
	if limit == 0 {
		limit = 50 // Default 50 messages
	}

	// Call service
	dbCtx, cancel := util.NewDefaultDBContext()
	defer cancel()

	messages, err := c.chatService.GetMessagesBySessionID(dbCtx, userID, sessionID, limit)
	if err != nil {
		dto.SendError(ctx, apperror.StatusFromError(err), apperror.Message(err), apperror.Code(err))
		return
	}

	// Convert to response
	response := make([]dto.ChatMessageResponse, len(messages))
	for i, msg := range messages {
		response[i] = dto.ChatMessageResponse{
			ID:        msg.ID.Hex(),
			Role:      string(msg.Role),
			Content:   msg.Content,
			Metadata:  msg.Metadata,
			CreatedAt: msg.CreatedAt,
		}
	}

	dto.SendSuccess(ctx, http.StatusOK, "Messages retrieved successfully", response)
}

// DeleteSession soft deletes a session
// DELETE /api/chat/sessions/:id
func (c *ChatController) DeleteSession(ctx *gin.Context) {
	authUser, exists := ctx.Get("authUser")
	if !exists {
		dto.SendError(ctx, http.StatusUnauthorized, apperror.ErrForbidden.Message, apperror.ErrForbidden.Code)
		return
	}
	userID := authUser.(auth.AuthUser).ID

	sessionID := ctx.Param("id")
	if sessionID == "" {
		dto.SendError(ctx, http.StatusBadRequest, "Session ID is required", apperror.ErrBadRequest.Code)
		return
	}

	// Call service
	dbCtx, cancel := util.NewDefaultDBContext()
	defer cancel()

	err := c.chatService.DeleteSession(dbCtx, userID, sessionID)
	if err != nil {
		dto.SendError(ctx, apperror.StatusFromError(err), apperror.Message(err), apperror.Code(err))
		return
	}

	dto.SendSuccess(ctx, http.StatusOK, "Session deleted successfully", nil)
}

// UpdateSessionTitle updates the session title
// PATCH /api/chat/sessions/:id/title
func (c *ChatController) UpdateSessionTitle(ctx *gin.Context) {
	authUser, exists := ctx.Get("authUser")
	if !exists {
		dto.SendError(ctx, http.StatusUnauthorized, apperror.ErrForbidden.Message, apperror.ErrForbidden.Code)
		return
	}
	userID := authUser.(auth.AuthUser).ID

	sessionID := ctx.Param("id")
	if sessionID == "" {
		dto.SendError(ctx, http.StatusBadRequest, "Session ID is required", apperror.ErrBadRequest.Code)
		return
	}

	// Bind request
	var req dto.UpdateSessionTitleRequest
	if err := ctx.ShouldBindJSON(&req); err != nil {
		dto.SendError(ctx, http.StatusBadRequest, "Invalid request body", apperror.ErrBadRequest.Code)
		return
	}

	// Validate title
	if req.Title == "" {
		dto.SendError(ctx, http.StatusBadRequest, "Title cannot be empty", apperror.ErrBadRequest.Code)
		return
	}

	// Call service
	dbCtx, cancel := util.NewDefaultDBContext()
	defer cancel()

	session, err := c.chatService.UpdateSessionTitle(dbCtx, userID, sessionID, req.Title)
	if err != nil {
		dto.SendError(ctx, apperror.StatusFromError(err), apperror.Message(err), apperror.Code(err))
		return
	}

	response := dto.SessionResponse{
		ID:        session.ID.Hex(),
		Title:     session.Title,
		CreatedAt: session.CreatedAt,
		UpdatedAt: session.UpdatedAt,
	}

	dto.SendSuccess(ctx, http.StatusOK, "Session title updated successfully", response)
}
