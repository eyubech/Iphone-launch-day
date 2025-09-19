"""
Bright Data Proxy Manager for IP rotation - Fixed Version
"""

import requests
import random
import json
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType


class BrightDataProxy:
    def __init__(self, config=None):
        if config:
            # Use config from Config class
            self.zone_id = config.BRIGHT_DATA_ZONE_ID
            self.username = config.BRIGHT_DATA_USERNAME
            self.endpoint = config.BRIGHT_DATA_ENDPOINT
            self.port = config.BRIGHT_DATA_PORT
        else:
            # Fallback values based on your actual Bright Data credentials
            self.username = "brd-customer-hl_34c5d083-zone-residential_proxy1"
            self.password = "9peyq4z8rhj0"
            self.endpoint = "brd.superproxy.io"
            self.port = 33335
        
        self.session_id = None
        self.enabled = False
        
    def generate_session_id(self, process_num=1):
        """Generate unique session ID for each process"""
        self.session_id = f"session_{process_num}_{random.randint(1000, 9999)}"
        return self.session_id
    
    def get_proxy_auth(self, process_num=1):
        """Get proxy authentication string with random session for IP rotation"""
        if hasattr(self, 'password'):
            # Add random session to force IP rotation
            session_id = f"session_{process_num}_{random.randint(10000, 99999)}"
            auth_username = f"{self.username}-session-{session_id}"
            return f"{auth_username}:{self.password}"
        else:
            # Old format fallback
            return f"{self.username}:{self.zone_id}"
    
    def get_proxy_url(self, process_num=1):
        """Get complete proxy URL for requests with session for IP rotation"""
        if hasattr(self, 'password'):
            session_id = f"session_{process_num}_{random.randint(10000, 99999)}"
            auth_username = f"{self.username}-session-{session_id}"
            return f"http://{auth_username}:{self.password}@{self.endpoint}:{self.port}"
        else:
            return f"http://{self.username}:{self.zone_id}@{self.endpoint}:{self.port}"
    
    def test_proxy(self, process_num=1, max_retries=3):
        """Test proxy connection with retry logic for 503 errors"""
        import time
        
        for attempt in range(max_retries):
            try:
                if hasattr(self, 'password'):
                    # Use different session ID for each attempt to get fresh IP
                    session_id = f"session_{process_num}_{random.randint(10000, 99999)}"
                    auth_username = f"{self.username}-session-{session_id}"
                    auth_password = self.password
                else:
                    auth_username = self.username
                    auth_password = self.zone_id
                
                proxy_url = f"http://{auth_username}:{auth_password}@{self.endpoint}:{self.port}"
                
                proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }
                
                print(f"Testing proxy (attempt {attempt + 1}/{max_retries}): {self.endpoint}:{self.port}")
                print(f"Auth username: {auth_username}")
                print(f"Password: {auth_password[:5]}...")
                
                # Test with simple endpoint
                response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    ip = data.get('origin', 'Unknown')
                    return True, f"IP: {ip} (attempt {attempt + 1})"
                elif response.status_code == 503:
                    print(f"503 Service Unavailable on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5  # 5, 10, 15 seconds
                        print(f"Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return False, "503 Service Unavailable - all retries failed"
                else:
                    return False, f"HTTP {response.status_code}"
                    
            except requests.exceptions.ProxyError as e:
                error_msg = str(e)
                if "407" in error_msg:
                    return False, "Proxy authentication failed: Check username/password"
                elif "403" in error_msg:
                    return False, "Access forbidden: Check proxy permissions"
                elif "503" in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5
                        print(f"503 error, waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return False, "503 Service unavailable: All retries failed"
                else:
                    return False, f"Proxy error: {error_msg}"
            except requests.exceptions.ConnectTimeout:
                return False, "Connection timeout - check endpoint and port"
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"Timeout on attempt {attempt + 1}, retrying...")
                    time.sleep(3)
                    continue
                return False, "Request timeout - all retries failed"
            except requests.exceptions.ConnectionError as e:
                return False, f"Connection error: {str(e)}"
            except Exception as e:
                return False, f"Error: {str(e)}"
        
        return False, "All attempts failed"
    
    def get_chrome_proxy_options(self, process_num=1):
        """Get Chrome proxy options for Selenium - without session ID"""
        if not self.enabled:
            return []
        
        if hasattr(self, 'password'):
            auth = f"{self.username}:{self.password}"
        else:
            auth = f"{self.username}:{self.zone_id}"
        
        proxy_options = [
            f"--proxy-server=http://{self.endpoint}:{self.port}",
            f"--proxy-auth={auth}",
            "--disable-web-security",
            "--ignore-certificate-errors",
            "--ignore-ssl-errors",
            "--ignore-certificate-errors-spki-list"
        ]
        
        return proxy_options
    
    def create_selenium_proxy(self, process_num=1):
        """Create Selenium proxy object (Note: Auth must be handled via Chrome options)"""
        if not self.enabled:
            return None
            
        proxy = Proxy()
        proxy.proxy_type = ProxyType.MANUAL
        proxy.http_proxy = f"{self.endpoint}:{self.port}"
        proxy.ssl_proxy = f"{self.endpoint}:{self.port}"
        
        # Note: Selenium doesn't directly support proxy auth
        # Authentication is handled through Chrome options
        return proxy
    
    def enable_proxy(self):
        """Enable proxy usage"""
        self.enabled = True
        print(f"Bright Data proxy enabled: {self.endpoint}:{self.port}")
    
    def disable_proxy(self):
        """Disable proxy usage"""
        self.enabled = False
        print("Bright Data proxy disabled")
    
    def is_enabled(self):
        """Check if proxy is enabled"""
        return self.enabled
    
    def get_status(self):
        """Get proxy status information"""
        status = {
            'enabled': self.enabled,
            'zone_id': self.zone_id,
            'username': self.username,
            'endpoint': self.endpoint,
            'port': self.port,
            'current_session': self.session_id
        }
        return status
    
    def make_request_with_retry(self, url, process_num=1, max_retries=3, method='GET', **kwargs):
        """Make HTTP request through proxy with automatic retry on 503"""
        import time
        
        for attempt in range(max_retries):
            try:
                # Generate fresh session ID for each attempt
                session_id = f"session_{process_num}_{random.randint(10000, 99999)}"
                
                if hasattr(self, 'password'):
                    auth_username = f"{self.username}-session-{session_id}"
                    proxy_url = f"http://{auth_username}:{self.password}@{self.endpoint}:{self.port}"
                else:
                    proxy_url = f"http://{self.username}:{self.zone_id}@{self.endpoint}:{self.port}"
                
                proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }
                
                print(f"Making {method} request to {url} (attempt {attempt + 1}/{max_retries})")
                
                if method.upper() == 'GET':
                    response = requests.get(url, proxies=proxies, timeout=30, **kwargs)
                elif method.upper() == 'POST':
                    response = requests.post(url, proxies=proxies, timeout=30, **kwargs)
                else:
                    response = requests.request(method, url, proxies=proxies, timeout=30, **kwargs)
                
                if response.status_code == 503:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 10  # 10, 20, 30 seconds
                        print(f"503 error, waiting {wait_time} seconds for IP cooldown...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print("503 error - all retries exhausted")
                        return None
                
                return response
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 5
                    print(f"Request failed: {e}, retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Request failed after all retries: {e}")
                    return None
        
        return None