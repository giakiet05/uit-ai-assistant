package route

import (
	"github.com/giakiet05/uit-ai-assistant/backend/internal/controller"
	"github.com/giakiet05/uit-ai-assistant/backend/internal/middleware"
	"github.com/gin-gonic/gin"
)

func RegisterChatRoutes(rg *gin.RouterGroup, c *controller.ChatController) {
	chat := rg.Group("/chat")
	chat.Use(middleware.RequireAuth()) // All chat routes require authentication
	{
		// Main chat endpoint
		chat.POST("", c.Chat)

		// Session management
		sessions := chat.Group("/sessions")
		{
			sessions.GET("", c.GetSessions)
			sessions.GET("/:id", c.GetSession)
			sessions.GET("/:id/messages", c.GetMessages)
			sessions.DELETE("/:id", c.DeleteSession)
			sessions.PATCH("/:id/title", c.UpdateSessionTitle)
		}
	}
}
