import requests
import json
import time
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
try:
    import markdown2
except ImportError:
    print("Warning: markdown2 not installed, markdown features will be limited")
    markdown2 = None

try:
    from config import settings
except ImportError:
    from config_simple import settings

requests.packages.urllib3.disable_warnings()

class WeReadAPI:
    def __init__(self, cookies: str):
        """
        初始化微信读书API客户端
        参考 wereader 项目，支持自动获取的cookie

        Args:
            cookies: cookie字符串，格式为 "key1=value1; key2=value2"
        """
        self.cookies = cookies

        # Web端请求头 - 模拟浏览器行为，用于访问网页端点
        self.headers_web = {
            'Host': 'weread.qq.com',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Sec-Ch-Ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Cookie': cookies,
            'Referer': 'https://weread.qq.com/'
        }

        # API请求头 - 用于访问API端点
        self.headers = {
            'Host': 'i.weread.qq.com',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Cookie': cookies
        }

        self.headers_post = {
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'https://weread.qq.com',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cookie': cookies
        }

    def request_data(self, url: str) -> Dict:
        """Request data from WeRead API"""
        r = requests.get(url, headers=self.headers, verify=False)
        if r.ok:
            return r.json()
        else:
            raise Exception(f"Request failed: {r.text}")

    def login_success(self) -> bool:
        """
        检查登录是否成功
        简化为基本的网页访问验证，避免无效的API端点验证
        """
        try:
            print("🔍 验证登录状态: 检查网页访问权限")

            # 只验证最基本的网页访问权限
            r = requests.get(
                f"{settings.weread_web_url}/web/shelf",
                headers=self.headers_web,
                verify=False,
                timeout=10
            )

            if r.status_code == 200:
                # 检查是否返回HTML页面且包含微信读书相关内容
                content_type = r.headers.get('content-type', '')
                if 'text/html' in content_type:
                    html_content = r.text.lower()
                    # 检查是否包含微信读书相关关键词
                    if any(keyword in html_content for keyword in ['weread', '读书', '微信读书', 'book', 'shelf']):
                        print("✅ 登录验证成功：能够正常访问微信读书页面")
                        return True
                    else:
                        print("⚠️ 页面内容异常，可能未正确登录")
                        return False
                else:
                    print("✅ 登录验证成功：API响应正常")
                    return True

            elif r.status_code in [401, 403]:
                print(f"❌ 登录验证失败：认证错误 {r.status_code}")
                return False

            elif r.status_code == 404:
                print("⚠️ 端点不存在，但可能登录状态正常")
                # 404不一定表示登录失败，可能是端点变更
                return True

            else:
                print(f"⚠️ 异常状态码 {r.status_code}，尝试其他验证方式")
                return False

        except requests.exceptions.Timeout:
            print("⚠️ 请求超时，网络可能存在问题")
            return False
        except requests.exceptions.ConnectionError:
            print("⚠️ 连接错误，无法访问微信读书")
            return False
        except Exception as e:
            print(f"⚠️ 验证过程出错: {e}")
            return False

    def get_user_data(self, user_vid: str) -> Dict:
        """Get user's bookshelf data using multiple fallback APIs"""
        fallback_apis = [
            {
                "name": "web_shelf_new",
                "url": f"{settings.weread_web_url}/web/shelf",
                "method": "GET",
                "headers": self.headers_web,
                "timeout": 15
            },
            {
                "name": "web_bookshelf",
                "url": f"{settings.weread_web_url}/web/bookshelf",
                "method": "GET",
                "headers": self.headers_web,
                "timeout": 15
            },
            {
                "name": "shelf_sync_old",
                "url": f"{settings.weread_base_url}/shelf/sync?userVid={user_vid}&synckey=0&lectureSynckey=0",
                "method": "GET",
                "headers": self.headers,
                "timeout": 15
            },
            {
                "name": "user_bookshelf",
                "url": f"{settings.weread_base_url}/user/bookshelf?userVid={user_vid}",
                "method": "GET",
                "headers": self.headers,
                "timeout": 15
            },
            {
                "name": "web_shelf_minimal",
                "url": f"{settings.weread_web_url}/web/shelf?minimal=1",
                "method": "GET",
                "headers": self.headers_web,
                "timeout": 10
            }
        ]

        last_error = None
        for api_config in fallback_apis:
            try:
                print(f"🔄 尝试API: {api_config['name']} - {api_config['url']}")

                headers = api_config.get('headers', self.headers)

                if api_config['method'] == 'GET':
                    r = requests.get(
                        api_config['url'],
                        headers=headers,
                        verify=False,
                        timeout=api_config['timeout']
                    )
                else:
                    r = requests.post(
                        api_config['url'],
                        headers=headers,
                        verify=False,
                        timeout=api_config['timeout']
                    )

                if r.status_code == 200:
                    # 检查响应内容类型
                    content_type = r.headers.get('content-type', '')

                    if 'text/html' in content_type:
                        # HTML响应 - 尝试解析页面中的数据
                        print(f"✅ {api_config['name']} 返回HTML响应，尝试解析数据")
                        html_content = r.text

                        # 尝试从HTML中提取书籍数据
                        books_data = self._extract_books_from_html(html_content, user_vid)
                        if books_data:
                            print(f"✅ 从HTML中提取到 {len(books_data)} 本书籍")
                            return {
                                "books": books_data,
                                "user_vid": user_vid,
                                "source": api_config['name'] + "_html_parsed"
                            }
                        else:
                            # 无法解析HTML，但页面访问成功
                            return {
                                "books": [],
                                "user_vid": user_vid,
                                "source": api_config['name'] + "_html_no_data",
                                "html_content": html_content[:1000]  # 保存部分HTML用于调试
                            }
                    else:
                        # JSON响应
                        try:
                            data = r.json()
                            print(f"✅ {api_config['name']} API调用成功")
                            return data
                        except ValueError as json_error:
                            print(f"⚠️ {api_config['name']} 返回的不是有效JSON: {json_error}")
                            # 如果不是JSON但状态码是200，可能是一个特殊响应
                            return {
                                "books": [],
                                "user_vid": user_vid,
                                "source": api_config['name'] + "_non_json",
                                "raw_response": r.text[:200]
                            }

                elif r.status_code in [401, 403]:
                    # 认证相关错误，记录但继续尝试其他API
                    error_msg = f"认证失败 {r.status_code}: {api_config['name']}"
                    print(f"⚠️ {error_msg}")
                    last_error = Exception(error_msg)
                    continue

                elif r.status_code == 404:
                    # 端点不存在，继续尝试其他API
                    print(f"⚠️ 端点不存在 404: {api_config['name']}")
                    continue

                else:
                    # 其他错误状态码
                    error_msg = f"API返回异常状态码 {r.status_code}: {api_config['name']}"
                    print(f"⚠️ {error_msg}")
                    last_error = Exception(error_msg)
                    continue

            except requests.exceptions.Timeout:
                print(f"⚠️ 请求超时: {api_config['name']}")
                continue
            except requests.exceptions.ConnectionError:
                print(f"⚠️ 连接错误: {api_config['name']}")
                continue
            except Exception as e:
                error_msg = f"{api_config['name']} 调用出错: {str(e)}"
                print(f"⚠️ {error_msg}")
                last_error = e
                continue

        # 所有API都失败了
        error_msg = "所有书架API都调用失败，最后错误: " + str(last_error) if last_error else "未知错误"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)

    def _extract_books_from_html(self, html_content: str, user_vid: str) -> List[Dict]:
        """
        从HTML页面中提取书籍数据
        分析微信读书页面的结构，寻找书籍相关的数据
        """
        try:
            import re
            import json
            from typing import List, Dict

            books = []
            print(f"🔍 开始解析HTML书架数据，内容长度: {len(html_content)}")

            # 方法1: 查找JavaScript中的书籍数据（更加全面的模式）
            js_patterns = [
                # 常见的书籍数据模式
                r'books\s*:\s*(\[[\s\S]*?\])',  # books: [...]
                r'"books"\s*:\s*(\[[\s\S]*?\])',  # "books": [...]
                r'bookList\s*:\s*(\[[\s\S]*?\])',  # bookList: [...]
                r'shelfData\s*:\s*(\[[\s\S]*?\])',  # shelfData: [...]
                r'shelf\s*:\s*\{[^}]*books\s*:\s*(\[[\s\S]*?\])',  # shelf: {books: [...]}
                r'data\s*:\s*\{[^}]*books\s*:\s*(\[[\s\S]*?\])',  # data: {books: [...]}
                # 更具体的微信读书模式
                r'window\.__INITIAL_STATE__\s*=\s*\{[\s\S]*?"books"\s*:\s*(\[[\s\S]*?\])',
                r'window\.preloadedData\s*=\s*[\s\S]*?"books"\s*:\s*(\[[\s\S]*?\])',
                r'__NUXT__\s*=\s*[\s\S]*?"books"\s*:\s*(\[[\s\S]*?\])'
            ]

            for pattern in js_patterns:
                try:
                    matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
                    for match in matches:
                        try:
                            # 尝试解析JSON数据
                            match = match.strip()
                            if match.startswith('[') and match.endswith(']'):
                                book_list = json.loads(match)
                                if isinstance(book_list, list) and book_list:
                                    print(f"✅ 找到JS书籍数据，数量: {len(book_list)}")
                                    for book in book_list:
                                        if isinstance(book, dict) and book.get('bookId'):
                                            books.append(self._normalize_book_data(book))
                        except (json.JSONDecodeError, ValueError) as e:
                            continue
                except Exception as e:
                    continue

            # 方法2: 查找更具体的书籍ID和信息模式
            if not books:
                print("🔍 JS解析无结果，尝试HTML元素解析")
                
                # 更精确的书籍ID模式
                book_patterns = [
                    r'data-book-id=["\']([^"\']+)["\']',  # data-book-id="..."
                    r'data-bookid=["\']([^"\']+)["\']',   # data-bookid="..."
                    r'bookId["\']?\s*[:=]\s*["\']([a-zA-Z0-9_-]{6,})["\']',  # bookId: "..."
                    r'/book/([a-zA-Z0-9_-]{6,})',         # /book/bookId
                    r'weread\.qq\.com/web/reader/([a-zA-Z0-9_-]{6,})',  # reader links
                ]
                
                # 提取书籍标题模式
                title_patterns = [
                    r'data-title=["\']([^"\']+)["\']',
                    r'title=["\']([^"\']+)["\']',
                    r'alt=["\']([^"\']+)["\']'
                ]

                book_ids = set()
                for pattern in book_patterns:
                    matches = re.findall(pattern, html_content, re.IGNORECASE)
                    for match in matches:
                        if match and len(match) >= 6 and not match.startswith('http'):
                            book_ids.add(match)

                if book_ids:
                    print(f"✅ 从HTML中找到 {len(book_ids)} 个书籍ID")
                    for book_id in book_ids:
                        books.append({
                            "bookId": book_id,
                            "title": self._extract_book_title(html_content, book_id) or f"书籍-{book_id[:8]}",
                            "author": "待获取",
                            "cover": self._extract_book_cover(html_content, book_id) or "",
                            "category": "",
                            "finishReading": 0,
                            "newRatingDetail": "",
                            "readUpdateTime": int(time.time() * 1000),
                            "source": "html_element_parsed"
                        })

            # 方法3: 查找书架相关的JSON数据
            if not books:
                print("🔍 尝试查找内嵌的JSON数据")
                json_patterns = [
                    r'<script[^>]*type=["\']application/json["\'][^>]*>([\s\S]*?)</script>',
                    r'<script[^>]*>([\s\S]*?window\.__.*?=[\s\S]*?)</script>',
                ]
                
                for pattern in json_patterns:
                    matches = re.findall(pattern, html_content, re.DOTALL)
                    for match in matches:
                        try:
                            # 尝试提取其中的书籍信息
                            if 'book' in match.lower() and 'id' in match.lower():
                                book_refs = re.findall(r'"([a-zA-Z0-9_-]{6,})"', match)
                                for book_id in book_refs:
                                    if len(book_id) >= 6 and book_id not in [b.get('bookId') for b in books]:
                                        books.append({
                                            "bookId": book_id,
                                            "title": f"书籍-{book_id[:8]}",
                                            "author": "待获取",
                                            "cover": "",
                                            "category": "",
                                            "finishReading": 0,
                                            "newRatingDetail": "",
                                            "readUpdateTime": int(time.time() * 1000),
                                            "source": "json_script_parsed"
                                        })
                        except Exception:
                            continue

            # 去重和清理
            seen_ids = set()
            unique_books = []
            for book in books:
                book_id = book.get('bookId', '')
                if book_id and book_id not in seen_ids and len(book_id) >= 6:
                    seen_ids.add(book_id)
                    unique_books.append(book)

            print(f"📚 HTML解析完成，提取到 {len(unique_books)} 本书籍")
            
            # 如果仍然没有找到书籍，输出调试信息
            if not unique_books:
                print("⚠️ 未找到书籍数据，输出HTML片段用于调试:")
                preview = html_content[:500].replace('\n', ' ')
                print(f"HTML预览: {preview}...")
                
                # 检查是否包含登录相关的关键词
                if any(keyword in html_content.lower() for keyword in ['login', '登录', 'scan', '扫码']):
                    print("💡 检测到登录页面，可能需要重新登录")

            return unique_books[:100]  # 增加到100本书的限制

        except Exception as e:
            print(f"❌ HTML解析出错: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _normalize_book_data(self, book_data: Dict) -> Dict:
        """标准化书籍数据格式"""
        return {
            "bookId": book_data.get('bookId', book_data.get('id', '')),
            "title": book_data.get('title', book_data.get('name', '未知书籍')),
            "author": book_data.get('author', book_data.get('authors', '未知作者')),
            "cover": book_data.get('cover', book_data.get('coverUrl', '')),
            "category": book_data.get('category', book_data.get('categoryName', '')),
            "finishReading": book_data.get('finishReading', book_data.get('isFinished', 0)),
            "newRatingDetail": book_data.get('newRatingDetail', book_data.get('rating', '')),
            "readUpdateTime": book_data.get('readUpdateTime', book_data.get('updateTime', int(time.time() * 1000))),
            "source": "js_data_parsed"
        }

    def _extract_book_title(self, html_content: str, book_id: str) -> str:
        """从HTML中提取特定书籍的标题"""
        try:
            import re
            # 在书籍ID附近查找标题
            patterns = [
                rf'{re.escape(book_id)}[^>]*[^>]*title=["\']([^"\']+)["\']',
                rf'title=["\']([^"\']+)["\'][^>]*{re.escape(book_id)}',
                rf'{re.escape(book_id)}[^>]*>([^<]+)<',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            return ""
        except Exception:
            return ""

    def _extract_book_cover(self, html_content: str, book_id: str) -> str:
        """从HTML中提取特定书籍的封面"""
        try:
            import re
            # 在书籍ID附近查找封面图片
            patterns = [
                rf'{re.escape(book_id)}[^>]*[^>]*src=["\']([^"\']+)["\']',
                rf'src=["\']([^"\']*{re.escape(book_id)}[^"\']*)["\']',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            return ""
        except Exception:
            return ""

    def get_book_info(self, book_id: str) -> Dict:
        """Get book information with fallback support"""
        fallback_urls = [
            f"{settings.weread_base_url}/book/info?bookId={book_id}",
            f"{settings.weread_base_url}/web/book/info?bookId={book_id}",
            f"{settings.weread_base_url}/book/detail?bookId={book_id}"
        ]

        last_error = None
        for url in fallback_urls:
            try:
                print(f"🔄 获取书籍信息: {book_id} - {url.split('/')[-1]}")
                r = requests.get(url, headers=self.headers, verify=False, timeout=10)

                if r.status_code == 200:
                    try:
                        data = r.json()
                        print(f"✅ 书籍信息获取成功: {book_id}")
                        return data
                    except ValueError as json_error:
                        # 检查是否为HTML响应
                        content_type = r.headers.get('content-type', '')
                        if 'text/html' in content_type:
                            print(f"📄 书籍信息返回HTML页面: {book_id}")
                            # 返回基础书籍信息，避免抛出异常
                            return {
                                "bookId": book_id,
                                "title": "书籍信息不可用",
                                "author": "未知",
                                "cover": "",
                                "intro": "该书籍信息暂时无法获取",
                                "publisher": "",
                                "category": "",
                                "finishReading": 0,
                                "newRatingDetail": {"title": ""},
                                "source": "html_response"
                            }
                        else:
                            print(f"⚠️ 书籍信息返回的不是有效JSON: {json_error}")
                            last_error = json_error
                            continue
                elif r.status_code == 404:
                    print(f"⚠️ 书籍不存在 404: {book_id}")
                    # 书籍不存在时返回基础信息而不是抛出异常
                    return {
                        "bookId": book_id,
                        "title": "书籍信息不可用",
                        "author": "未知",
                        "cover": "",
                        "intro": "该书籍信息暂时无法获取",
                        "category": "",
                        "publisher": "",
                        "finishReading": 0,
                        "newRatingDetail": {"title": ""},
                        "error": "书籍信息不可用"
                    }
                else:
                    error_msg = f"获取书籍信息失败 {r.status_code}: {book_id}"
                    print(f"⚠️ {error_msg}")
                    last_error = Exception(error_msg)
                    continue

            except Exception as e:
                print(f"⚠️ 获取书籍信息出错: {book_id} - {e}")
                last_error = e
                continue

        # 所有URL都失败了
        error_msg = f"无法获取书籍信息 {book_id}: {str(last_error) if last_error else '未知错误'}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)

    def get_sorted_chapters(self, book_id: str) -> List[Tuple]:
        """Get sorted chapters of a book"""
        if '_' in book_id:
            return []  # WeChat articles not supported

        url = f"{settings.weread_base_url}/book/chapterInfos?bookIds={book_id}&synckeys=0"
        data = self.request_data(url)
        chapters = []

        for item in data['data'][0]['updated']:
            try:
                chapters.append((item['chapterUid'], item['level'], item['title']))
            except:
                chapters.append((item['chapterUid'], 1, item['title']))

        return chapters

    def get_bookmarks(self, book_id: str) -> Dict:
        """Get bookmarks/notes for a book with fallback support"""
        fallback_urls = [
            f"{settings.weread_base_url}/book/bookmarklist?bookId={book_id}",
            f"{settings.weread_base_url}/web/book/bookmarklist?bookId={book_id}",
            f"{settings.weread_base_url}/bookmarks/list?bookId={book_id}"
        ]

        last_error = None
        for url in fallback_urls:
            try:
                print(f"🔄 获取书签: {book_id} - {url.split('/')[-1]}")
                r = requests.get(url, headers=self.headers, verify=False, timeout=15)

                if r.status_code == 200:
                    try:
                        data = r.json()
                        # 检查数据结构是否正确
                        if isinstance(data, dict) and ('updated' in data or 'bookmarks' in data or 'data' in data):
                            print(f"✅ 书签获取成功: {book_id}")
                            return data
                        else:
                            print(f"⚠️ 书签数据结构异常: {book_id}")
                            last_error = Exception("数据结构异常")
                            continue
                    except ValueError as json_error:
                        # 检查是否为HTML响应
                        content_type = r.headers.get('content-type', '')
                        if 'text/html' in content_type:
                            print(f"📄 书签返回HTML页面: {book_id}")
                            # 返回空书签数据，避免抛出异常
                            return {
                                "book": {"bookId": book_id},
                                "updated": [],
                                "source": "html_response",
                                "error": "书签功能暂时不可用，返回HTML页面"
                            }
                        else:
                            print(f"⚠️ 书签数据返回的不是有效JSON: {json_error}")
                            last_error = json_error
                            continue
                elif r.status_code == 404:
                    print(f"⚠️ 书籍不存在或无书签 404: {book_id}")
                    # 返回空书签数据而不是抛出异常
                    return {
                        "book": {"bookId": book_id},
                        "updated": [],
                        "error": "书籍不存在或无书签"
                    }
                else:
                    error_msg = f"获取书签失败 {r.status_code}: {book_id}"
                    print(f"⚠️ {error_msg}")
                    last_error = Exception(error_msg)
                    continue

            except Exception as e:
                print(f"⚠️ 获取书签出错: {book_id} - {e}")
                last_error = e
                continue

        # 所有URL都失败了，返回空数据结构而不是抛出异常
        print(f"❌ 无法获取书签 {book_id}: {str(last_error) if last_error else '未知错误'}")
        return {
            "book": {"bookId": book_id},
            "updated": [],
            "error": f"无法获取书签: {str(last_error) if last_error else '未知错误'}"
        }

    def get_sorted_contents_from_data(self, data: Dict) -> Dict:
        """Process bookmark data and sort by chapter and position"""
        book_id = data['book']['bookId']

        # Handle WeChat articles
        if '_' in book_id:
            return {}  # Simplified for now

        contents = defaultdict(list)

        for item in data['updated']:
            chapter_uid = item['chapterUid']
            text = item['markText']
            text_position = int(item['range'].split('-')[0])
            text_style = item['style']
            contents[chapter_uid].append([text_position, text_style, text])

        # Sort contents by position within each chapter
        sorted_contents = defaultdict(list)
        for chapter_uid in contents.keys():
            sorted_contents[chapter_uid] = sorted(contents[chapter_uid], key=lambda x: x[0])

        return sorted_contents

    def set_content_style(self, style: int, text: str) -> str:
        """Apply styling to content based on highlight style"""
        style_map = {
            0: {'pre': "", 'suf': ""},  # Red underline
            1: {'pre': "**", 'suf': "**"},  # Orange background (bold)
            2: {'pre': "", 'suf': ""}  # Blue wavy line
        }
        style_config = style_map.get(style, style_map[0])
        return style_config['pre'] + text.strip() + style_config['suf']

    def set_chapter_level(self, level: int) -> str:
        """Set chapter heading level"""
        level_map = {
            1: '## ',
            2: '### ',
            3: '#### '
        }
        return level_map.get(level, '## ')

    def get_markdown_content(self, book_id: str, is_all_chapter: int = 1) -> str:
        """Generate markdown content from bookmarks"""
        try:
            # Get bookmark data
            bookmark_data = self.get_bookmarks(book_id)

            if '_' in book_id:
                return ""  # WeChat articles not fully supported

            # Get chapters and contents
            sorted_chapters = self.get_sorted_chapters(book_id)
            sorted_contents = self.get_sorted_contents_from_data(bookmark_data)

            res = '\n'

            # Iterate through chapters
            for chapter in sorted_chapters:
                # Skip chapters without bookmarks if requested
                if is_all_chapter <= 0 and len(sorted_contents[chapter[0]]) == 0:
                    continue

                # Add chapter title
                title = chapter[2]
                res += self.set_chapter_level(chapter[1]) + title + '\n\n'

                # Add bookmarks for this chapter
                for text in sorted_contents[chapter[0]]:
                    res += self.set_content_style(text[1], text[2]) + '\n\n'

            return res

        except Exception as e:
            raise Exception(f"Failed to get markdown content: {str(e)}")

    def search_books(self, user_data: Dict, query: str) -> List[Dict]:
        """
        在用户书库中搜索书籍
        参考 wereader 项目的搜索实现
        """
        try:
            from fuzzywuzzy import fuzz
        except ImportError:
            print("Warning: fuzzywuzzy not installed, using simple string matching")
            # 简单的字符串匹配作为fallback
            results = []
            for book in user_data.get('books', []):
                title = book.get('title', '')
                if query.lower() in title.lower():
                    results.append({
                        'bookId': book['bookId'],
                        'title': title,
                        'author': book.get('author', ''),
                        'cover': book.get('cover', '').replace('s_', 't7_'),
                        'ratio': 80  # 固定评分
                    })
            return results

        results = []

        for book in user_data.get('books', []):
            title = book.get('title', '')
            ratio = fuzz.partial_ratio(title, query)

            if ratio > 60:  # Lowered threshold for better results
                results.append({
                    'bookId': book['bookId'],
                    'title': title,
                    'author': book.get('author', ''),
                    'cover': book.get('cover', '').replace('s_', 't7_'),
                    'ratio': ratio
                })

        # Sort by relevance
        results.sort(key=lambda x: x['ratio'], reverse=True)
        return results
    
    @staticmethod
    def format_cookies_from_dict(cookie_dict: Dict) -> str:
        """
        将cookie字典格式化为字符串
        参考 wereader 项目的cookie处理方式
        """
        return '; '.join([f'{key}={value}' for key, value in cookie_dict.items()])
    
    @staticmethod
    def parse_cookies_from_string(cookie_string: str) -> Dict:
        """
        从cookie字符串解析为字典
        参考 wereader 项目的cookie解析方式
        对URL编码的值进行解码处理
        """
        import urllib.parse

        cookies = {}
        for item in cookie_string.split(';'):
            if '=' in item:
                key, value = item.strip().split('=', 1)
                # 对URL编码的值进行解码
                cookies[key] = urllib.parse.unquote(value)

        return cookies