import { useForm } from 'react-hook-form'
import { useMutation, useQueryClient } from 'react-query'
import { useLocation, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { BookOpen, ExternalLink, HelpCircle } from 'lucide-react'
import { authAPI } from '../lib/api'
import { useAuthStore } from '../stores/authStore'
import { useEffect } from 'react'

interface LoginForm {
  cookieString: string
}

export default function LoginPage() {
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const location = useLocation()

  useEffect(() => {
    if (location.state?.message) {
      toast.error(location.state.message)
      // Clear the state to prevent the message from showing again on refresh
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [location.state, navigate, location.pathname])

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>()

  const loginMutation = useMutation(authAPI.login, {
    onSuccess: async (response) => {
      if (response.data.success) {
        const { access_token, user, cached_books_count, cache_success } = response.data.data
        setAuth(access_token, user)

        // 显示详细的登录成功信息
        if (cache_success && cached_books_count > 0) {
          toast.success(`登录成功！已自动加载 ${cached_books_count} 本书籍`)
        } else {
          toast.success('登录成功！正在加载书架数据...')
        }

        // 清除所有相关的查询缓存，确保首页获取最新数据
        queryClient.removeQueries(['books'])
        console.log('📚 已清除书籍缓存，首页将重新获取数据')

        // 设置登录标记，让首页知道需要刷新数据
        sessionStorage.setItem('justLoggedIn', 'true')

        // 延迟一点时间显示成功消息，然后导航到首页
        setTimeout(() => {
          navigate('/', { replace: true, state: { fromLogin: true } })
        }, 1500)
      } else {
        toast.error(response.data.message || '登录失败')
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || '登录失败，请检查网络连接')
    },
  })

  const parseCookieString = (cookieString: string) => {
    const cookies: Record<string, string> = {}
    
    // 解析Cookie字符串
    cookieString.split(';').forEach(cookie => {
      const [name, value] = cookie.trim().split('=')
      if (name && value) {
        // 对URL编码的值进行解码（特别是用户名和头像）
        try {
          cookies[name] = decodeURIComponent(value)
        } catch {
          // 如果解码失败，使用原始值
          cookies[name] = value
        }
      }
    })
    
    return {
      wr_gid: cookies.wr_gid || '',
      wr_vid: cookies.wr_vid || '',
      wr_skey: cookies.wr_skey || '',
      wr_rt: cookies.wr_rt || '',
      wr_name: cookies.wr_name || '',
      wr_avatar: cookies.wr_avatar || '',
      wr_localvid: cookies.wr_localvid || '',
      wr_gender: cookies.wr_gender || '',
      wr_pf: cookies.wr_pf || '0'
    }
  }

  const onSubmit = (data: LoginForm) => {
    const parsedCookies = parseCookieString(data.cookieString)
    
    // 检查必要字段
    const requiredFields = ['wr_gid', 'wr_vid', 'wr_skey', 'wr_rt']
    const missingFields = requiredFields.filter(field => !parsedCookies[field as keyof typeof parsedCookies])
    
    if (missingFields.length > 0) {
      toast.error(`Cookie中缺少必要字段: ${missingFields.join(', ')}`)
      return
    }
    
    loginMutation.mutate(parsedCookies)
  }


  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <div className="flex justify-center mb-6">
              <div className="w-16 h-16 rounded-2xl overflow-hidden shadow-lg">
                <img
                  src="/src/static/images/weread.png"
                  alt="微信读书"
                  className="w-full h-full object-cover rounded-2xl"
                />
              </div>
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent mb-3">WereadTool</h1>
            <p className="text-xl text-gray-600 mb-4">微信读书助手</p>
          </div>

          <div className="grid lg:grid-cols-2 gap-12 items-start">
            {/* 左侧：登录表单 */}
            <div className="order-2 lg:order-1">
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl p-8 border border-white/20">
                <div className="text-center mb-8">
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">粘贴Cookie登录</h2>
                  <p className="text-gray-600">将右侧获取的完整Cookie字符串粘贴到下方</p>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                  <div>
                    <label htmlFor="cookieString" className="block text-sm font-semibold text-gray-700 mb-3">
                      Cookie 字符串
                    </label>
                    <textarea
                      {...register('cookieString', { 
                        required: 'Cookie字符串不能为空',
                        validate: {
                          hasRequiredFields: (value) => {
                            const cookies = value.split(';').map(c => c.trim().split('=')[0])
                            const requiredFields = ['wr_gid', 'wr_vid', 'wr_skey', 'wr_rt']
                            const missingFields = requiredFields.filter(field => !cookies.includes(field))
                            return missingFields.length === 0 || `缺少必要字段: ${missingFields.join(', ')}`
                          }
                        }
                      })}
                      rows={6}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition-colors font-mono text-sm bg-white/50"
                      placeholder="请粘贴从Network面板获取的完整Cookie字符串，例如：
pgv_pvid=123; wr_gid=209373411; wr_vid=67890; wr_skey=abc123; wr_rt=def456; wr_fp=982590028; 其他cookie..."
                    />
                    {errors.cookieString && (
                      <p className="mt-2 text-sm text-red-600">{errors.cookieString.message}</p>
                    )}
                    
                    <div className="mt-3 p-3 bg-sky-50 rounded-lg border border-sky-200">
                      <div className="flex items-start gap-2">
                        <div className="flex-shrink-0 w-5 h-5 bg-sky-500 text-white rounded-full flex items-center justify-center text-xs font-bold mt-0.5">
                          ℹ
                        </div>
                        <div className="text-sm text-sky-800">
                          <p className="font-medium mb-1">提示：</p>
                          <ul className="space-y-1 text-sky-700">
                            <li>• 必须从Network面板获取Cookie（document.cookie不完整）</li>
                            <li>• 确保包含 wr_gid、wr_vid、wr_skey、wr_rt 四个字段</li>
                            <li>• 直接粘贴完整字符串，系统会自动解析</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={loginMutation.isLoading}
                    className="w-full bg-gradient-to-r from-sky-600 to-sky-700 text-white py-4 px-6 rounded-lg font-semibold hover:from-sky-700 hover:to-sky-800 focus:ring-2 focus:ring-sky-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl text-lg"
                  >
                    {loginMutation.isLoading ? (
                      <div className="flex items-center justify-center gap-3">
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        解析Cookie并登录中...
                      </div>
                    ) : (
                      '解析Cookie并登录'
                    )}
                  </button>
                </form>
              </div>
            </div>

            {/* 右侧：获取指导 */}
            <div className="order-1 lg:order-2">
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 overflow-hidden">
                <div className="bg-gradient-to-r from-sky-600 to-sky-700 px-6 py-4">
                  <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <HelpCircle className="h-5 w-5" />
                    Cookie 获取指导
                  </h3>
                  <p className="text-sky-100 text-sm mt-1">参考 mcp-server-weread 项目方法</p>
                </div>

                <div className="p-6">
                  <div className="space-y-6">
                    {/* 步骤1 */}
                    <div className="flex gap-4">
                      <div className="flex-shrink-0 w-8 h-8 bg-sky-100 text-sky-600 rounded-full flex items-center justify-center font-bold text-sm">
                        1
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-2">访问微信读书</h4>
                        <p className="text-gray-600 text-sm mb-3">在Chrome浏览器中打开微信读书网页版</p>
                        <button
                          onClick={() => window.open('https://weread.qq.com', '_blank')}
                          className="inline-flex items-center gap-2 px-4 py-2 bg-sky-600 text-white text-sm rounded-lg hover:bg-sky-700 transition-colors"
                        >
                          <ExternalLink className="h-4 w-4" />
                          打开微信读书
                        </button>
                      </div>
                    </div>

                    {/* 步骤2 */}
                    <div className="flex gap-4">
                      <div className="flex-shrink-0 w-8 h-8 bg-sky-100 text-sky-600 rounded-full flex items-center justify-center font-bold text-sm">
                        2
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-2">完成登录</h4>
                        <p className="text-gray-600 text-sm">使用微信扫码完成登录</p>
                      </div>
                    </div>

                    {/* 步骤3 */}
                    <div className="flex gap-4">
                      <div className="flex-shrink-0 w-8 h-8 bg-sky-100 text-sky-600 rounded-full flex items-center justify-center font-bold text-sm">
                        3
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-2">获取Cookie</h4>
                        <div className="space-y-3">
                          <div className="bg-red-50 rounded-lg p-4 border-l-4 border-red-400">
                            <p className="text-sm text-red-800 mb-2">
                              <strong>⚠️ 注意</strong>：<code className="bg-red-100 px-1 rounded">document.cookie</code> 方法无法获取完整信息
                            </p>
                            <p className="text-xs text-red-700">
                              某些关键Cookie（wr_vid、wr_skey、wr_rt）是HttpOnly的，JavaScript无法访问
                            </p>
                          </div>

                          <div className="bg-green-50 rounded-lg p-4">
                            <p className="text-sm text-green-800 mb-3">
                              <strong>✅ 正确方法</strong>：通过Network面板获取完整Cookie
                            </p>
                            <ol className="text-sm text-green-700 space-y-2">
                              <li className="flex gap-2">
                                <span className="flex-shrink-0 font-bold">1.</span>
                                <span>按 <kbd className="px-1 py-0.5 bg-green-200 rounded text-xs">F12</kbd> 打开开发者工具</span>
                              </li>
                              <li className="flex gap-2">
                                <span className="flex-shrink-0 font-bold">2.</span>
                                <span>切换到 <strong>Network</strong> 标签页</span>
                              </li>
                              <li className="flex gap-2">
                                <span className="flex-shrink-0 font-bold">3.</span>
                                <span>刷新页面（Ctrl+R 或 F5）</span>
                              </li>
                              <li className="flex gap-2">
                                <span className="flex-shrink-0 font-bold">4.</span>
                                <span>找到 <code className="bg-green-100 px-1 rounded">weread.qq.com</code> 请求并点击</span>
                              </li>
                              <li className="flex gap-2">
                                <span className="flex-shrink-0 font-bold">5.</span>
                                <span>在右侧面板找到 <strong>Headers</strong> → <strong>Request Headers</strong> → <strong>Cookie</strong></span>
                              </li>
                              <li className="flex gap-2">
                                <span className="flex-shrink-0 font-bold">6.</span>
                                <span>复制完整的Cookie值到左侧文本框</span>
                              </li>
                            </ol>
                          </div>

                          <div className="bg-sky-50 rounded-lg p-4 border border-sky-200">
                            <p className="text-sm text-sky-800 mb-2">
                              <strong>💡 提示</strong>：寻找包含以下字段的Cookie字符串
                            </p>
                            <div className="text-xs text-sky-700 grid grid-cols-2 gap-1">
                              <span>• wr_gid=...</span>
                              <span>• wr_vid=...</span>
                              <span>• wr_skey=...</span>
                              <span>• wr_rt=...</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* 必要字段提示 */}
                    <div className="bg-green-50 border-l-4 border-green-400 p-4 rounded">
                      <div className="flex">
                        <div className="ml-3">
                          <h4 className="text-sm font-semibold text-green-800">必要字段说明</h4>
                          <div className="mt-2 text-sm text-green-700">
                            <p className="mb-2">系统会自动从Cookie字符串中提取以下字段：</p>
                            <ul className="list-disc list-inside space-y-1">
                              <li><code className="bg-green-100 px-1 rounded">wr_gid</code> - 用户组ID</li>
                              <li><code className="bg-green-100 px-1 rounded">wr_vid</code> - 用户ID</li>
                              <li><code className="bg-green-100 px-1 rounded">wr_skey</code> - 会话密钥</li>
                              <li><code className="bg-green-100 px-1 rounded">wr_rt</code> - 刷新令牌</li>
                            </ul>
                            <p className="mt-2 text-xs text-green-600">
                              ✅ 从Network面板复制，无需手动分离字段
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}