import requests

# Test API
try:
    response = requests.get('http://localhost:8000/api/themes/all')
    data = response.json()
    print(f"API Status: {response.status_code}")
    print(f"Number of domains: {len(data)}")
    
    total_themes = 0
    for domain in data:
        theme_count = len(domain.get('themes', []))
        total_themes += theme_count
        print(f"  {domain['name']}: {theme_count} themes")
    
    print(f"\nTotal themes: {total_themes}")
except Exception as e:
    print(f"Error: {e}")
    print("Make sure backend is running on port 8000")