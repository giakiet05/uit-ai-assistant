import uuid

from pydantic import BaseModel, EmailStr
from typing import Optional

from .user_dto import UserResponse # Use our existing User DTO as UserResponse

# ==================================
# Registration DTOs
# ==================================

class SendEmailVerificationRequest(BaseModel):
    email: EmailStr

class VerifyEmailCodeRequest(BaseModel):
    email: EmailStr
    otp: str # Assuming OTP is a 6-digit string

class CompleteRegistrationRequest(BaseModel):
    verification_token: str # A temporary token received after OTP verification
    username: str
    password: str # This will be hashed in the service layer

class ResendOTPRequest(BaseModel):
    email: EmailStr

# ==================================
# Login DTOs
# ==================================

class UserLoginRequest(BaseModel):
    identifier: str # Can be email or username
    password: str

# ==================================
# Google Setup DTOs
# ==================================

class CompleteGoogleSetupRequest(BaseModel):
    setup_token: str # A temporary token from Google OAuth process
    username: str

# ==================================
# Token Management DTOs
# ==================================

class RefreshRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    access_token: str
    refresh_token: str

# ==================================
# Response DTOs
# ==================================

class AuthResponse(BaseModel):
    user: UserResponse # Uses the User DTO from user_dto.py
    access_token: str
    refresh_token: str
    token_type: str = "bearer" # Default token type

class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer" # Default token type

# DTO for the data encoded in the JWT
class TokenPayload(BaseModel):
    sub: Optional[uuid.UUID] = None
