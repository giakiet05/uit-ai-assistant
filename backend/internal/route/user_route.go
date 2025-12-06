package route

import (
	"github.com/giakiet05/uit-ai-assistant/internal/controller"
	"github.com/giakiet05/uit-ai-assistant/internal/middleware"
	"github.com/gin-gonic/gin"
)

func RegisterUserRoutes(rg *gin.RouterGroup, c *controller.UserController) {
	users := rg.Group("/users")

	// Public routes - anyone can view a user's profile
	users.GET("/", c.GetUsers)
	users.GET("/profile/:username", c.GetUserByUsername)

	// Routes for the currently authenticated user ("me")
	me := users.Group("/me")
	me.Use(middleware.RequireAuth())
	{
		me.GET("", c.GetMyProfile)
		me.PATCH("", c.UpdateUser)                // Update user (username)
		me.PATCH("/password", c.ChangePassword)   // Change password
		me.POST("/avatar", c.UploadAvatar)        // Upload avatar
		me.DELETE("/avatar", c.DeleteAvatar)      // Delete avatar
		me.GET("/settings", c.GetSettings)        // Get settings
		me.PATCH("/settings", c.UpdateSettings)   // Update settings
	}
}
