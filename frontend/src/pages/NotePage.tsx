import React, { useState, useEffect } from 'react'
import { useParams, useSearchParams, Link, useNavigate } from 'react-router-dom'
import { useQuery } from 'react-query'
import { ArrowLeft, Copy, Download, ChevronUp } from 'lucide-react'
import toast from 'react-hot-toast'
import { notesAPI } from '../lib/api'
import { useAuthStore } from '../stores/authStore'

// Improved Markdown Renderer Component
const MarkdownRenderer: React.FC<{ content: string }> = ({ content }) => {
  const processLine = (line: string, index: number): JSX.Element => {
    const trimmedLine = line.trim()

    // Headers
    if (trimmedLine.startsWith('#### ')) {
      return (
        <h4 key={index} className="text-lg font-medium text-gray-800 mb-3 mt-4">
          {trimmedLine.substring(5)}
        </h4>
      )
    } else if (trimmedLine.startsWith('### ')) {
      return (
        <h3 key={index} className="text-xl font-medium text-sky-600 mb-4 mt-6">
          {trimmedLine.substring(4)}
        </h3>
      )
    } else if (trimmedLine.startsWith('## ')) {
      return (
        <h2 key={index} className="text-2xl font-semibold text-sky-700 mb-6 mt-8">
          {trimmedLine.substring(3)}
        </h2>
      )
    } else if (trimmedLine.startsWith('# ')) {
      return (
        <h1 key={index} className="text-3xl font-bold text-sky-800 mb-8 mt-10 pb-4 border-b-2 border-sky-200">
          {trimmedLine.substring(2)}
        </h1>
      )
    }
    // Blockquotes
    else if (trimmedLine.startsWith('> ')) {
      return (
        <blockquote key={index} className="border-l-4 border-sky-400 bg-sky-50/50 pl-6 pr-4 py-4 my-6 text-gray-700 italic rounded-r-lg shadow-sm">
          {trimmedLine.substring(2)}
        </blockquote>
      )
    }
    // Empty lines
    else if (trimmedLine === '') {
      return <div key={index} className="mb-4"></div>
    }
    // Regular text with formatting
    else {
      return (
        <p key={index} className="leading-loose mb-6 text-gray-700 text-base">
          {formatInlineText(trimmedLine)}
        </p>
      )
    }
  }

  const formatInlineText = (text: string): React.ReactNode => {
    // Handle bold text **text**
    if (text.includes('**')) {
      const parts = text.split(/(\*\*[^*]+\*\*)/g)
      return parts.map((part, index) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return (
            <strong key={index} className="text-sky-700 font-semibold">
              {part.slice(2, -2)}
            </strong>
          )
        }
        return formatCode(part, `bold-${index}`)
      })
    }

    return formatCode(text, 'main')
  }

  const formatCode = (text: string, keyPrefix: string): React.ReactNode => {
    // Handle inline code `code`
    if (text.includes('`')) {
      const parts = text.split(/(`[^`]+`)/g)
      return parts.map((part, index) => {
        if (part.startsWith('`') && part.endsWith('`')) {
          return (
            <code key={`${keyPrefix}-${index}`} className="bg-gray-100 text-sky-800 px-2 py-1 rounded text-sm font-medium">
              {part.slice(1, -1)}
            </code>
          )
        }
        return part
      })
    }

    return text
  }

  if (!content) return <div>暂无内容</div>

  const lines = content.split('\n')
  const elements = lines.map((line, index) => processLine(line, index))

  return <div className="markdown-content space-y-1">{elements}</div>
}

export default function NotePage() {
  const { bookId } = useParams<{ bookId: string }>()
  const [searchParams, setSearchParams] = useSearchParams()
  const option = parseInt(searchParams.get('option') || '1')
  const [activeTab, setActiveTab] = useState<'preview' | 'markdown'>('preview')
  const [noteMode, setNoteMode] = useState<1 | 2>(option as 1 | 2)
  const [showScrollTop, setShowScrollTop] = useState(false)
  const [readingProgress, setReadingProgress] = useState(0)
  const navigate = useNavigate()
  const { logout } = useAuthStore()

  // 强制退出登录的函数
  const forceLogout = () => {
    console.log('🚨 NotePage - 强制退出登录');
    logout();
    navigate('/login', { replace: true, state: { message: '登录已过期，请重新登录' } });
  };

  const { data: response, isLoading, error, refetch } = useQuery(
    ['notes', bookId, noteMode],
    () => notesAPI.getNotes(bookId!, noteMode),
    { enabled: !!bookId }
  )

  // 更新URL参数和重新获取数据
  const handleNoteModeChange = (newMode: 1 | 2) => {
    setNoteMode(newMode)
    setSearchParams({ option: newMode.toString() })
  }

  // 滚动监听
  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 300)

      // 计算阅读进度
      const scrollTop = window.scrollY
      const docHeight = document.documentElement.scrollHeight - window.innerHeight
      const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0
      setReadingProgress(Math.min(100, Math.max(0, progress)))
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // 键盘快捷键
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case '1':
            e.preventDefault()
            handleNoteModeChange(1)
            break
          case '2':
            e.preventDefault()
            handleNoteModeChange(2)
            break
          case 'c':
            if (e.shiftKey) {
              e.preventDefault()
              copyToClipboard()
            }
            break
          case 'd':
            if (e.shiftKey) {
              e.preventDefault()
              downloadMarkdown()
            }
            break
        }
      }
      if (e.key === 'Tab') {
        e.preventDefault()
        setActiveTab(activeTab === 'preview' ? 'markdown' : 'preview')
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [activeTab, noteMode])

  // 返回顶部
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const noteData = response?.data?.data

  // 检查错误并自动返回登录界面
  useEffect(() => {
    if (error) {
      console.log('🚨 NotePage - 检测到错误:', error);
      const detail = (error as any).response?.data?.detail;
      const message = (error as any).message;
      console.log('🔍 错误详情 - detail:', detail);
      console.log('🔍 错误详情 - message:', message);

      // 检查是否包含需要自动跳转的错误信息
      const errorPatterns = [
        '未找到 booksAndArchives 数据',
        '无法获取书架数据',
        '未知书籍信息',
        '未知书籍',
        'BookId is required',
        'book not found',
        '书籍不存在',
        '登录已过期',
        'unauthorized',
        'cookie失效',
        'Failed to get notes',
        '无法获取笔记',
        'UNKNOWN_BOOK',
        'LOGIN_EXPIRED'
      ];

      // 检查响应数据中的错误字段
      const responseError = (error as any).response?.data?.data?.error;

      const shouldRedirect = errorPatterns.some(pattern =>
        (typeof detail === 'string' && detail.toLowerCase().includes(pattern.toLowerCase())) ||
        (typeof message === 'string' && message.toLowerCase().includes(pattern.toLowerCase())) ||
        (typeof responseError === 'string' && responseError.toLowerCase().includes(pattern.toLowerCase()))
      );

      if (shouldRedirect) {
        console.log('✅ 检测到Cookie失效相关错误，强制退出登录');
        forceLogout();
      }
    }
  }, [error, navigate]);

  const copyToClipboard = async () => {
    if (noteData?.markdown_content) {
      try {
        await navigator.clipboard.writeText(noteData.markdown_content)
        toast.success('已复制到剪贴板')
      } catch (error) {
        toast.error('复制失败')
      }
    }
  }

  const downloadMarkdown = () => {
    if (noteData?.markdown_content) {
      const blob = new Blob([noteData.markdown_content], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${noteData.book_title}_笔记.md`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      toast.success('下载完成')
    }
  }


  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50">
        {/* Header Skeleton */}
        <div className="bg-gradient-to-r from-sky-600 to-sky-700 shadow-lg border-b border-sky-500/20">
          <div className="max-w-4xl mx-auto px-4 py-8">
            <div className="h-6 bg-white/20 rounded w-32 mb-6"></div>
            <div className="h-8 bg-white/30 rounded w-64 mb-2"></div>
            <div className="h-5 bg-white/20 rounded w-24"></div>
          </div>
        </div>

        {/* Content Skeleton */}
        <div className="max-w-4xl mx-auto px-4 -mt-8 relative z-10">
          <div className="bg-white rounded-2xl shadow-xl p-6 mb-8">
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
                <div className="text-blue-700 text-lg font-medium mb-2">
                  正在获取{noteMode === 1 ? '完整' : '精选'}笔记...
                </div>
                <div className="text-gray-500 text-sm">
                  请稍候，正在处理书籍内容
                </div>
              </div>
            </div>
          </div>

          {/* Content skeleton */}
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-8 animate-pulse">
            <div className="space-y-6">
              <div className="h-6 bg-gray-200 rounded w-3/4"></div>
              <div className="space-y-3">
                <div className="h-4 bg-gray-200 rounded"></div>
                <div className="h-4 bg-gray-200 rounded w-5/6"></div>
                <div className="h-4 bg-gray-200 rounded w-4/6"></div>
              </div>
              <div className="h-6 bg-gray-200 rounded w-2/3"></div>
              <div className="space-y-3">
                <div className="h-4 bg-gray-200 rounded w-full"></div>
                <div className="h-4 bg-gray-200 rounded w-4/5"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error || !noteData) {
    return (
      <div className="min-h-screen bg-slate-50">
        {/* Header */}
        <div className="bg-gradient-to-r from-sky-600 to-sky-700 shadow-lg border-b border-sky-500/20 text-white">
          <div className="max-w-4xl mx-auto px-4 py-8">
            <Link
              to={`/books/${bookId}`}
              className="inline-flex items-center space-x-2 text-white/80 hover:text-white mb-6 transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>返回书籍详情</span>
            </Link>

            <div className="mb-6">
              <h1 className="text-3xl md:text-4xl font-bold mb-2">
                笔记获取失败
              </h1>
              <p className="text-white/80 text-lg">遇到了一些问题</p>
            </div>
          </div>
        </div>

        {/* Error Content */}
        <div className="max-w-4xl mx-auto px-4 -mt-8 relative z-10">
          <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
            <div className="bg-slate-50 rounded-2xl p-8 border border-slate-200">
              <div className="text-6xl mb-4">⚠️</div>
              <div className="text-gray-800 text-xl font-medium mb-2">
                {noteMode === 1 ? '完整笔记' : '精选笔记'}暂不可用
              </div>
              <div className="text-gray-600 text-sm mb-6">
                该书籍可能没有笔记，或者当前笔记模式下没有内容
              </div>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  onClick={() => handleNoteModeChange(noteMode === 1 ? 2 : 1)}
                  className="px-6 py-3 bg-sky-600 hover:bg-sky-700 text-white rounded-lg font-medium transition-colors shadow-md"
                >
                  尝试{noteMode === 1 ? '精选' : '完整'}笔记模式
                </button>
                <Link
                  to={`/books/${bookId}`}
                  className="px-6 py-3 bg-slate-600 hover:bg-slate-700 text-white rounded-lg font-medium transition-colors shadow-md text-center"
                >
                  返回书籍详情
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Reading Progress Bar */}
      <div className="fixed top-0 left-0 w-full h-1 bg-gray-200 z-50">
        <div
          className="h-full bg-sky-600 transition-all duration-300 ease-out"
          style={{ width: `${readingProgress}%` }}
        />
      </div>

      {/* Header Section */}
      <div className="bg-gradient-to-r from-sky-600 to-sky-700 shadow-lg border-b border-sky-500/20 text-white">
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Back Button */}
          <Link
            to={`/books/${bookId}`}
            className="inline-flex items-center space-x-2 text-white/80 hover:text-white mb-6 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>返回书籍详情</span>
          </Link>

          {/* Title Section */}
          <div className="mb-6">
            <h1 className="text-3xl md:text-4xl font-bold mb-2">
              《{noteData.book_title}》
            </h1>
            <p className="text-white/80 text-lg">阅读笔记</p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 -mt-8 relative z-10">

        {/* Control Panel */}
        <div className="bg-white rounded-2xl shadow-xl p-6 mb-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            {/* Left: Mode Selector */}
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-gray-700">笔记模式：</span>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleNoteModeChange(1)}
                  className={`px-4 py-2 text-sm rounded-lg font-medium transition-all duration-200 ${
                    noteMode === 1
                      ? 'bg-blue-600 text-white shadow-md hover:bg-blue-700 scale-105'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200 hover:scale-105'
                  }`}
                  title="显示所有主要章节 (Ctrl+1)"
                >
                  完整笔记
                </button>
                <button
                  onClick={() => handleNoteModeChange(2)}
                  className={`px-4 py-2 text-sm rounded-lg font-medium transition-all duration-200 ${
                    noteMode === 2
                      ? 'bg-orange-500 text-white shadow-md hover:bg-orange-600 scale-105'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200 hover:scale-105'
                  }`}
                  title="仅显示有笔记的章节 (Ctrl+2)"
                >
                  精选笔记
                </button>
              </div>
            </div>

            {/* Right: Actions and Stats */}
            <div className="flex items-center space-x-4">
              {noteData?.markdown_content && (
                <div className="text-xs text-gray-500 bg-gray-100 px-3 py-2 rounded-lg">
                  约 {Math.round(noteData.markdown_content.length / 500)} 分钟阅读
                </div>
              )}
              <button
                onClick={copyToClipboard}
                className="flex items-center space-x-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-all duration-200 shadow-md hover:shadow-lg hover:scale-105 active:scale-95"
                title="复制笔记内容 (Ctrl+Shift+C)"
              >
                <Copy className="h-4 w-4" />
                <span>复制</span>
              </button>
              <button
                onClick={downloadMarkdown}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all duration-200 shadow-md hover:shadow-lg hover:scale-105 active:scale-95"
                title="下载为Markdown文件 (Ctrl+Shift+D)"
              >
                <Download className="h-4 w-4" />
                <span>下载</span>
              </button>
            </div>
          </div>

          {/* Mode Description */}
          <div className="mt-4 text-sm text-gray-600 bg-gray-50 px-4 py-2 rounded-lg">
            {noteMode === 1 ? '📚 显示所有主要章节，包括没有笔记的章节' : '✨ 仅显示有笔记或标注的章节'}
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-2xl shadow-lg mb-8 overflow-hidden">
          <div className="flex">
            <button
              onClick={() => setActiveTab('preview')}
              className={`flex-1 py-4 px-6 text-center font-medium transition-all duration-200 ${
                activeTab === 'preview'
                  ? 'bg-blue-600 text-white shadow-md transform scale-105'
                  : 'bg-white text-gray-600 hover:bg-gray-50 hover:scale-105'
              }`}
              title="预览渲染后的笔记 (Tab)"
            >
              📖 预览模式
            </button>
            <button
              onClick={() => setActiveTab('markdown')}
              className={`flex-1 py-4 px-6 text-center font-medium transition-all duration-200 ${
                activeTab === 'markdown'
                  ? 'bg-gray-800 text-white shadow-md transform scale-105'
                  : 'bg-white text-gray-600 hover:bg-gray-50 hover:scale-105'
              }`}
              title="查看Markdown源码 (Tab)"
            >
              📝 Markdown源码
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden mb-8">
          {(!noteData.markdown_content || noteData.markdown_content.trim() === '') ? (
            <div className="p-12 text-center">
              <div className="bg-slate-50 rounded-2xl p-8 border border-slate-200">
                <div className="text-6xl mb-4">📝</div>
                <div className="text-gray-700 text-xl font-medium mb-2">暂无笔记内容</div>
                <div className="text-gray-500 text-sm mb-6">
                  {noteMode === 1 ? '该书籍还没有任何笔记或标注' : '在当前模式下没有找到有笔记的章节'}
                </div>
                {noteMode === 2 && (
                  <button
                    onClick={() => handleNoteModeChange(1)}
                    className="px-6 py-3 bg-sky-600 hover:bg-sky-700 text-white rounded-lg font-medium transition-colors shadow-md"
                  >
                    查看完整笔记
                  </button>
                )}
              </div>
            </div>
          ) : activeTab === 'preview' ? (
            <div className="p-8 lg:p-12">
              <div className="max-w-4xl mx-auto">
                <MarkdownRenderer content={noteData.markdown_content} />
              </div>
            </div>
          ) : (
            <div className="bg-slate-900 text-gray-100">
              <div className="p-6 border-b border-slate-700 bg-slate-800">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 rounded-full bg-red-500"></div>
                      <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                      <div className="w-3 h-3 rounded-full bg-green-500"></div>
                    </div>
                    <span className="text-sm font-mono text-gray-300">markdown</span>
                  </div>
                  <div className="text-xs text-gray-400 font-mono">
                    {noteData.markdown_content?.split('\n').length || 0} 行
                  </div>
                </div>
              </div>
              <div className="p-8 overflow-auto max-h-[80vh]">
                <pre className="whitespace-pre-wrap text-sm font-mono leading-loose text-gray-100 selection:bg-sky-500/30">
                  {noteData.markdown_content}
                </pre>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center py-8">
          <div className="text-gray-400 text-sm mb-4">
            使用微信读书工具生成 · 享受阅读的乐趣
          </div>

          {/* Keyboard shortcuts hint */}
          <div className="bg-gray-50 rounded-lg p-4 max-w-2xl mx-auto">
            <div className="text-gray-600 text-xs font-medium mb-2">🔥 快捷键提示</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-gray-500">
              <div><kbd className="px-2 py-1 bg-gray-200 rounded text-gray-700">Ctrl+1</kbd> 完整笔记</div>
              <div><kbd className="px-2 py-1 bg-gray-200 rounded text-gray-700">Ctrl+2</kbd> 精选笔记</div>
              <div><kbd className="px-2 py-1 bg-gray-200 rounded text-gray-700">Tab</kbd> 切换预览</div>
              <div><kbd className="px-2 py-1 bg-gray-200 rounded text-gray-700">Ctrl+Shift+C</kbd> 复制</div>
            </div>
          </div>
        </div>

        {/* Scroll to top button */}
        {showScrollTop && (
          <button
            onClick={scrollToTop}
            className="fixed bottom-8 right-8 bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-full shadow-lg transition-all duration-300 hover:scale-110 z-50"
            title="返回顶部"
          >
            <ChevronUp className="h-6 w-6" />
          </button>
        )}
      </div>
    </div>
  )
}