"""
Bright Data Proxy Manager for IP rotation
"""

import requests
import random
import json
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType


class BrightDataProxy:
    def __init__(self):
        self.zone_id = "41644681-8a9c-4b6e-be2c-f4fe5e93e801"
        self.username = "younes@garraje.com"
        self.password = None
        self.endpoint = "zproxy.lum-superproxy.io"
        self.port = 22225
        self.session_id = None
        self.enabled = False
        
    def generate_session_id(self, process_num=1):
        """Generate unique session ID for each process"""
        self.session_id = f"session_{process_num}_{random.randint(1000, 9999)}"
        return self.session_id
    
    def get_proxy_auth(self, process_num=1):
        """Get proxy authentication string"""
        session_id = self.generate_session_id(process_num)
        return f"{self.username}-session-{session_id}:{self.zone_id}"
    
    def get_proxy_url(self, process_num=1):
        """Get complete proxy URL for requests"""
        auth = self.get_proxy_auth(process_num)
        return f"http://{auth}@{self.endpoint}:{self.port}"
    
    def test_proxy(self, process_num=1):
        try:
            session_id = self.generate_session_id(process_num)
            username = f"{self.username}-session-{session_id}"
            
            proxy_dict = {
                'http': f'http://{username}:{self.zone_id}@{self.endpoint}:{self.port}',
                'https': f'http://{username}:{self.zone_id}@{self.endpoint}:{self.port}'
            }
            
            response = requests.get('http://httpbin.org/ip', proxies=proxy_dict, timeout=10)
            
            if response.status_code == 200:
                return True, response.json().get('origin', 'Connected')
            else:
                return False, f"Status: {response.status_code}"
                
        except requests.exceptions.ProxyError as e:
            return False, f"Proxy Error: {str(e)}"
        except requests.exceptions.Timeout:
            return False, "Connection timeout"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def get_chrome_proxy_options(self, process_num=1):
        """Get Chrome proxy options"""
        if not self.enabled:
            return []
            
        auth = self.get_proxy_auth(process_num)
        
        proxy_options = [
            f"--proxy-server=http://{self.endpoint}:{self.port}",
            f"--proxy-auth={auth}",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor"
        ]
        
        return proxy_options
    
    def create_selenium_proxy(self, process_num=1):
        """Create Selenium proxy object"""
        if not self.enabled:
            return None
            
        proxy = Proxy()
        proxy.proxy_type = ProxyType.MANUAL
        proxy.http_proxy = f"{self.endpoint}:{self.port}"
        proxy.ssl_proxy = f"{self.endpoint}:{self.port}"
        
        # Note: Selenium doesn't directly support proxy auth
        # We'll handle this through Chrome options instead
        return proxy
    
    def enable_proxy(self):
        """Enable proxy usage"""
        self.enabled = True
    
    def disable_proxy(self):
        """Disable proxy usage"""
        self.enabled = False
    
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