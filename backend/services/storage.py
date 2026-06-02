import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from typing import Optional
import uuid

class StorageService:
    def __init__(self):
        self.s3_client = None
        self.bucket_name = os.getenv("S3_BUCKET_NAME", "blueprint-reader-files")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.use_local = os.getenv("USE_LOCAL_STORAGE", "false").lower() == "true"
        
        if not self.use_local:
            try:
                self.s3_client = boto3.client(
                    's3',
                    region_name=self.region,
                    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
                )
            except NoCredentialsError:
                print("Warning: AWS credentials not found, falling back to local storage")
                self.use_local = True
        
        if self.use_local:
            self.local_storage_path = os.getenv("LOCAL_STORAGE_PATH", "./storage")
            os.makedirs(self.local_storage_path, exist_ok=True)
    
    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        """Upload file to storage and return the file path/key"""
        
        # Generate unique filename
        file_extension = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_key = f"uploads/{unique_filename}"
        
        if self.use_local:
            # Save to local storage
            file_path = os.path.join(self.local_storage_path, unique_filename)
            with open(file_path, "wb") as f:
                f.write(file_content)
            return file_path
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=file_content,
                ContentType=content_type
            )
            return f"s3://{self.bucket_name}/{file_key}"
        except ClientError as e:
            print(f"Error uploading to S3: {e}")
            # Fallback to local storage
            return await self.upload_file(file_content, filename, content_type)
    
    async def download_file(self, file_key: str) -> bytes:
        """Download file from storage"""
        
        if self.use_local or file_key.startswith("s3://") == False:
            # Local storage
            file_path = file_key
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.local_storage_path, os.path.basename(file_key))
            
            with open(file_path, "rb") as f:
                return f.read()
        
        try:
            # Extract key from s3://bucket/key format
            if file_key.startswith("s3://"):
                parts = file_key.replace("s3://", "").split("/", 1)
                bucket = parts[0]
                key = parts[1] if len(parts) > 1 else ""
            else:
                bucket = self.bucket_name
                key = file_key
            
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
        except ClientError as e:
            print(f"Error downloading from S3: {e}")
            raise
    
    async def delete_file(self, file_key: str) -> bool:
        """Delete file from storage"""
        
        if self.use_local or file_key.startswith("s3://") == False:
            # Local storage
            file_path = file_key
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.local_storage_path, os.path.basename(file_key))
            
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        
        try:
            if file_key.startswith("s3://"):
                parts = file_key.replace("s3://", "").split("/", 1)
                bucket = parts[0]
                key = parts[1] if len(parts) > 1 else ""
            else:
                bucket = self.bucket_name
                key = file_key
            
            self.s3_client.delete_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            print(f"Error deleting from S3: {e}")
            return False
    
    async def get_file_url(self, file_key: str, expires_in: int = 3600) -> str:
        """Get presigned URL for file"""
        
        if self.use_local:
            # For local storage, return a relative path
            return f"/api/v1/storage/{os.path.basename(file_key)}"
        
        try:
            if file_key.startswith("s3://"):
                parts = file_key.replace("s3://", "").split("/", 1)
                bucket = parts[0]
                key = parts[1] if len(parts) > 1 else ""
            else:
                bucket = self.bucket_name
                key = file_key
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None

# Global storage service instance
storage_service = StorageService()
