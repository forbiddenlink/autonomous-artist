import requests

# Your user token with pages_show_list and business_management permissions
user_token = "EAARPkdFQtQkBQdZAgEIwZAvQbxKGJmcFDPKHnLEnvhCnpTO0dZCee0b0cJyb4QTlGVFWTwFpZAKURU7WDyAah5l5jsrTt98AyKHtmj32aetjfn56tCNc8vPB2kt2FRgrHZBg06NJhBwMvSMI0nV89qOIBKxtyYo49njIM7GofsutGqyqIP6994ZBqyRESQJtjkgayIk5QY3YhpKQV0W7WKnBz0XdxzjsGbb1aOSC33NpllvPZC6nZAX221GugRXTYwczFCqyY8GJeAZDZD"

# Known page ID
page_id = "993674647151431"

print("🔄 Attempting to get page access token...")
print(f"   Page ID: {page_id}")
print()

# Try method 1: Direct page token request
url = f"https://graph.facebook.com/v19.0/{page_id}?fields=access_token&access_token={user_token}"

try:
    response = requests.get(url)
    data = response.json()
    
    if 'access_token' in data:
        print("=" * 60)
        print("✅ SUCCESS! Found page token!")
        print("=" * 60)
        print(f"FB_PAGE_ID={page_id}")
        print(f"FB_PAGE_ACCESS_TOKEN={data['access_token']}")
        print("=" * 60)
        print("\nCopy the above lines to your .env file!")
    else:
        print("❌ Method 1 failed. Error:")
        print(data)
        print("\n🔄 Trying alternative method...")
        
        # Method 2: Try getting all pages with different endpoint
        url2 = f"https://graph.facebook.com/v19.0/me/accounts?access_token={user_token}"
        response2 = requests.get(url2)
        data2 = response2.json()
        
        if 'data' in data2 and len(data2['data']) > 0:
            print(f"✅ Found {len(data2['data'])} page(s):")
            for page in data2['data']:
                print(f"\nPage: {page['name']}")
                print(f"ID: {page['id']}")
                print(f"Token: {page['access_token']}")
        else:
            print("❌ No pages found. Error:")
            print(data2)
            print("\n⚠️  Your user token may not have the 'pages_show_list' permission.")
            print("   Try regenerating the token with these permissions:")
            print("   - pages_show_list")
            print("   - pages_manage_posts")
            print("   - pages_read_engagement")
        
except Exception as e:
    print(f"❌ Error: {e}")
