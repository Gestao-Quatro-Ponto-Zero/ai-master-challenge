package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"
	"github.com/gofiber/fiber/v2/middleware/logger"
	"github.com/gofiber/fiber/v2/middleware/recover"
	"github.com/gofiber/websocket/v2"
	"github.com/joho/godotenv"
	"github.com/matheus-petrato/sales-copilot-back/internal/api/handlers"
	"github.com/matheus-petrato/sales-copilot-back/internal/api/middleware"
	"github.com/matheus-petrato/sales-copilot-back/internal/database/postgres"
	"github.com/matheus-petrato/sales-copilot-back/internal/services"
	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
)

func main() {
	// Setup logging
	zerolog.TimeFieldFormat = zerolog.TimeFormatUnix
	log.Logger = log.Output(zerolog.ConsoleWriter{Out: os.Stderr})

	// Load .env
	if err := godotenv.Load(); err != nil {
		log.Warn().Msg("No .env file found, reading from environment")
	}

	// Connect to Database
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if _, err := postgres.Connect(ctx); err != nil {
		log.Error().Err(err).Msg("Could not connect to database")
	}
	defer postgres.Close()

	app := fiber.New(fiber.Config{
		ErrorHandler: func(ctx *fiber.Ctx, err error) error {
			code := fiber.StatusInternalServerError
			if e, ok := err.(*fiber.Error); ok {
				code = e.Code
			}
			return ctx.Status(code).JSON(fiber.Map{
				"error": err.Error(),
			})
		},
	})

	// Middleware
	app.Use(logger.New())
	app.Use(recover.New())
	app.Use(cors.New())

	// Routes
	app.Get("/health", func(c *fiber.Ctx) error {
		return c.JSON(fiber.Map{
			"status": "up",
			"time":   time.Now().Format(time.RFC3339),
		})
	})

	// API Group
	api := app.Group("/api")
	
	// Services
	pool := postgres.GetPool()
	importSvc := services.NewImportService(pool)
	scoringSvc := services.NewScoringService(pool)
	dataSvc := services.NewDataConnector(pool)
	convSvc := services.NewConversationService(pool)

	// Handlers
	authHandler := handlers.NewAuthHandler(pool)
	chatHandler := handlers.NewChatHandler(convSvc, dataSvc)
	importHandler := handlers.NewImportHandler(importSvc, scoringSvc)
	analyticsHandler := handlers.NewAnalyticsHandler(pool)
	briefingHandler := handlers.NewBriefingHandler(pool)
	dealHandler := handlers.NewDealHandler(dataSvc)
	alertHandler := handlers.NewAlertHandler(pool)
	settingsHandler := handlers.NewSettingsHandler(pool)

	// Public Auth
	auth := api.Group("/auth")
	auth.Post("/login", authHandler.Login)

	// Protected Routes
	protected := api.Group("/")
	protected.Use(middleware.JWTMiddleware())

	// Me
	protected.Get("/me", authHandler.Me)

	// Briefing
	protected.Get("/briefing", briefingHandler.GetBriefing)

	// Deals
	protected.Get("/deals", dealHandler.ListDeals)
	protected.Get("/deals/:id", dealHandler.GetDeal)

	// Alerts
	protected.Get("/alerts", alertHandler.GetAlerts)

	// Chat & Agent
	protected.Post("/chat", chatHandler.SendMessage)
	protected.Get("/chat/history", chatHandler.GetHistory)

	// Imports
	protected.Post("/imports", importHandler.UploadCSV)
	protected.Get("/imports", importHandler.ListImports)
	protected.Delete("/imports/:id", importHandler.DeleteImport)
	protected.Post("/imports/:id/reprocess", importHandler.ReprocessImport)

	// Analytics & Stats
	analytics := protected.Group("/analytics")
	analytics.Get("/stats", analyticsHandler.GetDashboardStats)
	analytics.Get("/pipeline", analyticsHandler.GetPipelineDistribution)

	stats := protected.Group("/stats")
	stats.Get("/team", analyticsHandler.GetTeamStats)

	// Settings
	protected.Get("/settings", settingsHandler.GetSettings)
	protected.Patch("/settings", settingsHandler.UpdateSettings)

	// WebSocket (Chat)
	app.Use("/ws", func(c *fiber.Ctx) error {
		if websocket.IsWebSocketUpgrade(c) {
			return c.Next()
		}
		return fiber.ErrUpgradeRequired
	})
	app.Get("/ws/chat", websocket.New(chatHandler.WebSocketChat))

	// Start server
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	// Graceful shutdown
	go func() {
		if err := app.Listen(":" + port); err != nil {
			log.Fatal().Err(err).Msg("Server failed to start")
		}
	}()

	fmt.Printf("\n  🚀 G4 Compass API is running on port %s\n\n", port)

	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)

	<-c // Wait for interrupt
	log.Info().Msg("Shutting down gracefully...")
	_ = app.Shutdown()
}
