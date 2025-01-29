import tls_client
import json
import time
import os
from colorama import Fore, init
import random

init(autoreset=True)

def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"{Fore.RED}Error: config.json not found!")
        print(f"{Fore.YELLOW}Please create a config.json file with the following structure:")
        print(f"{Fore.YELLOW}{json.dumps({
            'delay': 1,
            'proxies': False,
            'set_language': True,
            'set_dark_mode': True,  # New config option
            'unblock_users': True,
            'leave_servers': True,
            'clean_dms': True,
            'decline_message_requests': True,
            'remove_friends': True,
            'decline_friend_requests': True,
            'cancel_outgoing_requests': True
        }, indent=4)}")
        exit(1)
    except json.JSONDecodeError:
        print(f"{Fore.RED}Error: config.json is not a valid JSON file!")
        exit(1)

def load_proxies():
    try:
        with open('input/proxies.txt', 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
            if not proxies:
                print(f"{Fore.RED}Error: proxies.txt is empty!")
                exit(1)
            return proxies
    except FileNotFoundError:
        print(f"{Fore.RED}Error: proxies.txt not found!")
        exit(1)

def format_proxy(proxy):
    """Format proxy string to tls_client format"""
    if '@' in proxy:
        auth, hostport = proxy.split('@')
        username, password = auth.split(':')
        host, port = hostport.split(':')
        return {
            "http": f"http://{username}:{password}@{host}:{port}",
            "https": f"http://{username}:{password}@{host}:{port}"
        }
    else:
        host, port = proxy.split(':')
        return {
            "http": f"http://{host}:{port}",
            "https": f"http://{host}:{port}"
        }

def create_output_dir():
    timestamp = time.strftime('%Y-%m-%d %H-%M-%S')
    output_dir = f'output/{timestamp}'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

class DiscordCleaner:
    def __init__(self, config):
        self.config = config
        self.proxies = load_proxies() if config.get('proxies', False) else None
        self.session = None
        self.initialize_session()

    def initialize_session(self):
        """Initialize TLS session with optional proxy"""
        self.session = tls_client.Session(
            client_identifier="chrome_120",
            random_tls_extension_order=True
        )
        
        if self.proxies:
            proxy = random.choice(self.proxies)
            try:
                self.session.proxies = format_proxy(proxy)
            except Exception as e:
                print(f"{Fore.RED}Error setting proxy: {str(e)}")
                exit(1)

        self.session.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://discord.com',
            'referer': 'https://discord.com/channels/@me',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'x-debug-options': 'bugReporterEnabled',
            'x-discord-locale': 'en-US',
            'x-super-properties': 'eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6ImVuLVVTIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEyMC4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTIwLjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiIiLCJyZWZlcnJpbmdfZG9tYWluIjoiIiwicmVmZXJyZXJfY3VycmVudCI6IiIsInJlZmVycmluZ19kb21haW5fY3VycmVudCI6IiIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjI1MDgzMiwiY2xpZW50X2V2ZW50X3NvdXJjZSI6bnVsbH0='
        }

    def handle_proxy_error(self, error):
        """Handle proxy errors by rotating to a new proxy"""
        if self.proxies:
            print(f"{Fore.YELLOW}Proxy error: {str(error)}")
            print(f"{Fore.YELLOW}Rotating to new proxy...")
            self.initialize_session()
            return True
        return False

    def make_request(self, method, url, **kwargs):
        """Make a request with proxy error handling and rate limit handling"""
        try:
            response = getattr(self.session, method)(url, **kwargs)
            
            if response.status_code == 429:
                retry_after = response.json().get('retry_after', 5)
                print(f"{Fore.YELLOW}Rate limited, waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return self.make_request(method, url, **kwargs)
                
            return response
            
        except Exception as e:
            if self.handle_proxy_error(e):
                return self.make_request(method, url, **kwargs)
            raise e

    # Update all existing methods to use make_request instead of direct session calls
    def set_language(self, token):
        """Set account language to English (United States)"""
        try:
            self.session.headers['authorization'] = token
            payload = {
                "locale": "en-US"
            }
            
            response = self.make_request('patch', 'https://discord.com/api/v9/users/@me/settings', json=payload)
            return response.status_code == 200
            
        except Exception as e:
            print(f"{Fore.RED}Error setting language: {str(e)}")
            return False

    def get_user_id(self, token):
        try:
            self.session.headers['authorization'] = token
            response = self.session.get('https://discord.com/api/v9/users/@me')
            if response.status_code == 200:
                return response.json().get('id')
            return None
        except:
            return None

    # Server Functions
    def get_guilds(self, token):
        try:
            self.session.headers['authorization'] = token
            response = self.session.get('https://discord.com/api/v9/users/@me/guilds')
            if response.status_code == 200:
                return response.json()
            
            if response.status_code == 429:
                retry_after = response.json().get('retry_after', 5)
                print(f"{Fore.YELLOW}Rate limited, waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return self.get_guilds(token)
                
            return None
        except Exception as e:
            print(f"{Fore.RED}Error getting guilds: {str(e)}")
            return None

    def delete_guild(self, token, guild_id):
        """Delete a guild (server) if owner"""
        try:
            self.session.headers['authorization'] = token
            response = self.session.post(f'https://discord.com/api/v9/guilds/{guild_id}/delete')
            
            if response.status_code == 429:
                retry_after = response.json().get('retry_after', 5)
                print(f"{Fore.YELLOW}Rate limited, waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return self.delete_guild(token, guild_id)
                
            return response.status_code == 204
            
        except Exception as e:
            print(f"{Fore.RED}Error deleting guild {guild_id}: {str(e)}")
            return False

    def leave_guild(self, token, guild_id):
        try:
            self.session.headers['authorization'] = token
            
            # Check if user is guild owner
            guild_info = self.session.get(f'https://discord.com/api/v9/guilds/{guild_id}')
            if guild_info.status_code == 200:
                guild_data = guild_info.json()
                if str(guild_data.get('owner_id')) == str(self.get_user_id(token)):
                    print(f"{Fore.YELLOW}Found owned server, attempting to delete...")
                    if self.delete_guild(token, guild_id):
                        print(f"{Fore.GREEN}Successfully deleted owned server")
                        return True
                    else:
                        print(f"{Fore.RED}Failed to delete owned server")
                        return False

            # If not owner or deletion failed, try to leave the guild
            payload = {
                "lurking": False
            }
            
            response = self.session.delete(
                f'https://discord.com/api/v9/users/@me/guilds/{guild_id}',
                json=payload
            )
            
            if response.status_code == 429:
                retry_after = response.json().get('retry_after', 5)
                print(f"{Fore.YELLOW}Rate limited, waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return self.leave_guild(token, guild_id)
                
            return response.status_code in [204, 200]
            
        except Exception as e:
            print(f"{Fore.RED}Error leaving/deleting guild {guild_id}: {str(e)}")
            return False

    # DM Functions
    def get_dms(self, token):
        self.session.headers['authorization'] = token
        response = self.session.get('https://discord.com/api/v9/users/@me/channels')
        if response.status_code == 200:
            return response.json()
        
        if response.status_code == 429:
            retry_after = response.json().get('retry_after', 5)
            print(f"{Fore.YELLOW}Rate limited, waiting {retry_after} seconds...")
            time.sleep(retry_after)
            return self.get_dms(token)
            
        return None

    def get_message_requests(self, token):
        self.session.headers['authorization'] = token
        response = self.session.get('https://discord.com/api/v9/users/@me/message-requests')
        if response.status_code == 200:
            return response.json()
            
        if response.status_code == 429:
            retry_after = response.json().get('retry_after', 5)
            print(f"{Fore.YELLOW}Rate limited, waiting {retry_after} seconds...")
            time.sleep(retry_after)
            return self.get_message_requests(token)
            
        return None

    def close_dm(self, token, channel_id):
        self.session.headers['authorization'] = token
        response = self.session.delete(f'https://discord.com/api/v9/channels/{channel_id}')
        
        if response.status_code == 429:
            retry_after = response.json().get('retry_after', 5)
            print(f"{Fore.YELLOW}Rate limited, waiting {retry_after} seconds...")
            time.sleep(retry_after)
            return self.close_dm(token, channel_id)
            
        return response.status_code == 200

    def decline_message_request(self, token, channel_id):
        self.session.headers['authorization'] = token
        response = self.session.delete(f'https://discord.com/api/v9/channels/{channel_id}/message-requests')
        
        if response.status_code == 429:
            retry_after = response.json().get('retry_after', 5)
            print(f"{Fore.YELLOW}Rate limited, waiting {retry_after} seconds...")
            time.sleep(retry_after)
            return self.decline_message_request(token, channel_id)
            
        return response.status_code == 200

    # Friends Functions
    def get_friends(self, token):
        self.session.headers['authorization'] = token
        response = self.session.get('https://discord.com/api/v9/users/@me/relationships')
        if response.status_code == 200:
            return [r for r in response.json() if r['type'] == 1]  # type 1 = friend
            
        if response.status_code == 429:
            retry_after = response.json().get('retry_after', 5)
            print(f"{Fore.YELLOW}Rate limited, waiting {retry_after} seconds...")
            time.sleep(retry_after)
            return self.get_friends(token)
            
        return None

    def get_friend_requests(self, token):
        self.session.headers['authorization'] = token
        response = self.session.get('https://discord.com/api/v9/users/@me/relationships')
        if response.status_code == 200:
            return [r for r in response.json() if r['type'] == 3]  # type 3 = incoming
            
        if response.status_code == 429:
            retry_after = response.json().get('retry_after', 5)
            print(f"{Fore.YELLOW}Rate limited, waiting {retry_after} seconds...")
            time.sleep(retry_after)
            return self.get_friend_requests(token)
            
        return None

    def get_outgoing_requests(self, token):
        self.session.headers['authorization'] = token
        response = self.session.get('https://discord.com/api/v9/users/@me/relationships')
        if response.status_code == 200:
            return [r for r in response.json() if r['type'] == 4]  # type 4 = outgoing
            
        if response.status_code == 429:
            retry_after = response.json().get('retry_after', 5)
            print(f"{Fore.YELLOW}Rate limited, waiting {retry_after} seconds...")
            time.sleep(retry_after)
            return self.get_outgoing_requests(token)
            
        return None

    def get_blocked_users(self, token):
        """Get list of blocked users"""
        self.session.headers['authorization'] = token
        response = self.session.get('https://discord.com/api/v9/users/@me/relationships')
        if response.status_code == 200:
            return [r for r in response.json() if r['type'] == 2]  # type 2 = blocked
            
        if response.status_code == 429:
            retry_after = response.json().get('retry_after', 5)
            print(f"{Fore.YELLOW}Rate limited, waiting {retry_after} seconds...")
            time.sleep(retry_after)
            return self.get_blocked_users(token)
            
        return None

    def remove_friend(self, token, user_id):
        self.session.headers['authorization'] = token
        response = self.session.delete(f'https://discord.com/api/v9/users/@me/relationships/{user_id}')
        
        if response.status_code == 429:
            retry_after = response.json().get('retry_after', 5)
            print(f"{Fore.YELLOW}Rate limited, waiting {retry_after} seconds...")
            time.sleep(retry_after)
            return self.remove_friend(token, user_id)
            
        return response.status_code == 204

    def unblock_user(self, token, user_id):
        """Unblock a user"""
        self.session.headers['authorization'] = token
        response = self.session.delete(f'https://discord.com/api/v9/users/@me/relationships/{user_id}')
        
        if response.status_code == 429:
            retry_after = response.json().get('retry_after', 5)
            print(f"{Fore.YELLOW}Rate limited, waiting {retry_after} seconds...")
            time.sleep(retry_after)
            return self.unblock_user(token, user_id)
            
        return response.status_code == 204

    def check_token(self, token):
        """Check if the token is valid by attempting to fetch user information"""
        try:
            self.session.headers['authorization'] = token
            response = self.session.get('https://discord.com/api/v9/users/@me')
            
            if response.status_code == 429:
                retry_after = response.json().get('retry_after', 5)
                print(f"{Fore.YELLOW}Rate limited, waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return self.check_token(token)
                
            return response.status_code == 200
            
        except Exception as e:
            print(f"{Fore.RED}Error checking token: {str(e)}")
            return False

    def get_connections(self, token):
        """Get all account connections"""
        try:
            self.session.headers['authorization'] = token
            response = self.make_request('get', 'https://discord.com/api/v9/users/@me/connections')
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            print(f"{Fore.RED}Error getting connections: {str(e)}")
            return None

    def remove_connection(self, token, type, account_id):
        """Remove a specific connection"""
        try:
            self.session.headers['authorization'] = token
            response = self.make_request('delete', f'https://discord.com/api/v9/users/@me/connections/{type}/{account_id}')
            return response.status_code == 204
            
        except Exception as e:
            print(f"{Fore.RED}Error removing connection: {str(e)}")
            return False

    def set_dark_mode(self, token):
        """Set account theme to dark mode"""
        try:
            self.session.headers['authorization'] = token
            payload = {
                "theme": "dark"  # Valid values: "dark" or "light"
            }
            
            response = self.make_request('patch', 'https://discord.com/api/v9/users/@me/settings', json=payload)
            return response.status_code == 200
            
        except Exception as e:
            print(f"{Fore.RED}Error setting dark mode: {str(e)}")
            return False

    def process_token(self, token):
        try:
            email = token.split(':')[0]
            token = token.split(':')[-1]
            
            print(f"\n{Fore.YELLOW}Processing token: {token[:25]}...")
            
            # Check if token is valid before proceeding
            if not self.check_token(token):
                print(f"{Fore.RED}Token is invalid!")
                return False

            # Set Dark Mode if enabled in config
            if self.config.get('set_dark_mode', False):
                print(f"\n{Fore.CYAN}Setting dark mode...")
                if self.set_dark_mode(token):
                    print(f"{Fore.GREEN}Successfully set dark mode")
                else:
                    print(f"{Fore.RED}Failed to set dark mode")

            # Set Language to English (US)
            if self.config['set_language']:
                print(f"\n{Fore.CYAN}Setting language to English (US)...")
                if self.set_language(token):
                    print(f"{Fore.GREEN}Successfully set language to English (US)")
                else:
                    print(f"{Fore.RED}Failed to set language")
            
            # Leave/Delete Servers
            if self.config['leave_servers']:
                print(f"\n{Fore.CYAN}Processing Servers...")
                guilds = self.get_guilds(token)
                if guilds:
                    print(f"{Fore.GREEN}Found {len(guilds)} servers")
                    for guild in guilds:
                        guild_name = guild.get('name', 'Unknown Server')
                        if self.leave_guild(token, guild['id']):
                            print(f"{Fore.GREEN}Successfully processed server: {guild_name}")
                        else:
                            print(f"{Fore.RED}Failed to process server: {guild_name}")
                        time.sleep(2)
                else:
                    print(f"{Fore.YELLOW}No servers found")
            
            # Process DMs
            if self.config['clean_dms']:
                print(f"\n{Fore.CYAN}Cleaning DMs...")
                dms = self.get_dms(token)
                if dms:
                    print(f"{Fore.GREEN}Found {len(dms)} DM channels")
                    for dm in dms:
                        if self.close_dm(token, dm['id']):
                            print(f"{Fore.GREEN}Successfully closed DM channel {dm['id']}")
                        else:
                            print(f"{Fore.RED}Failed to close DM channel {dm['id']}")
                        time.sleep(1)
                else:
                    print(f"{Fore.YELLOW}No DMs found")

            # Process Friends
            if self.config['remove_friends']:
                print(f"\n{Fore.CYAN}Cleaning Friends...")
                friends = self.get_friends(token)
                if friends:
                    print(f"{Fore.GREEN}Found {len(friends)} friends")
                    for friend in friends:
                        if self.remove_friend(token, friend['id']):
                            print(f"{Fore.GREEN}Successfully removed friend: {friend.get('user', {}).get('username', 'Unknown')}")
                        else:
                            print(f"{Fore.RED}Failed to remove friend: {friend.get('user', {}).get('username', 'Unknown')}")
                        time.sleep(1)
                else:
                    print(f"{Fore.YELLOW}No friends found")

            # Process Message Requests
            if self.config['decline_message_requests']:
                print(f"\n{Fore.CYAN}Declining message requests...")
                message_requests = self.get_message_requests(token)
                if message_requests:
                    print(f"{Fore.GREEN}Found {len(message_requests)} message requests")
                    for request in message_requests:
                        if self.decline_message_request(token, request['id']):
                            print(f"{Fore.GREEN}Successfully declined message request {request['id']}")
                        else:
                            print(f"{Fore.RED}Failed to decline message request {request['id']}")
                        time.sleep(1)
                else:
                    print(f"{Fore.YELLOW}No message requests found")

            # Remove Connections
            if self.config.get('remove_connections', False):
                print(f"\n{Fore.CYAN}Removing account connections...")
                connections = self.get_connections(token)
                if connections:
                    print(f"{Fore.GREEN}Found {len(connections)} connections")
                    for connection in connections:
                        connection_type = connection.get('type', '')
                        connection_name = connection.get('name', 'Unknown')
                        if self.remove_connection(token, connection_type, connection.get('id')):
                            print(f"{Fore.GREEN}Successfully removed {connection_type} connection: {connection_name}")
                        else:
                            print(f"{Fore.RED}Failed to remove {connection_type} connection: {connection_name}")
                        time.sleep(1)
                else:
                    print(f"{Fore.YELLOW}No connections found")

            # Process Blocked Users
            if self.config['unblock_users']:
                print(f"\n{Fore.CYAN}Unblocking Users...")
                blocked_users = self.get_blocked_users(token)
                if blocked_users:
                    print(f"{Fore.GREEN}Found {len(blocked_users)} blocked users")
                    for user in blocked_users:
                        if self.unblock_user(token, user['id']):
                            print(f"{Fore.GREEN}Successfully unblocked user: {user.get('user', {}).get('username', 'Unknown')}")
                        else:
                            print(f"{Fore.RED}Failed to unblock user: {user.get('user', {}).get('username', 'Unknown')}")
                        time.sleep(1)
                else:
                    print(f"{Fore.YELLOW}No blocked users found")

            # Process Incoming Friend Requests
            if self.config['decline_friend_requests']:
                print(f"\n{Fore.CYAN}Declining Friend requests...")
                requests = self.get_friend_requests(token)
                if requests:
                    print(f"{Fore.GREEN}Found {len(requests)} incoming friend requests")
                    for request in requests:
                        if self.remove_friend(token, request['id']):
                            print(f"{Fore.GREEN}Successfully declined friend request from: {request.get('user', {}).get('username', 'Unknown')}")
                        else:
                            print(f"{Fore.RED}Failed to decline friend request from: {request.get('user', {}).get('username', 'Unknown')}")
                        time.sleep(1)
                else:
                    print(f"{Fore.YELLOW}No friend requests found")

            # Process Outgoing Friend Requests
            if self.config['cancel_outgoing_requests']:
                print(f"\n{Fore.CYAN}Canceling outgoing friend requests...")
                outgoing = self.get_outgoing_requests(token)
                if outgoing:
                    print(f"{Fore.GREEN}Found {len(outgoing)} outgoing friend requests")
                    for request in outgoing:
                        if self.remove_friend(token, request['id']):
                            print(f"{Fore.GREEN}Successfully cancelled outgoing friend request to: {request.get('user', {}).get('username', 'Unknown')}")
                        else:
                            print(f"{Fore.RED}Failed to cancel outgoing friend request to: {request.get('user', {}).get('username', 'Unknown')}")
                        time.sleep(1)
                else:
                    print(f"{Fore.YELLOW}No outgoing friend requests to cancel")

            return True
            
        except Exception as e:
            print(f"{Fore.RED}Error processing token: {str(e)}")
            return False

def main():
    # Load config first - will exit if file doesn't exist
    config = load_config()
    
    # Verify all required config keys exist
    required_keys = [
        'remove_connections', 
        'delay', 
        'proxies',
        'set_language',
        'set_dark_mode',  # Added to required keys
        'unblock_users',
        'leave_servers',
        'clean_dms',
        'decline_message_requests',
        'remove_friends',
        'decline_friend_requests',
        'cancel_outgoing_requests'
    ]
    
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        print(f"{Fore.RED}Error: Missing required configuration keys: {', '.join(missing_keys)}")
        exit(1)

    # Load proxies if enabled
    if config.get('proxies', False):
        print(f"{Fore.CYAN}Loading proxies...")
        proxies = load_proxies()
        print(f"{Fore.GREEN}Loaded {len(proxies)} proxies")
    
    output_dir = create_output_dir()
    
    with open('input/tokens.txt', 'r') as f:
        tokens = [line.strip() for line in f if line.strip()]
    
    cleaner = DiscordCleaner(config)
    success = 0
    failed = 0
    invalid = 0
    
    total_tokens = len(tokens)
    
    for index, token in enumerate(tokens, 1):
        print(f"\n{Fore.CYAN}Processing token {index}/{total_tokens}")
        
        if cleaner.process_token(token):
            success += 1
            with open(f"{output_dir}/success.txt", 'a') as f:
                f.write(f"{token}\n")
        else:
            if not cleaner.check_token(token.split(':')[-1]):
                invalid += 1
                with open(f"{output_dir}/invalid.txt", 'a') as f:
                    f.write(f"{token}\n")
            else:
                failed += 1
                with open(f"{output_dir}/failed.txt", 'a') as f:
                    f.write(f"{token}\n")
        
        time.sleep(config.get('delay', 1))
    
    print(f"\n{Fore.CYAN}Final Results:")
    print(f"{Fore.GREEN}Successfully processed: {success}")
    print(f"{Fore.RED}Failed: {failed}")
    print(f"{Fore.YELLOW}Invalid tokens: {invalid}")
    print(f"{Fore.YELLOW}Results saved in: {output_dir}")

if __name__ == "__main__":
    main()
