from pydantic import BaseModel

# Signup request body
class SignupRequest(BaseModel):
    username: str
    email: str
    password: str

# Login request body
class LoginRequest(BaseModel):
    username: str
    password: str

class URLTranscriptionRequest(BaseModel):
    file_url: str
    user_id: int = 0