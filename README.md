# Discord Account Cleaner

A powerful and configurable Python script for cleaning Discord account data. This tool helps you manage your Discord account by automatically handling various account-related tasks like leaving servers, cleaning DMs, managing relationships, and more.

## Showcase

  ![image](https://github.com/user-attachments/assets/84fcf633-a2ec-43a3-826d-a6193c1cde10)

## Features

- 🔄 Set account language to English (US)
- 🚪 Leave or delete servers (auto-detects owner status)
- 💬 Clean direct message channels
- 👥 Remove friends and manage friend requests
- 🚫 Unblock all blocked users
- ⛔ Decline pending message requests
- 🔗 Remove account connections
- 🌐 Proxy support for enhanced privacy
- ⏱️ Configurable delay between actions
- 🎨 Colored console output for better visibility
- 📊 Detailed success/failure tracking
- 📁 Organized output with timestamp-based folders

## Requirements

- Python 3.6+
- Required packages:
  - tls_client
  - colorama
  - json (built-in)
  - time (built-in)
  - os (built-in)
  - random (built-in)

## Setup

1. Clone the repository or download the script
2. Install required packages:
```bash
pip install tls_client colorama
```
3. Create a `config.json` file with your desired settings:
```json
{
    "delay": 1,
    "proxies": false,
    "set_language": true,
    "unblock_users": true,
    "leave_servers": true,
    "clean_dms": true,
    "decline_message_requests": true,
    "remove_friends": true,
    "decline_friend_requests": true,
    "cancel_outgoing_requests": true,
    "remove_connections": true
}
```
4. Create a `tokens.txt` file with your Discord tokens (one per line)
5. If using proxies, create a `proxies.txt` file with your proxy list

## Proxy Support

The script supports both authenticated and non-authenticated proxies in the following formats:
- Non-authenticated: `ip:port`
- Authenticated: `username:password@ip:port`

## Usage

1. Configure your settings in `config.json`
2. Add your Discord tokens to `tokens.txt`
3. (Optional) Add proxies to `proxies.txt` if enabled
4. Run the script:
```bash
python main.py
```

## Output

The script creates an output directory with the current timestamp containing:
- `success.txt`: Successfully processed tokens
- `failed.txt`: Tokens that failed during processing
- `invalid.txt`: Invalid tokens

## Rate Limiting

The script includes built-in rate limit handling:
- Automatically detects Discord rate limits
- Waits for the specified retry-after period
- Retries the action automatically
- Rotates proxies (if enabled) when rate limited

## Error Handling

- Comprehensive error handling for all API requests
- Proxy rotation on connection errors
- Detailed console output for debugging
- Failed operations tracking

## Safety Features

- Token validation before processing
- Configurable delays to prevent rate limiting
- Proxy support for additional security
- Separate success/failure logging

## Legal Notice

This tool is for educational purposes only. Users are responsible for ensuring compliance with Discord's Terms of Service and API guidelines.
