package model

import (
	"time"

	"go.mongodb.org/mongo-driver/bson/primitive"
)

// AuthProvider defines the source of user authentication.
type AuthProvider string

const (
	ProviderLocal  AuthProvider = "local"  // Registered with email and password
	ProviderGoogle AuthProvider = "google" // Registered via Google OAuth
)

// User represents a user in the UIT AI Assistant system
type User struct {
	// Identity
	ID       primitive.ObjectID `bson:"_id,omitempty" json:"id"`
	Email    string             `bson:"email" json:"email"`          // Unique, primary login
	Username string             `bson:"username" json:"username"`    // Unique, display name
	Password string             `bson:"password,omitempty" json:"-"` // Hashed (bcrypt)

	// Auth
	Provider   AuthProvider `bson:"provider" json:"provider"`
	ProviderID string       `bson:"provider_id,omitempty" json:"-"` // Google ID
	IsVerified bool         `bson:"is_verified" json:"is_verified"`

	// Role
	Role Role `bson:"role" json:"role"` // "user" | "admin"

	// Profile
	Avatar *Image `bson:"avatar,omitempty" json:"avatar,omitempty"` // Avatar image

	// Settings
	Settings UserSettings `bson:"settings" json:"settings"`

	// Status
	IsActive  bool       `bson:"is_active" json:"is_active"`
	BanUntil  *time.Time `bson:"ban_until,omitempty" json:"ban_until,omitempty"`
	BanReason *string    `bson:"ban_reason,omitempty" json:"ban_reason,omitempty"` // nil if not banned

	// Timestamps
	CreatedAt time.Time  `bson:"created_at" json:"created_at"`
	UpdatedAt time.Time  `bson:"updated_at" json:"updated_at"`
	DeletedAt *time.Time `bson:"deleted_at,omitempty" json:"deleted_at,omitempty"` // Soft delete
}

// Role defines user permission level
type Role string

const (
	UserRole  Role = "user"
	AdminRole Role = "admin"
)

// UserSettings contains user preference settings
type UserSettings struct {
	Language          string `bson:"language" json:"language"`                       // "vi" | "en"
	Theme             string `bson:"theme" json:"theme"`                             // "light" | "dark"
	NotifyNewFeatures bool   `bson:"notify_new_features" json:"notify_new_features"` // Notify about new features
}

// Theme constants
const (
	ThemeLight = "light"
	ThemeDark  = "dark"
)

// Language constants
const (
	LanguageVI = "vi"
	LanguageEN = "en"
)

// NewDefaultSettings returns default user settings
func NewDefaultSettings() UserSettings {
	return UserSettings{
		Language:          LanguageVI,
		Theme:             ThemeLight,
		NotifyNewFeatures: true,
	}
}

// IsBanned checks if user is currently banned
func (u *User) IsBanned() bool {
	if !u.IsActive {
		return true
	}
	if u.BanUntil != nil && u.BanUntil.After(time.Now()) {
		return true
	}
	return false
}

// IsAdmin checks if user has admin role
func (u *User) IsAdmin() bool {
	return u.Role == AdminRole
}

// CloneUser creates a deep copy of a user
func CloneUser(u *User) *User {
	if u == nil {
		return nil
	}

	clone := *u // shallow copy

	// Deep copy DeletedAt
	if u.DeletedAt != nil {
		t := *u.DeletedAt
		clone.DeletedAt = &t
	}

	// Deep copy BanUntil
	if u.BanUntil != nil {
		t := *u.BanUntil
		clone.BanUntil = &t
	}

	// Deep copy BanReason
	if u.BanReason != nil {
		s := *u.BanReason
		clone.BanReason = &s
	}

	// Deep copy Avatar
	if u.Avatar != nil {
		img := *u.Avatar
		clone.Avatar = &img
	}

	// Settings is value type, already copied

	return &clone
}
