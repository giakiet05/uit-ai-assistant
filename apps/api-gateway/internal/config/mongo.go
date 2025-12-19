package config

import (
	"context"
	"fmt"
	"log"
	"time"

	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

var (
	Client *mongo.Client
	db     *mongo.Database
)

// NewMongoClient creates and returns a new MongoDB client
func NewMongoClient() *mongo.Client {
	uri := Cfg.MongoURI
	if uri == "" {
		log.Fatal("MONGO_URI not configured")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	client, err := mongo.Connect(ctx, options.Client().ApplyURI(uri))
	if err != nil {
		log.Fatalf("Could not connect to MongoDB: %v", err)
	}

	// Test connection
	if err := client.Ping(ctx, nil); err != nil {
		log.Fatalf("MongoDB ping failed: %v", err)
	}

	log.Println("Connected to MongoDB successfully!")

	dbName := Cfg.DBName
	if dbName == "" {
		log.Fatal("DB_NAME not configured")
	}

	Client = client
	db = client.Database(dbName)

	// Ensure required collections exist (create if missing)
	if err := ensureCollections(ctx, db); err != nil {
		log.Fatalf("Collection initialization failed: %v", err)
	}

	log.Printf("Using database: %s\n", dbName)
	return client
}

func ensureCollections(ctx context.Context, db *mongo.Database) error {
	collections, err := db.ListCollectionNames(ctx, struct{}{})
	if err != nil {
		return fmt.Errorf("failed to list collections: %w", err)
	}

	required := []string{
		UserColName,
		NotificationColName,
		EmailVerificationColName,
		ChatSessionColName,
		ChatMessageColName,
	}

	existing := make(map[string]bool, len(collections))
	for _, c := range collections {
		existing[c] = true
	}

	// Create missing collections
	for _, name := range required {
		if !existing[name] {
			log.Printf("Creating missing collection: %s", name)
			if err := db.CreateCollection(ctx, name); err != nil {
				return fmt.Errorf("failed to create collection %q: %w", name, err)
			}
			log.Printf("✓ Collection created: %s", name)
		}
	}

	log.Println("All required collections ready")
	return nil
}
