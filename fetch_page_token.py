import os
import sys

import requests

user_token = os.environ.get("FB_USER_TOKEN")
if not user_token:
    sys.exit("FB_USER_TOKEN is not set. Export it in your shell or .env before running this script.")

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
