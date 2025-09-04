"""
Local Storage Manager for Camera Service
Handles local image storage with queue management and automatic cleanup.
"""
import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Optional
import logging

class LocalStorageManager:
    def __init__(self, max_images: int = 50, storage_dir: str = "images"):
        self.max_images = max_images
        self.storage_dir = storage_dir
        self.logger = logging.getLogger(__name__)
        
        # Ensure storage directory exists
        os.makedirs(storage_dir, exist_ok=True)
        
        # Load existing images
        self.images = self._load_images()
        
        # Track upload status separately
        self.uploaded_images = set()  # Set of filenames that have been uploaded
        self.upload_status_file = os.path.join(storage_dir, "upload_status.json")
        self._load_upload_status()
    
    def _load_images(self) -> List[Dict]:
        """Load existing images from storage directory."""
        images = []
        
        if not os.path.exists(self.storage_dir):
            return images
        
        for filename in os.listdir(self.storage_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                filepath = os.path.join(self.storage_dir, filename)
                try:
                    stat = os.stat(filepath)
                    images.append({
                        'filename': filename,
                        'filepath': filepath,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime),
                        'modified': datetime.fromtimestamp(stat.st_mtime)
                    })
                except OSError as e:
                    self.logger.error(f"Error reading file {filename}: {e}")
        
        # Sort by creation time (newest first)
        images.sort(key=lambda x: x['created'], reverse=True)
        return images
    
    def _load_upload_status(self):
        """Load upload status from file."""
        try:
            if os.path.exists(self.upload_status_file):
                with open(self.upload_status_file, 'r') as f:
                    data = json.load(f)
                    self.uploaded_images = set(data.get('uploaded_images', []))
                    self.logger.info(f"Loaded upload status: {len(self.uploaded_images)} uploaded images")
        except Exception as e:
            self.logger.error(f"Error loading upload status: {e}")
            self.uploaded_images = set()
    
    def _save_upload_status(self):
        """Save upload status to file."""
        try:
            data = {
                'uploaded_images': list(self.uploaded_images),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.upload_status_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving upload status: {e}")
    
    def mark_as_uploaded(self, filename: str):
        """Mark an image as uploaded."""
        self.uploaded_images.add(filename)
        self._save_upload_status()
        self.logger.info(f"Marked as uploaded: {filename}")
    
    def is_uploaded(self, filename: str) -> bool:
        """Check if an image has been uploaded."""
        return filename in self.uploaded_images
    
    def add_image(self, filepath: str) -> bool:
        """Add image to local storage, managing queue size."""
        try:
            if not os.path.exists(filepath):
                self.logger.error(f"File does not exist: {filepath}")
                return False
            
            filename = os.path.basename(filepath)
            stat = os.stat(filepath)
            
            image_info = {
                'filename': filename,
                'filepath': filepath,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime)
            }
            
            # Add to beginning of list (newest first)
            self.images.insert(0, image_info)
            
            # Remove excess images
            self._manage_queue_size()
            
            self.logger.info(f"Added image to local storage: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding image to storage: {e}")
            return False
    
    def _manage_queue_size(self):
        """Manage queue size by removing oldest images."""
        while len(self.images) > self.max_images:
            oldest_image = self.images.pop()  # Remove last (oldest) image
            
            try:
                # Move to backup directory or delete
                backup_dir = os.path.join(self.storage_dir, "backup")
                os.makedirs(backup_dir, exist_ok=True)
                
                backup_path = os.path.join(backup_dir, oldest_image['filename'])
                shutil.move(oldest_image['filepath'], backup_path)
                
                self.logger.info(f"Moved old image to backup: {oldest_image['filename']}")
                
            except Exception as e:
                self.logger.error(f"Error managing queue size: {e}")
                # If backup fails, just delete the file
                try:
                    os.remove(oldest_image['filepath'])
                    self.logger.info(f"Deleted old image: {oldest_image['filename']}")
                except Exception as delete_error:
                    self.logger.error(f"Error deleting old image: {delete_error}")
    
    def get_images(self) -> List[Dict]:
        """Get list of all images in storage."""
        return self.images.copy()
    
    def get_image_count(self) -> int:
        """Get current number of images in storage."""
        return len(self.images)
    
    def remove_image(self, filename: str) -> bool:
        """Remove image from storage."""
        try:
            for i, image in enumerate(self.images):
                if image['filename'] == filename:
                    # Remove from list
                    removed_image = self.images.pop(i)
                    
                    # Delete file
                    if os.path.exists(removed_image['filepath']):
                        os.remove(removed_image['filepath'])
                    
                    self.logger.info(f"Removed image from storage: {filename}")
                    return True
            
            self.logger.warning(f"Image not found in storage: {filename}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error removing image: {e}")
            return False
    
    def get_storage_info(self) -> Dict:
        """Get storage information."""
        total_size = sum(img['size'] for img in self.images)
        
        return {
            'total_images': len(self.images),
            'max_images': self.max_images,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'storage_dir': self.storage_dir,
            'oldest_image': self.images[-1]['created'].isoformat() if self.images else None,
            'newest_image': self.images[0]['created'].isoformat() if self.images else None
        }
    
    def cleanup_backup(self, max_backup_age_days: int = 30):
        """Clean up old backup files."""
        backup_dir = os.path.join(self.storage_dir, "backup")
        
        if not os.path.exists(backup_dir):
            return
        
        cutoff_date = datetime.now().timestamp() - (max_backup_age_days * 24 * 60 * 60)
        
        try:
            for filename in os.listdir(backup_dir):
                filepath = os.path.join(backup_dir, filename)
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    if file_time < cutoff_date:
                        os.remove(filepath)
                        self.logger.info(f"Cleaned up old backup file: {filename}")
        except Exception as e:
            self.logger.error(f"Error cleaning up backup files: {e}")
    
    def get_upload_queue(self) -> List[Dict]:
        """Get images that need to be uploaded (only pending images)."""
        return [img for img in self.images if not self.is_uploaded(img['filename'])]
    
    def get_uploaded_count(self) -> int:
        """Get count of uploaded images."""
        return len(self.uploaded_images)
