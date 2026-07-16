from dotenv import load_dotenv
import os

load_dotenv

class Settings:
    def __init__(self):
        # AI
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
        
        
        # AWS
        self.AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
        self.AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
        self.AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
        
        # External APIs
        self.REMOVE_BG_API_KEY = os.getenv("REMOVE_BG_API_KEY")
        
         # Storage folders
        self.S3_AVATAR_FOLDER = os.getenv("S3_AVATAR_FOLDER", "avatars")
        self.S3_WARDROBE_FOLDER = os.getenv("S3_WARDROBE_FOLDER", "wardrobe")
        
        # App
        self.PORT = int(os.getenv("PORT", 8000))
        self.ENV = os.getenv("ENV", "development")
        self.MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", 10))
        
        # Image validation
        self.MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", 10))
        self.MIN_IMAGE_DIMENSION = int(os.getenv("MIN_IMAGE_DIMENSION", 300))
        self.MAX_IMAGE_DIMENSION = int(os.getenv("MAX_IMAGE_DIMENSION", 6000))
        self.BLUR_THRESHOLD = float(os.getenv("BLUR_THRESHOLD", 80.0))
        
        required = {
            "OPENAI_API_KEY": self.OPENAI_API_KEY,
            "AWS_BUCKET_NAME": self.AWS_BUCKET_NAME,
            "AWS_ACCESS_KEY_ID": self.AWS_ACCESS_KEY_ID,
            "AWS_SECRET_ACCESS_KEY": self.AWS_SECRET_ACCESS_KEY,
            "REMOVE_BG_API_KEY": self.REMOVE_BG_API_KEY,
        }
        
        missing =  [k for k, v in required.items() if not v]
        if missing:
            raise RuntimeError(
                f"Missing environment variables: {', '.join(missing)}"
            )
    
settings = Settings()