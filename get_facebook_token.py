"""
Helper script to get Facebook Page Access Token
Follow the instructions printed by this script.
"""

print("""
╔════════════════════════════════════════════════════════════╗
║          GET FACEBOOK PAGE ACCESS TOKEN                    ║
╚════════════════════════════════════════════════════════════╝

Since the Graph API Explorer is giving errors, here's the manual method:

STEP 1: Get Your App ID
─────────────────────────
1. Go to: https://developers.facebook.com/apps
2. Click on your "Aria Bot" app
3. Look at the top - you'll see "App ID: 1234567890..." (a number)
4. Copy that number

STEP 2: Generate User Access Token
─────────────────────────────────────
1. Open this URL in your browser (replace YOUR_APP_ID):

https://www.facebook.com/v19.0/dialog/oauth?client_id=YOUR_APP_ID&redirect_uri=https://www.facebook.com/connect/login_success.html&scope=pages_manage_posts,pages_read_engagement

2. Replace YOUR_APP_ID with your actual App ID
3. Visit that URL - you'll be asked to authorize
4. After authorizing, you'll be redirected to a URL that looks like:
   https://www.facebook.com/connect/login_success.html#access_token=EAAxxxxx...
5. Copy everything after "access_token=" (the EAAxxxx part)

STEP 3: Exchange for Page Token
─────────────────────────────────
Now run this script again with your tokens:

python3 get_facebook_token.py YOUR_APP_ID YOUR_USER_TOKEN

""")

import sys
if len(sys.argv) == 3:
    import requests
    app_id = sys.argv[1]
    user_token = sys.argv[2]
    
    print("\n🔄 Fetching your pages...")
    
    # Get pages
    url = f"https://graph.facebook.com/v19.0/me/accounts?access_token={user_token}"
    response = requests.get(url)
    data = response.json()
    
    if 'data' in data and len(data['data']) > 0:
        print("\n✅ Found your pages:\n")
        for page in data['data']:
            print(f"📄 Page: {page['name']}")
            print(f"   ID: {page['id']}")
            print(f"   Token: {page['access_token'][:50]}...")
            print()
            
            if 'Aria' in page['name']:
                print(f"\n🎨 Found Aria's page! Add these to your .env:\n")
                print(f"FB_PAGE_ID={page['id']}")
                print(f"FB_PAGE_ACCESS_TOKEN={page['access_token']}")
                print()
    else:
        print("❌ Error:", data)
