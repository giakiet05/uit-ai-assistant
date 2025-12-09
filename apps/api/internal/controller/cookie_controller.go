package controller

import (
	"fmt"
	"net/http"
	"time"

	"github.com/giakiet05/uit-ai-assistant/backend/internal/apperror"
	"github.com/giakiet05/uit-ai-assistant/backend/internal/auth"
	"github.com/giakiet05/uit-ai-assistant/backend/internal/dto"
	"github.com/giakiet05/uit-ai-assistant/backend/internal/util"
	"github.com/gin-gonic/gin"
	"github.com/redis/go-redis/v9"
)

type CookieController struct {
	redisClient *redis.Client
}

func NewCookieController(redisClient *redis.Client) *CookieController {
	return &CookieController{redisClient: redisClient}
}

// SyncCookie saves external service cookie to Redis
// POST /api/v1/cookie/sync
func (c *CookieController) SyncCookie(ctx *gin.Context) {
	// Get authenticated user (từ middleware)
	authUser, exists := ctx.Get("authUser")
	if !exists {
		dto.SendError(ctx, http.StatusUnauthorized, "Unauthorized", "UNAUTHORIZED")
		return
	}
	user := authUser.(auth.AuthUser)

	// Parse request
	var req struct {
		Source string `json:"source" binding:"required"` // "daa", "courses", "drl"
		Cookie string `json:"cookie" binding:"required"`
	}

	if err := ctx.ShouldBindJSON(&req); err != nil {
		dto.SendError(ctx, http.StatusBadRequest, apperror.Message(apperror.ErrBadRequest), apperror.ErrBadRequest.Code)
		return
	}

	// Validate source
	validSources := map[string]bool{"daa": true, "courses": true, "drl": true}
	if !validSources[req.Source] {
		dto.SendError(ctx, http.StatusBadRequest, "Invalid source. Must be 'daa', 'courses', or 'drl'", "INVALID_SOURCE")
		return
	}

	// Save to Redis
	redisCtx, cancel := util.NewDefaultRedisContext()
	defer cancel()

	key := fmt.Sprintf("%s_cookie:%s", req.Source, user.ID)
	err := c.redisClient.Set(redisCtx, key, req.Cookie, 24*time.Hour).Err()
	if err != nil {
		dto.SendError(ctx, http.StatusInternalServerError, "Failed to save cookie", "REDIS_ERROR")
		return
	}

	dto.SendSuccess(ctx, http.StatusOK, fmt.Sprintf("Cookie for %s saved successfully", req.Source), nil)
}

// GetCookieStatus checks which cookies have been synced
// GET /api/v1/cookie/status
func (c *CookieController) GetCookieStatus(ctx *gin.Context) {
	authUser, exists := ctx.Get("authUser")
	if !exists {
		dto.SendError(ctx, http.StatusUnauthorized, "Unauthorized", "UNAUTHORIZED")
		return
	}
	user := authUser.(auth.AuthUser)

	redisCtx, cancel := util.NewDefaultRedisContext()
	defer cancel()

	sources := []string{"daa", "courses", "drl"}
	status := make(map[string]interface{})

	for _, source := range sources {
		key := fmt.Sprintf("%s_cookie:%s", source, user.ID)

		exists, err := c.redisClient.Exists(redisCtx, key).Result()
		if err != nil {
			status[source] = map[string]interface{}{
				"synced": false,
				"error":  err.Error(),
			}
			continue
		}

		if exists > 0 {
			ttl, _ := c.redisClient.TTL(redisCtx, key).Result()
			status[source] = map[string]interface{}{
				"synced":     true,
				"expires_in": int(ttl.Seconds()),
			}
		} else {
			status[source] = map[string]interface{}{
				"synced": false,
			}
		}
	}

	dto.SendSuccess(ctx, http.StatusOK, "Cookie status retrieved", status)
}
