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
        """Get proxy authentication string"""
        if hasattr(self, 'password'):
            # New format with password
            session_id = self.generate_session_id(process_num)
            auth_username = f"{self.username}-session-{session_id}"
            return f"{auth_username}:{self.password}"
        else:
            # Old format with zone_id
            session_id = self.generate_session_id(process_num)
            auth_username = f"{self.username}-session-{session_id}"
            return f"{auth_username}:{self.zone_id}"
    
    def get_proxy_url(self, process_num=1):
        """Get complete proxy URL for requests"""
        session_id = self.generate_session_id(process_num)
        auth_username = f"{self.username}-session-{session_id}"
        if hasattr(self, 'password'):
            return f"http://{auth_username}:{self.password}@{self.endpoint}:{self.port}"
        else:
            return f"http://{auth_username}:{self.zone_id}@{self.endpoint}:{self.port}"
    
    def test_proxy(self, process_num=1):
        """Test proxy connection"""
        try:
            session_id = self.generate_session_id(process_num)
            auth_username = f"{self.username}-session-{session_id}"
            
            if hasattr(self, 'password'):
                auth_password = self.password
            else:
                auth_password = self.zone_id
            
            proxy_url = f"http://{auth_username}:{auth_password}@{self.endpoint}:{self.port}"
            
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            print(f"Testing proxy: {self.endpoint}:{self.port}")
            print(f"Auth username: {auth_username}")
            print(f"Password: {auth_password[:5]}...")
            
            # Try multiple test endpoints in case one is blocked
            test_urls = [
                'https://geo.brdtest.com/mygeo.json',
                'http://httpbin.org/ip',
                'https://api.ipify.org?format=json',
                'http://icanhazip.com'
            ]
            
            for url in test_urls:
                try:
                    print(f"Testing with: {url}")
                    response = requests.get(url, proxies=proxies, timeout=30)
                    
                    if response.status_code == 200:
                        try:
                            if 'json' in url or 'ipify' in url:
                                data = response.json()
                                if 'ip' in data:
                                    ip = data.get('ip', 'Unknown')
                                elif 'origin' in data:
                                    ip = data.get('origin', 'Unknown')
                                else:
                                    ip = str(data)
                                country = data.get('country', 'Unknown')
                                return True, f"IP: {ip}, Country: {country}"
                            else:
                                ip = response.text.strip()
                                return True, f"IP: {ip}"
                        except:
                            return True, f"Connected (Status: {response.status_code})"
                    elif response.status_code == 503:
                        print(f"503 Service Unavailable from {url}")
                        continue
                    else:
                        print(f"HTTP {response.status_code} from {url}")
                        continue
                        
                except requests.exceptions.ProxyError as e:
                    print(f"Proxy error with {url}: {e}")
                    continue
                except Exception as e:
                    print(f"Error with {url}: {e}")
                    continue
            
            return False, "All test endpoints returned 503 or failed"
                
        except requests.exceptions.ProxyError as e:
            error_msg = str(e)
            if "407" in error_msg:
                return False, "Proxy authentication failed: Check username/password"
            elif "403" in error_msg:
                return False, "Access forbidden: Check proxy permissions"
            elif "503" in error_msg:
                return False, "Service unavailable: Check account limits or try again later"
            else:
                return False, f"Proxy error: {error_msg}"
        except requests.exceptions.ConnectTimeout:
            return False, "Connection timeout - check endpoint and port"
        except requests.exceptions.Timeout:
            return False, "Request timeout"
        except requests.exceptions.ConnectionError as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def get_chrome_proxy_options(self, process_num=1):
        """Get Chrome proxy options for Selenium"""
        if not self.enabled:
            return []
        
        session_id = self.generate_session_id(process_num)
        auth_username = f"{self.username}-session-{session_id}"
        
        proxy_options = [
            f"--proxy-server=http://{self.endpoint}:{self.port}",
            f"--proxy-auth={auth_username}:{self.zone_id}",
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
    
    def get_requests_proxies(self, process_num=1):
        """Get proxy dict for requests library"""
        if not self.enabled:
            return None
        
        proxy_url = self.get_proxy_url(process_num)
        return {
            'http': proxy_url,
            'https': proxy_url
        }