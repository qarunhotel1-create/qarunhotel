import os
import re

def update_prices_in_file(file_path):
    # Define the price mappings
    price_mapping = {
        'single: 500': 'single: 600',
        'double: 700': 'double: 800',
        'triple: 900': 'triple: 1000',
        "single:500": "single:600",
        "double:700": "double:800",
        "triple:900": "triple:1000",
        "'single': 500": "'single': 600",
        "'double': 700": "'double': 800",
        "'triple': 900": "'triple': 1000",
        '"single": 500': '"single": 600',
        '"double": 700': '"double": 800',
        '"triple": 900': '"triple": 1000',
        'single=500': 'single=600',
        'double=700': 'double=800',
        'triple=900': 'triple=1000',
        'single = 500': 'single = 600',
        'double = 700': 'double = 800',
        'triple = 900': 'triple = 1000',
    }

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        modified = False
        for old, new in price_mapping.items():
            if old in content:
                content = content.replace(old, new)
                modified = True

        if modified:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            return True
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
    
    return False

def main():
    # Define directories to search
    base_dir = os.path.join(os.path.dirname(__file__), 'hotel')
    target_dirs = [
        os.path.join(base_dir, 'static'),
        os.path.join(base_dir, 'templates'),
        os.path.join(base_dir, 'routes'),
        os.path.join(base_dir, 'models'),
        os.path.join(base_dir, 'utils')
    ]

    # File extensions to process
    extensions = ('.js', '.py', '.html', '.jinja2', '.jinja')
    updated_files = 0

    print("Starting price update process...")
    
    for target_dir in target_dirs:
        if not os.path.exists(target_dir):
            print(f"Directory not found: {target_dir}")
            continue
            
        print(f"\nSearching in: {target_dir}")
        
        for root, _, files in os.walk(target_dir):
            for file in files:
                if file.endswith(extensions):
                    file_path = os.path.join(root, file)
                    if update_prices_in_file(file_path):
                        print(f"Updated: {file_path}")
                        updated_files += 1

    print(f"\nUpdate complete! {updated_files} files were modified.")
    print("\nIMPORTANT: Please clear your browser cache and restart the server for changes to take effect.")

if __name__ == "__main__":
    main()
