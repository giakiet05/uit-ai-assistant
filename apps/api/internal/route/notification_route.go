package route

import (
	"github.com/giakiet05/uit-ai-assistant/backend/internal/controller"
	"github.com/giakiet05/uit-ai-assistant/backend/internal/middleware"
	"github.com/gin-gonic/gin"
)

func RegisterNotificationRoutes(rg *gin.RouterGroup, c *controller.NotificationController) {
	notifications := rg.Group("/notifications")
	notifications.Use(middleware.RequireAuth()) // All notification routes require authentication
	{
		notifications.GET("", c.GetNotifications)
		notifications.PATCH("/read-all", c.MarkAllAsRead)
	}
}
