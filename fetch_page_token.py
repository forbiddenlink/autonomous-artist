import requests

user_token = "EAARPkdFQtQkBQXlB9MMBbIoa5GByNLVh9wExZAWbeUo5GQgwwoB0gTrgJkfA8LeDZB5p7bzaMcNy5lujVGs15nJijP6eO4sx1YYs0LwDEg9YRZByUmpwAFcFjeFiUhLRPhe4j7NDuQDyZAQrHV269ZBt1fadtl3Dzsqi3rCxh0cT8laWhMnhiLuqaq8TZCJSKDPrZAT3Su0hRWzZBjBP4Yg2GzByOevs6pAZD"

print("🔄 Fetching your Facebook pages...")
url = f"https://graph.facebook.com/v19.0/me/accounts?access_token={user_token}"

try:
    response = requests.get(url)
    data = response.json()
    
    if 'data' in data:
        print(f"\n✅ Found {len(data['data'])} page(s):\n")
        for page in data['data']:
            print(f"📄 Page Name: {page['name']}")
            print(f"   Page ID: {page['id']}")
            print(f"   Access Token: {page['access_token']}")
            print()
            
            if 'Aria' in page['name'] or page['id'] == '993674647151431':
                print("=" * 60)
                print("🎨 FOUND ARIA'S PAGE! Copy these to your .env file:")
                print("=" * 60)
                print(f"FB_PAGE_ID={page['id']}")
                print(f"FB_PAGE_ACCESS_TOKEN={page['access_token']}")
                print("=" * 60)
    else:
        print("❌ Error response:")
        print(data)
        
except Exception as e:
    print(f"❌ Error: {e}")
