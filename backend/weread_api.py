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
        # 对cookie字符串进行编码处理，确保HTTP头部兼容
        self.cookies = self._safe_encode_cookies(cookies)

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
            'Cookie': self.cookies,
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
            'Cookie': self.cookies
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
            'Cookie': self.cookies
        }

    def _safe_encode_cookies(self, cookies: str) -> str:
        """
        安全地编码cookies字符串，确保HTTP头部兼容
        处理中文字符等非ASCII字符的编码问题
        """
        try:
            import urllib.parse
            
            # 解析cookie字符串
            cookie_pairs = []
            for item in cookies.split(';'):
                item = item.strip()
                if '=' in item:
                    key, value = item.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 对value进行安全编码处理
                    try:
                        # 检查是否包含非ASCII字符
                        value.encode('ascii')
                        # 如果能够ASCII编码，直接使用
                        cookie_pairs.append(f"{key}={value}")
                    except UnicodeEncodeError:
                        # 如果包含非ASCII字符（如中文），进行URL编码
                        encoded_value = urllib.parse.quote(value, safe='')
                        cookie_pairs.append(f"{key}={encoded_value}")
                        print(f"🔤 Cookie字段 {key} 包含非ASCII字符，已进行URL编码")
            
            result = '; '.join(cookie_pairs)
            print(f"🍪 Cookie编码处理完成，长度: {len(result)}")
            return result
            
        except Exception as e:
            print(f"⚠️ Cookie编码处理失败: {e}")
            # 如果编码失败，返回原始字符串
            return cookies

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
        优先使用 rawBooks 获取完整书籍列表，确保包含文件夹深处的所有书籍
        """
        try:
            import re
            import json

            books = []
            print(f"🔍 开始解析HTML书架数据，内容长度: {len(html_content)}")

            # 查找 window.__INITIAL_STATE__ 数据
            match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html_content, re.DOTALL)
            if not match:
                print("❌ 未找到 window.__INITIAL_STATE__ 数据")
                return []

            try:
                initial_state = json.loads(match.group(1))
                print("✅ 成功解析 window.__INITIAL_STATE__ 数据")
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                return []

            # 定位到 shelf 数据
            shelf = initial_state.get("shelf", {})
            if not shelf:
                print("❌ 未找到 shelf 数据")
                # 打印initial_state的顶级键来调试
                print(f"🔍 initial_state 可用键: {list(initial_state.keys())}")
                return []

            print(f"🔍 shelf 数据结构调试:")
            print(f"   shelf 键: {list(shelf.keys())}")
            print(f"   shelf 数据大小: {len(str(shelf))} 字符")

            # 🎯 综合使用 rawBooks 和 rawIndexes 获取完整书籍列表
            print("🎯 综合使用 rawBooks 和 rawIndexes 获取完整书籍列表")

            raw_books = shelf.get("rawBooks", [])
            raw_indexes = shelf.get("rawIndexes", [])

            print(f"📚 找到 rawBooks: {len(raw_books)} 本书")
            print(f"📋 找到 rawIndexes: {len(raw_indexes)} 个索引")

            # 如果没有找到数据，尝试查找其他可能的字段
            if len(raw_books) == 0 and len(raw_indexes) == 0:
                print("🔍 探索其他可能的数据字段:")
                for key, value in shelf.items():
                    if isinstance(value, list) and len(value) > 0:
                        print(f"   发现非空列表字段: '{key}' ({len(value)} 项)")
                        if len(value) > 0 and isinstance(value[0], dict):
                            sample_keys = list(value[0].keys()) if value[0] else []
                            print(f"     首项键: {sample_keys[:10]}...")  # 只显示前10个键
                    elif isinstance(value, dict) and len(value) > 0:
                        print(f"   发现非空字典字段: '{key}' ({len(value)} 项)")
                        if 'books' in str(value).lower():
                            print(f"     可能包含书籍数据: {list(value.keys())[:10]}")

                # 尝试查找包含bookId的字段
                for key, value in shelf.items():
                    if isinstance(value, list):
                        for item in value[:3]:  # 只检查前3项
                            if isinstance(item, dict) and 'bookId' in item:
                                print(f"✨ 在 '{key}' 中发现包含bookId的数据: {item.get('bookId')}")
                                break

            # 1. 先建立 rawBooks 的 bookId -> book 映射
            raw_books_dict = {}
            if raw_books:
                for book in raw_books:
                    if (isinstance(book, dict) and
                        "bookId" in book and
                        isinstance(book["bookId"], str) and
                        book["bookId"].strip() != "" and
                        book["bookId"] not in ["undefined", "null", "None"]):
                        book_id = book["bookId"].strip()
                        raw_books_dict[book_id] = book

            # 2. 从 rawIndexes 中提取所有书籍ID（这可能包含更完整的列表）
            all_book_ids_from_indexes = set()
            if raw_indexes:
                for index_item in raw_indexes:
                    if isinstance(index_item, dict):
                        book_id = index_item.get("bookId")
                        role = index_item.get("role", "")

                        # 只处理类型为 "book" 的项目，并验证bookId有效性
                        if (book_id and
                            role == "book" and
                            isinstance(book_id, str) and
                            book_id.strip() != "" and
                            book_id not in ["undefined", "null", "None"]):
                            all_book_ids_from_indexes.add(book_id.strip())

            print(f"📋 从 rawIndexes 提取到 {len(all_book_ids_from_indexes)} 个书籍ID")

            # 3. 合并两个数据源的书籍ID
            all_book_ids = set()

            # 从 rawBooks 中获取ID
            for book_id in raw_books_dict.keys():
                all_book_ids.add(book_id)

            # 从 rawIndexes 中获取ID
            all_book_ids.update(all_book_ids_from_indexes)

            print(f"🔗 合并后总共有 {len(all_book_ids)} 个唯一书籍ID")

            # 4. 按优先级提取书籍信息：先处理有完整信息的，再处理只有ID的
            books_with_full_info = []
            books_with_partial_info = []

            # 首先添加所有有完整信息的书籍（来自rawBooks）
            for book_id in all_book_ids:
                if book_id in raw_books_dict:
                    book_data = raw_books_dict[book_id]
                    normalized_book = self._normalize_book_data_from_html(book_data, "rawBooks")
                    books_with_full_info.append(normalized_book)

            # 然后添加只有ID的书籍（需要后续通过syncBook获取详情）
            for book_id in all_book_ids:
                if book_id not in raw_books_dict:
                    basic_book = {
                        "bookId": book_id,
                        "title": f"书籍_{book_id}",
                        "author": "需要获取详情",
                        "cover": "",
                        "category": "",
                        "finishReading": 0,
                        "newRatingDetail": "",
                        "readUpdateTime": int(time.time() * 1000),
                        "source": "rawIndexes_id_only",
                        "needsDetailFetch": True  # 标记需要获取详情
                    }
                    books_with_partial_info.append(basic_book)

            # 按顺序合并：完整信息的在前，部分信息的在后
            books.extend(books_with_full_info)
            books.extend(books_with_partial_info)

            print(f"✅ 成功提取 {len(books)} 本书籍")
            print(f"   📖 完整信息: {len(books_with_full_info)} 本")
            print(f"   📋 仅ID信息: {len(books_with_partial_info)} 本")

            # 检查是否还有更多书籍需要加载
            self._check_for_more_books(shelf)

            if books:
                return books

            # 如果没有 rawBooks，回退到 booksAndArchives 方法
            print("⚠️ 未找到 rawBooks，回退到 booksAndArchives 方法")

            books_and_archives = shelf.get("booksAndArchives", [])
            if not books_and_archives:
                print("❌ 未找到 booksAndArchives 数据")
                raise Exception("❌ 未找到 booksAndArchives 数据")

            print(f"📚 找到 booksAndArchives 数组，包含 {len(books_and_archives)} 个项目")

            # 处理 booksAndArchives 数组（回退方法）
            processed_book_ids = set()

            for i, item in enumerate(books_and_archives):
                if not isinstance(item, dict):
                    continue

                # 判断是书籍还是Archive文件夹
                if "bookId" in item:
                    # 这是一本书
                    book_id = item["bookId"]
                    if book_id not in processed_book_ids:
                        processed_book_ids.add(book_id)
                        normalized_book = self._normalize_book_data_from_html(item, "booksAndArchives")
                        books.append(normalized_book)
                        print(f"  📖 提取书籍: {item.get('title', book_id)}")

                elif "name" in item and "allBookIds" in item:
                    # 这是一个Archive文件夹
                    archive_name = item.get("name", f"文件夹{i}")
                    all_book_ids = item.get("allBookIds", [])

                    print(f"  📁 处理Archive: {archive_name} (包含 {len(all_book_ids)} 本书)")

                    # 对于 Archive 中的书籍，我们只能获取 bookId，无法获取完整信息
                    # 这些书籍需要通过后续的 syncBook 接口获取详细信息
                    for book_id in all_book_ids:
                        if book_id not in processed_book_ids:
                            processed_book_ids.add(book_id)
                            # 创建基础书籍信息，标记需要后续获取详情
                            basic_book = {
                                "bookId": book_id,
                                "title": f"Archive书籍_{book_id}",
                                "author": "需要获取详情",
                                "cover": "",
                                "category": f"来自文件夹: {archive_name}",
                                "finishReading": 0,
                                "newRatingDetail": "",
                                "readUpdateTime": int(time.time() * 1000),
                                "source": f"archive_{archive_name}_id_only",
                                "needsDetailFetch": True  # 标记需要获取详情
                            }
                            books.append(basic_book)

                    print(f"    ✅ 从Archive '{archive_name}' 提取了 {len(all_book_ids)} 个书籍ID")

                else:
                    # 未知类型的项目
                    print(f"  ❓ 未知项目类型: {list(item.keys())[:5]}")

            print(f"📚 HTML解析完成，共提取到 {len(books)} 本书籍")

            # 如果仍然没有找到书籍，输出调试信息
            if not books:
                print("⚠️ 未找到书籍数据，输出调试信息:")
                self._debug_initial_state_structure(initial_state)

                # 检查是否包含登录相关的关键词
                html_preview = html_content[:1000].replace('\n', ' ')
                if any(keyword in html_content.lower() for keyword in ['login', '登录', 'scan', '扫码']):
                    print("💡 检测到登录页面，可能需要重新登录")
                else:
                    print(f"HTML预览: {html_preview}...")

            return books

        except Exception as e:
            print(f"❌ HTML解析出错: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _debug_initial_state_structure(self, initial_state: Dict) -> None:
        """
        调试 __INITIAL_STATE__ 的数据结构，帮助发现可能遗漏的书籍数据源
        """
        try:
            print("🔍 调试 __INITIAL_STATE__ 结构:")

            # 检查顶层键
            top_keys = list(initial_state.keys())
            print(f"📋 顶层键: {top_keys}")

            # 检查 shelf 结构
            shelf = initial_state.get("shelf", {})
            if shelf:
                shelf_keys = list(shelf.keys())
                print(f"📚 shelf 键: {shelf_keys}")

                # 检查各个可能包含书籍信息的键
                for key in shelf_keys:
                    value = shelf[key]
                    if isinstance(value, list):
                        print(f"   📋 {key}: 数组长度 {len(value)}")
                        if value and isinstance(value[0], dict):
                            sample_keys = list(value[0].keys())[:5]
                            print(f"      示例键: {sample_keys}")
                    elif isinstance(value, dict):
                        dict_keys = list(value.keys())[:5]
                        print(f"   📋 {key}: 字典，键: {dict_keys}")
                    else:
                        print(f"   📋 {key}: {type(value).__name__}")

            # 检查其他可能包含书籍信息的顶层键
            for key in top_keys:
                if key != "shelf":
                    value = initial_state[key]
                    if isinstance(value, (list, dict)) and key.lower() in ['book', 'library', 'collection']:
                        print(f"🔍 发现可能相关的键: {key}")
                        if isinstance(value, list):
                            print(f"   📋 {key}: 数组长度 {len(value)}")
                        else:
                            print(f"   📋 {key}: 字典，键: {list(value.keys())[:5]}")

        except Exception as e:
            print(f"⚠️ 调试信息输出失败: {e}")

    def _check_for_more_books(self, shelf: Dict) -> None:
        """
        检查是否还有更多书籍需要加载（分页加载情况）
        """
        try:
            # 检查分页相关的字段
            loading_more = shelf.get("loadingMore", False)
            loading_more_error = shelf.get("loadingMoreError", False)
            has_more = shelf.get("hasMore", False)

            print(f"📄 分页状态检查:")
            print(f"   loadingMore: {loading_more}")
            print(f"   loadingMoreError: {loading_more_error}")
            print(f"   hasMore: {has_more}")

            # 检查是否有总数信息
            total_count = shelf.get("totalCount")
            if total_count:
                print(f"   总书籍数: {total_count}")

            # 检查是否有其他可能包含书籍信息的字段
            potential_book_fields = [
                "allBooks", "totalBooks", "bookList", "books",
                "libraryBooks", "userBooks", "bookIds"
            ]

            for field in potential_book_fields:
                value = shelf.get(field)
                if value:
                    if isinstance(value, list):
                        print(f"   发现书籍字段 {field}: 数组长度 {len(value)}")
                    elif isinstance(value, dict):
                        print(f"   发现书籍字段 {field}: 字典类型")
                    else:
                        print(f"   发现书籍字段 {field}: {type(value).__name__}")

        except Exception as e:
            print(f"⚠️ 分页检查失败: {e}")

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

    def _normalize_book_data_from_html(self, book_data: Dict, source_type: str = "unknown") -> Dict:
        """
        从HTML中提取的书籍数据进行标准化
        基于用户分析处理微信读书HTML响应中的完整书籍信息
        
        支持的字段:
        - bookId: 书籍唯一ID
        - title: 书名
        - author: 作者
        - translator: 译者
        - cover: 封面图片URL
        - category: 分类
        - totalWords: 总字数
        - finishReading: 是否读完 (1代表已读完，0代表未读完)
        - newRating: 评分 (例如 862 代表 86.2%)
        - secret: 是否为私密阅读
        """
        # 处理封面URL，确保使用完整的URL
        cover = book_data.get('cover', '')
        if cover:
            if cover.startswith('\\u002F\\u002F'):
                # 处理Unicode转义的URL
                cover = cover.replace('\\u002F', '/')
            if cover.startswith('//'):
                cover = 'https:' + cover
            elif not cover.startswith('http'):
                cover = 'https:' + cover

        # 处理评分信息
        new_rating = book_data.get('newRating', 0)
        new_rating_detail = book_data.get('newRatingDetail', {})

        # 定义评分映射，确保与前端getRatingImage函数一致
        valid_ratings = ['神作', '好评如潮', '脍炙人口', '值得一读', '褒贬不一', '不值一读']

        if isinstance(new_rating_detail, dict):
            rating_title = new_rating_detail.get('title', '')
            # 检查是否为有效的评分标题
            if rating_title in valid_ratings:
                rating_info = rating_title
                print(f"✅ HTML解析-有效评分: '{rating_title}' (书籍: {book_data.get('title', '')})")
            elif new_rating and rating_title:
                rating_info = f"{rating_title} ({new_rating}/1000)"
                print(f"📊 HTML解析-评分+数字: '{rating_info}' (书籍: {book_data.get('title', '')})")
            elif rating_title:
                rating_info = rating_title
                print(f"🔤 HTML解析-纯文本评分: '{rating_title}' (书籍: {book_data.get('title', '')})")
            elif new_rating:
                rating_info = f"评分: {new_rating}/1000"
                print(f"🔢 HTML解析-纯数字评分: '{rating_info}' (书籍: {book_data.get('title', '')})")
            else:
                rating_info = ''
        elif isinstance(new_rating_detail, str):
            # 如果是字符串，检查是否为有效的评分标题
            if new_rating_detail in valid_ratings:
                rating_info = new_rating_detail
                print(f"✅ HTML解析-字符串有效评分: '{rating_info}' (书籍: {book_data.get('title', '')})")
            else:
                rating_info = new_rating_detail
                print(f"⚠️ HTML解析-字符串未知评分: '{rating_info}' (书籍: {book_data.get('title', '')})")
        elif new_rating:
            rating_info = f"评分: {new_rating}/1000"
            print(f"🔢 HTML解析-仅数字评分: '{rating_info}' (书籍: {book_data.get('title', '')})")
        else:
            rating_info = ''

        # 处理作者信息（可能包含译者）
        author = book_data.get('author', '未知作者')
        translator = book_data.get('translator', '')
        if translator and translator != author:
            author_info = f"{author} (译: {translator})"
        else:
            author_info = author

        # 处理分类信息
        category = book_data.get('category', '')
        categories = book_data.get('categories', [])
        if not category and categories:
            # 从categories数组中提取第一个分类
            if isinstance(categories, list) and categories:
                first_cat = categories[0]
                if isinstance(first_cat, dict):
                    category = first_cat.get('title', '')

        # 处理字数信息
        total_words = book_data.get('totalWords', 0)
        if isinstance(total_words, str):
            try:
                total_words = int(total_words)
            except ValueError:
                total_words = 0

        # 处理阅读状态
        finish_reading = book_data.get('finishReading', 0)
        if isinstance(finish_reading, bool):
            finish_reading = 1 if finish_reading else 0

        return {
            "bookId": book_data.get('bookId', ''),
            "title": book_data.get('title', '未知书籍'),
            "author": author_info,
            "cover": cover,
            "category": category,
            "finishReading": finish_reading,
            "newRatingDetail": rating_info,
            "readUpdateTime": book_data.get('readUpdateTime', int(time.time() * 1000)),
            # 额外的完整信息
            "format": book_data.get('format', ''),
            "finished": book_data.get('finished', 0),
            "price": book_data.get('price', 0),
            "centPrice": book_data.get('centPrice', 0),
            "totalWords": total_words,
            "publishTime": book_data.get('publishTime', ''),
            "newRating": new_rating,
            "newRatingCount": book_data.get('newRatingCount', 0),
            "secret": book_data.get('secret', 0),  # 是否为私密阅读
            "intro": book_data.get('intro', ''),  # 书籍简介
            "publisher": book_data.get('publisher', ''),  # 出版社
            "isbn": book_data.get('isbn', ''),  # ISBN
            "lang": book_data.get('language', book_data.get('lang', '')),  # 语言
            "source": f"html_parsed_{source_type}"
        }

    def _normalize_web_book_info(self, raw_data: Dict, book_id: str) -> Dict:
        """
        标准化 /web/book/info 接口返回的书籍信息
        将微信读书web接口的数据格式转换为统一格式
        """
        try:
            # 处理基本信息
            title = raw_data.get('title', '未知书籍')
            author = raw_data.get('author', '未知作者')
            intro = raw_data.get('intro', '')

            # 处理封面
            cover = raw_data.get('cover', '')
            if cover and not cover.startswith('http'):
                cover = f"https://res.weread.qq.com{cover}" if not cover.startswith('//') else f"https:{cover}"

            # 处理分类信息
            category = raw_data.get('category', '')
            categories = raw_data.get('categories', [])
            if not category and categories and len(categories) > 0:
                category = categories[0].get('title', '')

            # 处理评分信息
            new_rating_detail = raw_data.get('newRatingDetail', {})
            if isinstance(new_rating_detail, dict):
                rating_title = new_rating_detail.get('title', '')
            else:
                rating_title = str(new_rating_detail) if new_rating_detail else ''

            # 处理译者信息
            translator_seg = raw_data.get('translatorSeg', [])
            if translator_seg and len(translator_seg) > 0:
                translator = translator_seg[0].get('words', '')
                if translator:
                    author = f"{author} (译: {translator})"

            # 构建标准化数据
            normalized_data = {
                "bookId": book_id,
                "title": title,
                "author": author,
                "cover": cover,
                "intro": intro,
                "publisher": raw_data.get('publisher', ''),
                "category": category,
                "finishReading": raw_data.get('finishReading', 0),
                "newRatingDetail": {"title": rating_title},
                "totalWords": raw_data.get('totalWords', 0),
                "publishTime": raw_data.get('publishTime', ''),
                "isbn": raw_data.get('isbn', ''),
                "newRating": raw_data.get('newRating', 0),
                "newRatingCount": raw_data.get('newRatingCount', 0),
                "paid": raw_data.get('paid', 0),
                "finished": raw_data.get('finished', 0),
                "secret": raw_data.get('secret', 0),
                "source": "web_book_info_normalized"
            }

            print(f"📚 成功标准化web书籍信息: {title} (评分: {rating_title})")
            return normalized_data

        except Exception as e:
            print(f"⚠️ 标准化web书籍信息失败 {book_id}: {e}")
            # 返回基础信息作为备选
            return {
                "bookId": book_id,
                "title": raw_data.get('title', '标准化失败'),
                "author": raw_data.get('author', '未知'),
                "cover": raw_data.get('cover', ''),
                "intro": raw_data.get('intro', ''),
                "publisher": raw_data.get('publisher', ''),
                "category": raw_data.get('category', ''),
                "finishReading": 0,
                "newRatingDetail": {"title": ""},
                "error": "标准化失败",
                "source": "web_book_info_fallback"
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
        fallback_apis = [
            {
                "name": "web_book_info",
                "url": f"{settings.weread_web_url}/web/book/info?bookId={book_id}",
                "headers": self.headers_web,
                "timeout": 15
            },
            {
                "name": "api_book_info",
                "url": f"{settings.weread_base_url}/book/info?bookId={book_id}",
                "headers": self.headers,
                "timeout": 10
            },
            {
                "name": "book_detail",
                "url": f"{settings.weread_base_url}/book/detail?bookId={book_id}",
                "headers": self.headers,
                "timeout": 10
            }
        ]

        last_error = None
        for api_config in fallback_apis:
            try:
                print(f"🔄 获取书籍信息: {book_id} - {api_config['name']}")
                r = requests.get(
                    api_config['url'],
                    headers=api_config['headers'],
                    verify=False,
                    timeout=api_config['timeout']
                )

                if r.status_code == 200:
                    try:
                        data = r.json()
                        print(f"✅ 书籍信息获取成功: {book_id} - {api_config['name']}")

                        # 对 web_book_info 的响应进行特殊处理
                        if api_config['name'] == 'web_book_info':
                            return self._normalize_web_book_info(data, book_id)

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
                    
                    # 对于401认证错误，直接返回基础信息，避免继续尝试
                    if r.status_code == 401:
                        print(f"🔐 认证失败，返回基础书籍信息: {book_id}")
                        return {
                            "bookId": book_id,
                            "title": "需要重新登录获取",
                            "author": "未知",
                            "cover": "",
                            "intro": "请重新登录以获取完整书籍信息",
                            "category": "",
                            "publisher": "",
                            "finishReading": 0,
                            "newRatingDetail": {"title": ""},
                            "error": "认证失败",
                            "source": "auth_error"
                        }
                    continue

            except Exception as e:
                print(f"⚠️ 获取书籍信息出错: {book_id} - {e}")
                last_error = e
                continue

        # 所有URL都失败了，返回基础信息而不是抛出异常
        error_msg = f"无法获取书籍信息 {book_id}: {str(last_error) if last_error else '未知错误'}"
        print(f"⚠️ {error_msg}，返回基础信息")
        
        return {
            "bookId": book_id,
            "title": "书籍信息暂时不可用",
            "author": "未知",
            "cover": "",
            "intro": "该书籍信息暂时无法获取，请稍后重试",
            "category": "",
            "publisher": "",
            "finishReading": 0,
            "newRatingDetail": {"title": ""},
            "error": "获取失败",
            "source": "api_error"
        }

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

    def sync_books(self, book_ids: List[str]) -> Dict:
        """
        使用 syncBook 接口批量同步书籍信息
        基于你提供的接口分析实现

        Args:
            book_ids: 书籍ID列表

        Returns:
            包含 books 和 bookProgress 的字典
        """
        try:
            url = f"{settings.weread_web_url}/web/shelf/syncBook"

            # 构建请求负载
            payload = {
                "bookIds": book_ids
            }

            print(f"🔄 同步 {len(book_ids)} 本书籍的详细信息")

            # 使用 POST 方法发送请求
            r = requests.post(
                url,
                headers=self.headers_post,
                json=payload,
                verify=False,
                timeout=30
            )

            if r.status_code == 200:
                try:
                    data = r.json()

                    # 验证响应数据结构
                    if isinstance(data, dict):
                        books = data.get('books', [])
                        book_progress = data.get('bookProgress', [])

                        print(f"✅ 成功同步 {len(books)} 本书籍信息，{len(book_progress)} 个阅读进度")

                        return {
                            'books': books,
                            'bookProgress': book_progress,
                            'source': 'syncBook_api'
                        }
                    else:
                        print(f"⚠️ syncBook 响应数据结构异常")
                        return {'books': [], 'bookProgress': [], 'error': '数据结构异常'}

                except ValueError as json_error:
                    print(f"⚠️ syncBook 返回的不是有效JSON: {json_error}")
                    return {'books': [], 'bookProgress': [], 'error': 'JSON解析失败'}

            elif r.status_code == 401:
                print(f"🔐 syncBook 认证失败，可能需要重新登录")
                return {'books': [], 'bookProgress': [], 'error': '认证失败'}

            else:
                print(f"⚠️ syncBook 请求失败，状态码: {r.status_code}")
                return {'books': [], 'bookProgress': [], 'error': f'请求失败: {r.status_code}'}

        except requests.exceptions.Timeout:
            print("⚠️ syncBook 请求超时")
            return {'books': [], 'bookProgress': [], 'error': '请求超时'}

        except requests.exceptions.ConnectionError:
            print("⚠️ syncBook 连接错误")
            return {'books': [], 'bookProgress': [], 'error': '连接错误'}

        except Exception as e:
            print(f"⚠️ syncBook 调用出错: {e}")
            return {'books': [], 'bookProgress': [], 'error': str(e)}

    def get_user_data_enhanced(self, user_vid: str) -> Dict:
        """
        增强版获取用户数据方法
        首先从 HTML 中获取所有 bookId，然后使用 syncBook 获取完整信息
        """
        try:
            # 1. 先通过 HTML 解析获取所有书籍ID
            print("📋 第一步: 获取书架HTML数据")
            html_data = self.get_user_data(user_vid)

            if not html_data or not html_data.get('books'):
                print("❌ 无法获取书架数据")
                raise Exception("❌ 无法获取书架数据")

            books_from_html = html_data['books']
            print(f"📚 从HTML获取到 {len(books_from_html)} 本书")

            # 2. 分析书籍类型：区分有完整信息的和只有ID的
            books_with_full_info = []
            books_need_details = []

            for book in books_from_html:
                book_id = book.get('bookId')
                if not book_id:
                    continue

                if book.get('needsDetailFetch', False):
                    # 这些书籍只有ID，需要通过syncBook获取详情
                    books_need_details.append(book_id)
                else:
                    # 这些书籍已有完整信息
                    books_with_full_info.append(book)

            print(f"📋 书籍分析结果:")
            print(f"   📖 已有完整信息: {len(books_with_full_info)} 本")
            print(f"   🔄 需要获取详情: {len(books_need_details)} 本")

            # 3. 如果有需要获取详情的书籍，使用 syncBook 批量获取
            synced_books = []
            all_book_progress = []

            if books_need_details:
                print(f"🔄 开始为 {len(books_need_details)} 本书籍获取详细信息")

                batch_size = 250  # 每批处理250本书，提高效率
                for i in range(0, len(books_need_details), batch_size):
                    batch_ids = books_need_details[i:i + batch_size]
                    print(f"   处理第 {i//batch_size + 1} 批，包含 {len(batch_ids)} 本书")

                    sync_result = self.sync_books(batch_ids)

                    if sync_result.get('books'):
                        synced_books.extend(sync_result['books'])

                    if sync_result.get('bookProgress'):
                        all_book_progress.extend(sync_result['bookProgress'])

                    # 短暂延迟，避免请求过于频繁（减少延迟提高效率）
                    import time
                    time.sleep(0.2)

                print(f"✅ 通过 syncBook 获取到 {len(synced_books)} 本书的详细信息")

            # 4. 合并数据：保持原有顺序（rawBooks在前，syncBook获取的在后）
            final_books = []

            # 首先添加有完整信息的书籍（来自rawBooks）
            final_books.extend(books_with_full_info)

            # 然后添加通过syncBook获取的书籍详情
            final_books.extend(synced_books)

            print(f"📚 最终合并结果: {len(final_books)} 本书")
            print(f"   📖 rawBooks: {len(books_with_full_info)} 本")
            print(f"   🔄 syncBook: {len(synced_books)} 本")

            # 创建增强数据响应
            enhanced_data = {
                'books': final_books,
                'bookProgress': all_book_progress,
                'user_vid': user_vid,
                'source': 'html_rawBooks_plus_syncBook_enhanced',
                'html_book_count': len(books_from_html),
                'rawbooks_count': len(books_with_full_info),
                'synced_book_count': len(synced_books),
                'total_count': len(final_books)
            }

            return enhanced_data

        except Exception as e:
            print(f"❌ 增强版数据获取失败: {e}")
            # 回退到原始HTML数据
            return self.get_user_data(user_vid)

    def get_markdown_content(self, book_id: str, is_all_chapter: int = 1) -> str:
        pass

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