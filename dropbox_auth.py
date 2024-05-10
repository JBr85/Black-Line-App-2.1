import requests
import json
import base64

# Your app's credentials
APP_KEY = 'kaug5l776krcnjz'
APP_SECRET = 'vwukil5qgbhdaaw'
REFRESH_TOKEN = 'CckLMa9ztHQAAAAAAAAAAWtdYhV0BsGzM2HhepV8l9oI0HzP3dwN9ZDfBGvWkTw-'

# Create Basic Auth header
BASIC_AUTH = base64.b64encode(f'{APP_KEY}:{APP_SECRET}'.encode()).decode()

headers = {
    'Authorization': f"Basic {BASIC_AUTH}",
    'Content-Type': 'application/x-www-form-urlencoded',
}

data = f'refresh_token={REFRESH_TOKEN}&grant_type=refresh_token'

response = requests.post('https://api.dropboxapi.com/oauth2/token',
                         data=data,
                         headers=headers)

new_tokens = json.loads(response.text)
new_access_token = new_tokens['access_token']

print(f"New Access Token: {new_access_token}")
