# 参考 mcp-server-weread 项目的Cookie管理实现
import requests
import json
import os
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta


class CookieManager:
    """微信读书Cookie管理器，参考mcp-server-weread项目实现"""
    
    def __init__(self):
        self.weread_base_url = "https://i.weread.qq.com"
        self.cookie_cache = {}
        self.cache_expiry = {}
    
    def parse_cookie_string(self, cookie_string: str) -> Dict[str, str]:
        """
        解析Cookie字符串为字典
        参考mcp-server-weread的解析方式
        """
        cookies = {}
        
        # 清理Cookie字符串
        cookie_string = cookie_string.strip()
        
        # 分割Cookie项目
        cookie_items = cookie_string.split(';')
        
        for item in cookie_items:
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # 只保留微信读书相关的cookies
                if key.startswith('wr_') or key in ['vid', 'skey', 'gid']:
                    cookies[key] = value
        
        return cookies
    
    def validate_cookie_format(self, cookies: Dict[str, str]) -> Tuple[bool, str]:
        """
        验证Cookie格式是否完整
        参考mcp-server-weread的验证逻辑
        """
        required_fields = ['wr_gid', 'wr_vid', 'wr_skey', 'wr_rt']
        missing_fields = []
        
        for field in required_fields:
            if field not in cookies or not cookies[field]:
                missing_fields.append(field)
        
        if missing_fields:
            return False, f"缺少必要的Cookie字段: {', '.join(missing_fields)}"
        
        # 基本格式验证
        if not cookies['wr_vid'].isdigit():
            return False, "wr_vid格式不正确，应为数字"
        
        return True, "Cookie格式验证通过"
    
    def test_cookie_validity(self, cookie_string: str) -> Tuple[bool, str, Dict]:
        """
        测试Cookie是否有效
        参考mcp-server-weread的验证方式
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Sec-Ch-Ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Cookie': cookie_string,
                'Referer': 'https://weread.qq.com/'
            }
            
            # 使用新的web shelf API进行验证
            test_url = f"https://weread.qq.com/web/shelf"
            response = requests.get(test_url, headers=headers, timeout=15, verify=False)
            
            if response.status_code == 200:
                try:
                    # 检查是否为HTML响应
                    if 'text/html' in response.headers.get('content-type', ''):
                        # HTML响应，检查登录状态
                        if 'wr_vid' in response.text or 'bookshelf' in response.text:
                            # 从Cookie中提取用户信息，进行URL解码
                            cookies = {}
                            for item in cookie_string.split(';'):
                                if '=' in item:
                                    key, value = item.strip().split('=', 1)
                                    cookies[key] = value

                            # 对URL编码的值进行解码，并进行更安全的处理
                            import urllib.parse
                            def safe_unquote(value: str) -> str:
                                """安全地进行URL解码"""
                                if not value:
                                    return ''
                                try:
                                    # 尝试多种解码方式
                                    decoded = urllib.parse.unquote(value, encoding='utf-8')
                                    # 如果解码后的字符串与原字符串相同，尝试其他编码
                                    if decoded == value and '%' in value:
                                        decoded = urllib.parse.unquote(value, encoding='gbk', errors='ignore')
                                    return decoded
                                except Exception:
                                    return value

                            user_info = {
                                'vid': cookies.get('wr_vid', ''),
                                'name': safe_unquote(cookies.get('wr_name', '')),
                                'avatar': safe_unquote(cookies.get('wr_avatar', '')),
                                'gender': cookies.get('wr_gender', ''),
                                'localvid': cookies.get('wr_localvid', ''),
                                'gid': cookies.get('wr_gid', ''),
                                'skey': cookies.get('wr_skey', ''),
                                'rt': cookies.get('wr_rt', '')
                            }
                            print(f"✅ 提取用户信息: {user_info['name']} (vid: {user_info['vid']})")
                            return True, "Cookie验证成功", user_info
                        else:
                            return False, "Cookie无效或需要重新登录", {}
                    else:
                        # JSON响应
                        user_info = response.json()
                        if user_info and isinstance(user_info, dict):
                            return True, "Cookie验证成功", user_info
                        else:
                            return False, "Cookie有效但无法获取用户信息", {}
                except Exception as e:
                    # 即使解析失败，但响应200仍然表示Cookie可能有效
                    cookies = {}
                    for item in cookie_string.split(';'):
                        if '=' in item:
                            key, value = item.strip().split('=', 1)
                            cookies[key] = value
                    
                    if cookies.get('wr_vid'):
                        # 使用相同的安全解码函数
                        import urllib.parse
                        def safe_unquote(value: str) -> str:
                            if not value:
                                return ''
                            try:
                                decoded = urllib.parse.unquote(value, encoding='utf-8')
                                if decoded == value and '%' in value:
                                    decoded = urllib.parse.unquote(value, encoding='gbk', errors='ignore')
                                return decoded
                            except Exception:
                                return value
                        
                        user_info = {
                            'vid': cookies.get('wr_vid', ''),
                            'name': safe_unquote(cookies.get('wr_name', '')),
                            'avatar': safe_unquote(cookies.get('wr_avatar', '')),
                            'gender': cookies.get('wr_gender', ''),
                            'localvid': cookies.get('wr_localvid', ''),
                            'gid': cookies.get('wr_gid', ''),
                            'skey': cookies.get('wr_skey', ''),
                            'rt': cookies.get('wr_rt', '')
                        }
                        print(f"⚠️ Cookie基本验证通过: {user_info['name']} (vid: {user_info['vid']})")
                        return True, "Cookie基本验证通过", user_info
                    return False, f"响应解析失败: {str(e)}", {}
            
            elif response.status_code == 401:
                return False, "Cookie已过期或无效", {}
            elif response.status_code == 403:
                return False, "访问被拒绝，可能需要重新登录", {}
            else:
                return False, f"API返回异常状态码: {response.status_code}", {}
                
        except requests.exceptions.Timeout:
            return False, "请求超时，请检查网络连接", {}
        except requests.exceptions.ConnectionError:
            return False, "无法连接到微信读书服务器", {}
        except Exception as e:
            return False, f"验证过程出错: {str(e)}", {}
    
    def get_bookshelf_preview(self, cookie_string: str, vid: str) -> Tuple[bool, str, Dict]:
        """
        获取书架预览信息，用于验证Cookie
        使用更新的微信读书API
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Sec-Ch-Ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Cookie': cookie_string,
                'Referer': 'https://weread.qq.com/',
            }
            
            # 使用新的web shelf API获取书架信息
            url = f"https://weread.qq.com/web/shelf"
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            
            if response.status_code == 200:
                try:
                    # 检查响应类型
                    if 'text/html' in response.headers.get('content-type', ''):
                        # HTML响应，返回基础信息
                        if 'bookshelf' in response.text or 'shelf' in response.text:
                            return True, "成功访问书架页面", {"books": [], "source": "web_shelf_html"}
                        else:
                            return False, "书架页面访问异常", {}
                    else:
                        # JSON响应
                        data = response.json()
                        books_count = len(data.get('books', []))
                        return True, f"成功获取书架信息，共{books_count}本书", data
                except Exception as e:
                    # 即使解析失败，200状态码仍表示访问成功
                    return True, "书架访问成功（解析异常）", {"books": [], "error": str(e)}
            else:
                return False, f"获取书架失败，状态码: {response.status_code}", {}
                
        except Exception as e:
            return False, f"获取书架信息失败: {str(e)}", {}
    
    def format_cookie_for_api(self, cookies: Dict[str, str]) -> str:
        """
        格式化Cookie用于API调用
        参考mcp-server-weread的格式化方式
        """
        # 确保必要字段存在
        formatted_cookies = {
            'wr_gid': cookies.get('wr_gid', ''),
            'wr_vid': cookies.get('wr_vid', ''),
            'wr_skey': cookies.get('wr_skey', ''),
            'wr_pf': '0',
            'wr_rt': cookies.get('wr_rt', ''),
            'wr_localvid': cookies.get('wr_localvid', ''),
            'wr_name': cookies.get('wr_name', ''),
            'wr_avatar': cookies.get('wr_avatar', ''),
            'wr_gender': cookies.get('wr_gender', '')
        }
        
        return '; '.join([f'{key}={value}' for key, value in formatted_cookies.items()])
    
    def extract_user_info(self, user_data: Dict) -> Dict[str, str]:
        """
        从用户数据中提取用户信息，进行适当的数据清理
        """
        import urllib.parse
        
        def safe_unquote(value: str) -> str:
            """安全地进行URL解码"""
            if not value:
                return ''
            try:
                decoded = urllib.parse.unquote(value, encoding='utf-8')
                if decoded == value and '%' in value:
                    decoded = urllib.parse.unquote(value, encoding='gbk', errors='ignore')
                return decoded
            except Exception:
                return value
        
        result = {
            'wr_name': safe_unquote(user_data.get('name', '')),
            'wr_avatar': safe_unquote(user_data.get('avatar', '')),
            'wr_vid': str(user_data.get('vid', '')),
            'wr_gender': str(user_data.get('gender', 0)),
            'wr_localvid': user_data.get('localvid', ''),
            'wr_gid': user_data.get('gid', ''),
            'wr_skey': user_data.get('skey', ''),
            'wr_rt': user_data.get('rt', '')
        }
        
        print(f"📋 提取用户信息完成: {result['wr_name']} (vid: {result['wr_vid']})")
        return result


# 全局Cookie管理器实例
cookie_manager = CookieManager()
