package repo

import (
	"context"
	"errors"
	"time"

	"github.com/giakiet05/uit-ai-assistant/backend/internal/config"
	"github.com/giakiet05/uit-ai-assistant/backend/internal/model"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// ChatSessionRepo defines the interface for chat session repository
type ChatSessionRepo interface {
	Create(ctx context.Context, session *model.ChatSession) (*model.ChatSession, error)
	GetByID(ctx context.Context, id string) (*model.ChatSession, error)
	GetByUserID(ctx context.Context, userID string, opts *FindOptions) ([]*model.ChatSession, error)
	Update(ctx context.Context, session *model.ChatSession) (*model.ChatSession, error)
	Delete(ctx context.Context, id string) error // Soft delete
	HardDelete(ctx context.Context, id string) error
	CountByUserID(ctx context.Context, userID string) (int64, error)
}

type chatSessionRepo struct {
	db         *mongo.Database
	collection *mongo.Collection
}

// NewChatSessionRepo creates a new chat session repository
func NewChatSessionRepo(db *mongo.Database) ChatSessionRepo {
	return &chatSessionRepo{
		db:         db,
		collection: db.Collection(config.ChatSessionColName),
	}
}

// Create creates a new chat session
func (r *chatSessionRepo) Create(ctx context.Context, session *model.ChatSession) (*model.ChatSession, error) {
	session.CreatedAt = time.Now()
	session.UpdatedAt = time.Now()

	result, err := r.collection.InsertOne(ctx, session)
	if err != nil {
		return nil, err
	}

	session.ID = result.InsertedID.(primitive.ObjectID)
	return session, nil
}

// GetByID retrieves a chat session by ID (excluding soft-deleted)
func (r *chatSessionRepo) GetByID(ctx context.Context, id string) (*model.ChatSession, error) {
	objectID, err := primitive.ObjectIDFromHex(id)
	if err != nil {
		return nil, err
	}

	filter := bson.M{
		"_id":        objectID,
		"deleted_at": nil, // Exclude soft-deleted
	}

	var session model.ChatSession
	err = r.collection.FindOne(ctx, filter).Decode(&session)
	if err != nil {
		return nil, err
	}

	return &session, nil
}

// GetByUserID retrieves all chat sessions for a user (excluding soft-deleted)
func (r *chatSessionRepo) GetByUserID(ctx context.Context, userID string, opts *FindOptions) ([]*model.ChatSession, error) {
	objectID, err := primitive.ObjectIDFromHex(userID)
	if err != nil {
		return nil, err
	}

	filter := bson.M{
		"user_id":    objectID,
		"deleted_at": nil, // Exclude soft-deleted
	}

	// Default sort by updated_at descending (most recent first)
	findOpts := options.Find().SetSort(bson.D{{Key: "updated_at", Value: -1}})

	// Apply custom options
	if opts != nil {
		if opts.Limit > 0 {
			findOpts.SetLimit(opts.Limit)
		}
		if opts.Skip > 0 {
			findOpts.SetSkip(opts.Skip)
		}
		if opts.Sort != nil {
			// Convert map to bson.D for MongoDB
			sortDoc := bson.D{}
			for k, v := range opts.Sort {
				sortDoc = append(sortDoc, bson.E{Key: k, Value: v})
			}
			findOpts.SetSort(sortDoc)
		}
	}

	cursor, err := r.collection.Find(ctx, filter, findOpts)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	var sessions []*model.ChatSession
	if err = cursor.All(ctx, &sessions); err != nil {
		return nil, err
	}

	return sessions, nil
}

// Update updates a chat session
func (r *chatSessionRepo) Update(ctx context.Context, session *model.ChatSession) (*model.ChatSession, error) {
	session.UpdatedAt = time.Now()

	filter := bson.M{"_id": session.ID}
	update := bson.M{"$set": session}

	result := r.collection.FindOneAndUpdate(
		ctx,
		filter,
		update,
		options.FindOneAndUpdate().SetReturnDocument(options.After),
	)

	if result.Err() != nil {
		return nil, result.Err()
	}

	var updated model.ChatSession
	if err := result.Decode(&updated); err != nil {
		return nil, err
	}

	return &updated, nil
}

// Delete soft deletes a chat session
func (r *chatSessionRepo) Delete(ctx context.Context, id string) error {
	objectID, err := primitive.ObjectIDFromHex(id)
	if err != nil {
		return err
	}

	now := time.Now()
	filter := bson.M{"_id": objectID}
	update := bson.M{"$set": bson.M{"deleted_at": now}}

	result, err := r.collection.UpdateOne(ctx, filter, update)
	if err != nil {
		return err
	}

	if result.MatchedCount == 0 {
		return mongo.ErrNoDocuments
	}

	return nil
}

// HardDelete permanently deletes a chat session
func (r *chatSessionRepo) HardDelete(ctx context.Context, id string) error {
	objectID, err := primitive.ObjectIDFromHex(id)
	if err != nil {
		return err
	}

	filter := bson.M{"_id": objectID}
	result, err := r.collection.DeleteOne(ctx, filter)
	if err != nil {
		return err
	}

	if result.DeletedCount == 0 {
		return errors.New("session not found")
	}

	return nil
}

// CountByUserID counts chat sessions for a user (excluding soft-deleted)
func (r *chatSessionRepo) CountByUserID(ctx context.Context, userID string) (int64, error) {
	objectID, err := primitive.ObjectIDFromHex(userID)
	if err != nil {
		return 0, err
	}

	filter := bson.M{
		"user_id":    objectID,
		"deleted_at": nil,
	}

	count, err := r.collection.CountDocuments(ctx, filter)
	if err != nil {
		return 0, err
	}

	return count, nil
}
