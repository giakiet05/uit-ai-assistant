package route

import (
	"github.com/giakiet05/uit-ai-assistant/backend/internal/controller"
	"github.com/giakiet05/uit-ai-assistant/backend/internal/middleware"
	"github.com/gin-gonic/gin"
)

func RegisterCookieRoutes(rg *gin.RouterGroup, cookieCtrl *controller.CookieController) {
	cookie := rg.Group("/cookie")
	cookie.Use(middleware.RequireAuth()) // Cần auth
	{
		cookie.POST("/sync", cookieCtrl.SyncCookie)
		cookie.GET("/status", cookieCtrl.GetCookieStatus)
	}
}
