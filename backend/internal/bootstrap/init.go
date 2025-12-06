package bootstrap

import (
	"log"

	"github.com/giakiet05/uit-ai-assistant/internal/auth"
	"github.com/giakiet05/uit-ai-assistant/internal/config"
	"github.com/giakiet05/uit-ai-assistant/internal/controller"
	"github.com/giakiet05/uit-ai-assistant/internal/middleware"
	"github.com/giakiet05/uit-ai-assistant/internal/platform/bus"
	"github.com/giakiet05/uit-ai-assistant/internal/platform/email"
	"github.com/giakiet05/uit-ai-assistant/internal/platform/gemini"
	"github.com/giakiet05/uit-ai-assistant/internal/platform/ws"
	"github.com/giakiet05/uit-ai-assistant/internal/repo"
	"github.com/giakiet05/uit-ai-assistant/internal/route"
	"github.com/giakiet05/uit-ai-assistant/internal/service"
	"github.com/gin-gonic/gin"
	"github.com/redis/go-redis/v9"
	"go.mongodb.org/mongo-driver/mongo"
)

type Repos struct {
	repo.UserRepo
	repo.NotificationRepo
	repo.EmailVerificationRepo
}

type Services struct {
	service.AuthService
	service.UserService
	service.NotificationService
	service.AdminUserService
}

type Controllers struct {
	controller.AuthController
	controller.UserController
	controller.NotificationController
	controller.WebSocketController
	controller.AdminUserController
}

func initRepos(client *mongo.Client, db *mongo.Database) *Repos {
	return &Repos{
		UserRepo:              repo.NewUserRepo(db),
		NotificationRepo:      repo.NewNotificationRepo(db),
		EmailVerificationRepo: repo.NewEmailVerificationRepo(db),
	}
}

func initServices(repos *Repos, redisClient *redis.Client, emailSender email.Sender, eventBus bus.EventBus, geminiClient *gemini.GeminiClient) *Services {
	return &Services{
		AuthService:         service.NewAuthService(repos.UserRepo, repos.EmailVerificationRepo, emailSender, redisClient),
		UserService:         service.NewUserService(repos.UserRepo, eventBus, redisClient),
		NotificationService: service.NewNotificationService(repos.NotificationRepo, repos.UserRepo, eventBus, redisClient),
	}

}

func initControllers(services *Services, wsHub *ws.Hub) *Controllers {
	return &Controllers{
		AuthController:         *controller.NewAuthController(services.AuthService),
		UserController:         *controller.NewUserController(services.UserService),
		NotificationController: *controller.NewNotificationController(services.NotificationService),
		WebSocketController:    *controller.NewWebSocketController(wsHub),
		AdminUserController:    *controller.NewAdminUserController(services.AdminUserService),
	}
}

func initRoutes(controllers *Controllers, r *gin.Engine) {
	r.GET("/ping", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "pong"})
	})

	api := r.Group("/api")
	api.GET("/", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "Welcome to LKForum API!"})
	})

	route.RegisterAuthRoutes(api, &controllers.AuthController, &controllers.UserController)
	route.RegisterUserRoutes(api, &controllers.UserController)
	route.RegisterNotificationRoutes(api, &controllers.NotificationController)
	route.RegisterWebSocketRoutes(api, &controllers.WebSocketController)
	route.RegisterAdminUserRoutes(api, &controllers.AdminUserController)
}

func Init() (*gin.Engine, error) {
	config.LoadConfig()
	auth.InitGoogleOAuthConfig()

	redisClient := config.NewRedisClient()

	if err := InitializeTokenService(redisClient); err != nil {
		log.Printf("Warning: Token invalidation service not available: %v\n", err)
	}

	client := config.NewMongoClient()
	db := client.Database(config.Cfg.DBName)
	router := gin.Default()

	router.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", config.Cfg.FrontendURL)
		c.Writer.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		c.Writer.Header().Set("Access-Control-Allow-Credentials", "true")
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}
		c.Next()
	})

	eventBus := bus.NewEventBus()
	wsHub := ws.NewHub(eventBus)
	emailSender := email.NewSMTPSender()

	// Initialize Gemini client for content moderation
	geminiClient, err := gemini.NewGeminiClient(&config.Cfg.Gemini)
	if err != nil {
		log.Printf("Warning: Gemini client initialization failed: %v. Content moderation will be disabled.", err)
	}

	repos := initRepos(client, db)
	services := initServices(repos, redisClient, emailSender, eventBus, geminiClient)
	controllers := initControllers(services, wsHub)

	// Inject userRepo into middleware for settings caching
	middleware.SetUserRepo(repos.UserRepo)

	initRoutes(controllers, router)

	// Start background services
	go wsHub.Start()
	services.NotificationService.Start()

	return router, nil
}
