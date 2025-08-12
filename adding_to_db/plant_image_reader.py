import os
import cv2
import numpy as np
import psycopg2
from PIL import Image
import matplotlib.pyplot as plt

class PlantImageReader:
    def __init__(self, db_config):
        """Initialize with database configuration"""
        self.db_config = db_config
    
    def get_db_connection(self):
        """Establish database connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            print(f"Database connection failed: {e}")
            return None

    def read_from_db(self, limit=5):
        """Read image paths from database"""
        conn = self.get_db_connection()
        if not conn:
            return []
            
        try:
            with conn.cursor() as cur:
                # Get sample images from each category using separate queries
                samples = []
                
                # Get healthy leaves
                cur.execute("SELECT file_path, label FROM healthy_leaves LIMIT %s", (limit,))
                samples.extend(cur.fetchall())
                
                # Get leaf rust
                cur.execute("SELECT file_path, label FROM leaf_rust LIMIT %s", (limit,))
                samples.extend(cur.fetchall())
                
                # Get loose smut
                cur.execute("SELECT file_path, label FROM loose_smut LIMIT %s", (limit,))
                samples.extend(cur.fetchall())
                
                return samples
                
        except Exception as e:
            print(f"Database error: {e}")
            return []
        finally:
            conn.close()

    def load_image(self, file_path):
        """Load image from file path"""
        try:
            img = cv2.imread(file_path)
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if img is not None else None
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None

    def display_samples(self, num_samples=3):
        """Display sample images from each category"""
        samples = self.read_from_db(num_samples)
        if not samples:
            print("No images found in database!")
            return
        
        plt.figure(figsize=(15, 5))
        for i, (file_path, label) in enumerate(samples):
            img = self.load_image(file_path)
            if img is not None:
                plt.subplot(1, len(samples), i+1)
                plt.imshow(img)
                plt.title(f"{label}\n{os.path.basename(file_path)}")
                plt.axis('off')
        
        plt.tight_layout()
        plt.show()

    def analyze_image(self, file_path):
        """Perform basic image analysis"""
        img = self.load_image(file_path)
        if img is None:
            return None
            
        # Convert to HSV for color analysis
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        
        # Calculate basic statistics
        return {
            'original_size': img.shape,
            'average_color_rgb': np.mean(img, axis=(0,1)).astype(int),
            'dominant_hue': int(np.mean(hsv[:,:,0])),  # Hue channel (0-180)
            'brightness': np.mean(hsv[:,:,2]).astype(int),  # Value channel (0-255)
            'color_variance': np.var(img).astype(int)
        }

    def preprocess_image(self, img, target_size=(256, 256)):
        """Basic preprocessing for CNN input"""
        img = cv2.resize(img, target_size)
        return img / 255.0  # Normalize to [0,1]

if __name__ == "__main__":
    # Database configuration (UPDATE THESE VALUES)
    DB_CONFIG = {
        "host": "localhost",
        "database": "wheat_disease_db",
        "user": "postgres",
        "password": "noman1338",  # Change this
        "port": "5432"
    }
    
    # Initialize the reader
    reader = PlantImageReader(DB_CONFIG)
    
    # 1. Display sample images
    print("\nDisplaying sample images from database...")
    reader.display_samples()
    
    # 2. Analyze a specific image
    print("\nAnalyzing a sample image...")
    sample_images = reader.read_from_db(1)
    
    if sample_images:
        file_path, label = sample_images[0]
        analysis = reader.analyze_image(file_path)
        
        print(f"\nAnalysis for {os.path.basename(file_path)} ({label}):")
        for k, v in analysis.items():
            print(f"{k:>20}: {v}")
        
        # 3. Show preprocessing example
        img = reader.load_image(file_path)
        processed = reader.preprocess_image(img)
        print(f"\nPreprocessed image shape: {processed.shape}")
        print(f"Pixel range: {processed.min():.2f}-{processed.max():.2f}")
