
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Post(BaseModel):
    shortcode: str
    caption: Optional[str] = None
    media_urls: List[str] = []
    posted_at: Optional[datetime] = None

class Profile(BaseModel):
    username: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    external_url: Optional[str] = None
    profile_pic_url: Optional[str] = None
    followers: Optional[int] = None
    following: Optional[int] = None
    latest_posts: List[Post] = []
