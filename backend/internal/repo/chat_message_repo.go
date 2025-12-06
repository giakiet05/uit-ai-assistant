package repo

import (
	"context"
	"time"

	"github.com/giakiet05/uit-ai-assistant/internal/config"
	"github.com/giakiet05/uit-ai-assistant/internal/model"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// ChatMessageRepo defines the interface for chat message repository
type ChatMessageRepo interface {
	Create(ctx context.Context, message *model.ChatMessage) (*model.ChatMessage, error)
	CreateBatch(ctx context.Context, messages []*model.ChatMessage) error
	GetBySessionID(ctx context.Context, sessionID string, limit int) ([]*model.ChatMessage, error)
	GetByID(ctx context.Context, id string) (*model.ChatMessage, error)
	DeleteBySessionID(ctx context.Context, sessionID string) error
	CountBySessionID(ctx context.Context, sessionID string) (int64, error)
}

type chatMessageRepo struct {
	db         *mongo.Database
	collection *mongo.Collection
}

// NewChatMessageRepo creates a new chat message repository
func NewChatMessageRepo(db *mongo.Database) ChatMessageRepo {
	return &chatMessageRepo{
		db:         db,
		collection: db.Collection(config.ChatMessageColName),
	}
}

// Create creates a new chat message
func (r *chatMessageRepo) Create(ctx context.Context, message *model.ChatMessage) (*model.ChatMessage, error) {
	message.CreatedAt = time.Now()

	result, err := r.collection.InsertOne(ctx, message)
	if err != nil {
		return nil, err
	}

	message.ID = result.InsertedID.(primitive.ObjectID)
	return message, nil
}

// CreateBatch creates multiple chat messages in one operation
func (r *chatMessageRepo) CreateBatch(ctx context.Context, messages []*model.ChatMessage) error {
	if len(messages) == 0 {
		return nil
	}

	docs := make([]interface{}, len(messages))
	now := time.Now()

	for i, msg := range messages {
		msg.CreatedAt = now
		docs[i] = msg
	}

	result, err := r.collection.InsertMany(ctx, docs)
	if err != nil {
		return err
	}

	// Update IDs
	for i, id := range result.InsertedIDs {
		messages[i].ID = id.(primitive.ObjectID)
	}

	return nil
}

// GetBySessionID retrieves messages for a session, ordered by creation time
// If limit > 0, returns the last N messages
func (r *chatMessageRepo) GetBySessionID(ctx context.Context, sessionID string, limit int) ([]*model.ChatMessage, error) {
	objectID, err := primitive.ObjectIDFromHex(sessionID)
	if err != nil {
		return nil, err
	}

	filter := bson.M{"session_id": objectID}

	// Sort by created_at ascending (oldest first)
	findOpts := options.Find().SetSort(bson.D{{Key: "created_at", Value: 1}})

	// If limit is specified, we want the LAST N messages
	// So we need to:
	// 1. Sort descending to get latest messages
	// 2. Limit to N
	// 3. Reverse the results
	if limit > 0 {
		findOpts.SetSort(bson.D{{Key: "created_at", Value: -1}})
		findOpts.SetLimit(int64(limit))
	}

	cursor, err := r.collection.Find(ctx, filter, findOpts)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	var messages []*model.ChatMessage
	if err = cursor.All(ctx, &messages); err != nil {
		return nil, err
	}

	// If we limited, reverse the results to get chronological order
	if limit > 0 && len(messages) > 0 {
		for i, j := 0, len(messages)-1; i < j; i, j = i+1, j-1 {
			messages[i], messages[j] = messages[j], messages[i]
		}
	}

	return messages, nil
}

// GetByID retrieves a chat message by ID
func (r *chatMessageRepo) GetByID(ctx context.Context, id string) (*model.ChatMessage, error) {
	objectID, err := primitive.ObjectIDFromHex(id)
	if err != nil {
		return nil, err
	}

	filter := bson.M{"_id": objectID}

	var message model.ChatMessage
	err = r.collection.FindOne(ctx, filter).Decode(&message)
	if err != nil {
		return nil, err
	}

	return &message, nil
}

// DeleteBySessionID deletes all messages for a session (when session is deleted)
func (r *chatMessageRepo) DeleteBySessionID(ctx context.Context, sessionID string) error {
	objectID, err := primitive.ObjectIDFromHex(sessionID)
	if err != nil {
		return err
	}

	filter := bson.M{"session_id": objectID}
	_, err = r.collection.DeleteMany(ctx, filter)
	return err
}

// CountBySessionID counts messages in a session
func (r *chatMessageRepo) CountBySessionID(ctx context.Context, sessionID string) (int64, error) {
	objectID, err := primitive.ObjectIDFromHex(sessionID)
	if err != nil {
		return 0, err
	}

	filter := bson.M{"session_id": objectID}
	count, err := r.collection.CountDocuments(ctx, filter)
	if err != nil {
		return 0, err
	}

	return count, nil
}
