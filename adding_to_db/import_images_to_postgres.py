import os
import psycopg2
from PIL import Image
from tqdm import tqdm

# Database configuration (Update these values)
DB_CONFIG = {
    "host": "localhost",
    "database": "wheat_disease_db",
    "user": "postgres",
    "password": "noman1338",  # Change to your PostgreSQL password
    "port": "5432"
}

# Get current directory path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
FOLDER_MAPPING = {
    "healthy": {
        "path": os.path.join(CURRENT_DIR, "renamed_healthy"),
        "table": "healthy_leaves"
    },
    "rust": {
        "path": os.path.join(CURRENT_DIR, "renamed_Wheat_Leaf_Rust"),
        "table": "leaf_rust"
    },
    "smut": {
        "path": os.path.join(CURRENT_DIR, "renamed_Wheat_Loose_Smut"),
        "table": "loose_smut"
    }
}
def get_image_metadata(file_path):
    """Extracts metadata from image files"""
    try:
        with Image.open(file_path) as img:
            width, height = img.size
        return {
            "file_name": os.path.basename(file_path),
            "file_path": file_path,
            "file_size_kb": round(os.path.getsize(file_path) / 1024, 2),
            "resolution": f"{width}x{height}",
            "width": width,
            "height": height
        }
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def process_images(conn, folder_path, table_name):
    """Process all images in a folder and insert to database"""
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return

    image_files = [f for f in os.listdir(folder_path) 
                  if f.lower().endswith('.jpg')]
    
    if not image_files:
        print(f"No JPG images found in {folder_path}")
        return

    print(f"\nProcessing {len(image_files)} images for {table_name}...")
    
    with tqdm(total=len(image_files), desc=f"Importing to {table_name}") as pbar:
        for filename in image_files:
            file_path = os.path.join(folder_path, filename)
            metadata = get_image_metadata(file_path)
            
            if metadata:
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            f"INSERT INTO {table_name} "
                            "(file_name, file_path, file_size_kb, resolution, width, height) "
                            "VALUES (%s, %s, %s, %s, %s, %s)",
                            (
                                metadata['file_name'],
                                metadata['file_path'],
                                metadata['file_size_kb'],
                                metadata['resolution'],
                                metadata['width'],
                                metadata['height']
                            )
                        )
                        conn.commit()
                except Exception as e:
                    conn.rollback()
                    print(f"Error inserting {filename}: {e}")
            
            pbar.update(1)

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Connected to PostgreSQL database successfully!")
        
        for category, config in FOLDER_MAPPING.items():
            process_images(conn, config['path'], config['table'])
                
    except Exception as e:
        print(f"Database connection failed: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    main()
