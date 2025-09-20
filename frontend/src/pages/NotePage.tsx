import React, { useState, useEffect } from 'react'
import { useParams, useSearchParams, Link, useNavigate } from 'react-router-dom'
import { useQuery } from 'react-query'
import { ArrowLeft, Copy, Download } from 'lucide-react'
import toast from 'react-hot-toast'
import { notesAPI } from '../lib/api'
import { useAuthStore } from '../stores/authStore'

export default function NotePage() {
  const { bookId } = useParams<{ bookId: string }>()
  const [searchParams] = useSearchParams()
  const option = parseInt(searchParams.get('option') || '1')
  const [activeTab, setActiveTab] = useState<'preview' | 'markdown'>('preview')
  const navigate = useNavigate()
  const { logout } = useAuthStore()

  // 强制退出登录的函数
  const forceLogout = () => {
    console.log('🚨 NotePage - 强制退出登录');
    logout();
    navigate('/login', { replace: true, state: { message: '登录已过期，请重新登录' } });
  };

  const { data: response, isLoading, error } = useQuery(
    ['notes', bookId, option],
    () => notesAPI.getNotes(bookId!, option),
    { enabled: !!bookId }
  )

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
      const shouldRedirect = (
        (typeof detail === 'string' && (detail.includes('未找到 booksAndArchives 数据') || detail.includes('无法获取书架数据') || detail.includes('未知书籍信息'))) ||
        (typeof message === 'string' && (message.includes('未找到 booksAndArchives 数据') || message.includes('无法获取书架数据') || message.includes('未知书籍信息')))
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
      <div className="animate-pulse">
        <div className="h-8 bg-gray-300 rounded w-32 mb-8"></div>
        <div className="h-12 bg-gray-300 rounded mb-4"></div>
        <div className="space-y-4">
          <div className="h-4 bg-gray-300 rounded"></div>
          <div className="h-4 bg-gray-300 rounded w-5/6"></div>
          <div className="h-4 bg-gray-300 rounded w-4/6"></div>
        </div>
      </div>
    )
  }

  if (error || !noteData) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">该书籍无笔记或加载失败</div>
        <Link to={`/books/${bookId}`} className="btn btn-primary">
          返回书籍详情
        </Link>
      </div>
    )
  }

  return (
    <div>
      {/* Back Button */}
      <Link
        to={`/books/${bookId}`}
        className="inline-flex items-center space-x-2 text-gray-600 hover:text-gray-900 mb-8"
      >
        <ArrowLeft className="h-4 w-4" />
        <span>返回书籍详情</span>
      </Link>

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          《{noteData.book_title}》笔记
        </h1>
        <div className="flex items-center space-x-2">
          <button
            onClick={copyToClipboard}
            className="btn btn-secondary flex items-center space-x-2"
          >
            <Copy className="h-4 w-4" />
            <span>复制</span>
          </button>
          <button
            onClick={downloadMarkdown}
            className="btn btn-primary flex items-center space-x-2"
          >
            <Download className="h-4 w-4" />
            <span>下载</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('preview')}
            className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'preview'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            预览
          </button>
          <button
            onClick={() => setActiveTab('markdown')}
            className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'markdown'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Markdown
          </button>
        </nav>
      </div>

      {/* Content */}
      <div className="card p-6">
        {activeTab === 'preview' ? (
          <div
            className="prose prose-lg max-w-none"
            dangerouslySetInnerHTML={{ __html: noteData.html_content }}
          />
        ) : (
          <pre className="whitespace-pre-wrap text-sm text-gray-800 overflow-auto">
            {noteData.markdown_content}
          </pre>
        )}
      </div>
    </div>
  )
}