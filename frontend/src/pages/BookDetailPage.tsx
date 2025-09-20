import React, { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery } from 'react-query'
import { ArrowLeft, FileText, Download, Star, Book as BookIcon, X } from 'lucide-react'
import { booksAPI } from '../lib/api'
import { useAuthStore } from '../stores/authStore'

export default function BookDetailPage() {
  const { bookId } = useParams<{ bookId: string }>()
  const [showImageModal, setShowImageModal] = useState(false)
  const navigate = useNavigate()
  const { logout } = useAuthStore()

  // 获取高分辨率封面图片URL
  const getHighResolutionCover = (coverUrl: string) => {
    if (coverUrl && coverUrl.includes('t6_')) {
      return coverUrl.replace('t6_', 't9_')
    }
    return coverUrl
  }

  // 强制退出登录的函数
  const forceLogout = () => {
    console.log('🚨 BookDetail - 强制退出登录');
    logout();
    navigate('/login', { replace: true, state: { message: '登录已过期，请重新登录' } });
  };

  // 添加调试日志
  console.log('📚 BookDetailPage - bookId:', bookId)
  console.log('📚 BookDetailPage - bookId type:', typeof bookId)
  console.log('📚 BookDetailPage - bookId enabled:', !!bookId)

  // 验证bookId有效性
  const isValidBookId = bookId &&
                       typeof bookId === 'string' &&
                       bookId.trim() !== '' &&
                       bookId !== 'undefined' &&
                       bookId !== 'null'

  const { data: response, isLoading, error } = useQuery(
    ['book', bookId],
    () => {
      console.log('🔄 API调用 - getBook bookId:', bookId)
      console.log('   📋 bookId验证:', {
        exists: !!bookId,
        type: typeof bookId,
        length: bookId?.length,
        trimmed: bookId?.trim(),
        isValid: isValidBookId
      })

      if (!isValidBookId) {
        console.error('❌ BookId无效，无法调用API')
        throw new Error('BookId is invalid or empty')
      }

      return booksAPI.getBook(bookId.trim())
    },
    {
      enabled: isValidBookId,
      cacheTime: 0,  // 不缓存
      staleTime: 0,  // 立即过期
      refetchOnMount: true,  // 每次挂载都重新获取
      refetchOnWindowFocus: false,  // 窗口聚焦时不重新获取
      retry: (failureCount, error) => {
        console.log('❌ API调用失败:', error, 'failureCount:', failureCount)
        // 如果是bookId无效错误，不重试
        if (error?.message?.includes('invalid') || error?.message?.includes('empty')) {
          return false
        }
        return failureCount < 2
      },
      onSuccess: (data) => {
        console.log('✅ API调用成功:', data)
      },
      onError: (error) => {
        console.log('❌ API调用错误:', error)
      }
    }
  )

  const book = response?.data?.data

  // 检查错误并自动返回登录界面
  useEffect(() => {
    if (error) {
      console.log('🚨 BookDetailPage - 检测到错误:', error);
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

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
        <div className="max-w-6xl mx-auto px-4 py-8">
          {/* Back Button Skeleton */}
          <div className="animate-pulse">
            <div className="inline-flex items-center space-x-3 bg-white/80 backdrop-blur-sm px-4 py-3 rounded-xl shadow-lg mb-8 border border-white/20">
              <div className="bg-gradient-to-r from-sky-200 to-sky-300 rounded-lg p-1.5">
                <div className="h-4 w-4 bg-white/50 rounded"></div>
              </div>
              <div className="h-4 w-16 bg-gradient-to-r from-gray-200 to-gray-300 rounded"></div>
            </div>
          </div>

          {/* Content Skeleton */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 overflow-hidden">
            <div className="grid md:grid-cols-3 gap-8 p-8 animate-pulse">
              {/* Cover Skeleton */}
              <div className="flex justify-center">
                <div className="bg-gradient-to-br from-gray-200 via-gray-100 to-gray-200 h-96 w-full max-w-xs rounded-xl shadow-2xl relative overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent -skew-x-12 animate-pulse-shimmer"></div>
                </div>
              </div>

              {/* Info Skeleton */}
              <div className="md:col-span-2 space-y-6">
                {/* Title and Author */}
                <div className="space-y-3">
                  <div className="h-10 bg-gradient-to-r from-gray-200 to-gray-300 rounded-lg w-4/5"></div>
                  <div className="h-6 bg-gradient-to-r from-gray-200 to-gray-300 rounded w-1/2"></div>
                </div>

                {/* Tags */}
                <div className="flex space-x-3">
                  <div className="h-8 w-24 bg-gradient-to-r from-sky-200 to-sky-300 rounded-full"></div>
                  <div className="h-8 w-20 bg-gradient-to-r from-yellow-200 to-yellow-300 rounded-full"></div>
                </div>

                {/* Intro */}
                <div className="bg-gradient-to-r from-gray-100 to-blue-100 rounded-xl p-6 border border-gray-200/50">
                  <div className="h-5 bg-gradient-to-r from-gray-200 to-gray-300 rounded w-32 mb-3"></div>
                  <div className="space-y-2">
                    <div className="h-4 bg-gradient-to-r from-gray-200 to-gray-300 rounded"></div>
                    <div className="h-4 bg-gradient-to-r from-gray-200 to-gray-300 rounded"></div>
                    <div className="h-4 bg-gradient-to-r from-gray-200 to-gray-300 rounded w-3/4"></div>
                  </div>
                </div>

                {/* Publisher */}
                <div className="bg-gray-100 rounded-lg px-4 py-3 border border-gray-200/50">
                  <div className="h-4 bg-gradient-to-r from-gray-200 to-gray-300 rounded w-1/3"></div>
                </div>

                {/* Action Buttons */}
                <div className="space-y-4 pt-4">
                  <div className="h-5 bg-gradient-to-r from-gray-200 to-gray-300 rounded w-24 mb-3"></div>
                  <div className="grid sm:grid-cols-1 lg:grid-cols-2 gap-4">
                    <div className="h-16 bg-gradient-to-r from-sky-200 to-sky-300 rounded-xl shadow-lg"></div>
                    <div className="h-16 bg-gradient-to-r from-gray-200 to-gray-300 rounded-xl shadow-lg"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // 如果bookId无效，显示特殊错误页面
  if (!isValidBookId) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-8 bg-gradient-to-br from-white/95 to-yellow-50/80 backdrop-blur-sm rounded-2xl shadow-xl border border-yellow-200/50">
          <div className="bg-gradient-to-br from-yellow-500 to-yellow-600 rounded-full p-4 w-20 h-20 mx-auto mb-6 shadow-lg">
            <FileText className="h-12 w-12 text-white" />
          </div>
          <h3 className="text-xl font-bold text-gray-800 mb-3">书籍ID无效</h3>
          <p className="text-gray-600 mb-6">无法识别的书籍标识符：{bookId || '空'}</p>
          <Link
            to="/"
            className="bg-gradient-to-r from-sky-500 to-sky-600 hover:from-sky-600 hover:to-sky-700 text-white font-semibold px-6 py-3 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            返回书架
          </Link>
        </div>
      </div>
    )
  }

  if (error || !book) {
    const errorData = (error as any)?.response?.data?.data
    const isLoginExpired = errorData?.error === 'LOGIN_EXPIRED'
    const isBookUnavailable = errorData?.error === 'BOOK_INFO_UNAVAILABLE'
    const isInvalidBookId = errorData?.error === 'INVALID_BOOK_ID'

    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-8 bg-gradient-to-br from-white/95 to-red-50/80 backdrop-blur-sm rounded-2xl shadow-xl border border-red-200/50">
          <div className="bg-gradient-to-br from-red-500 to-red-600 rounded-full p-4 w-20 h-20 mx-auto mb-6 shadow-lg">
            <FileText className="h-12 w-12 text-white" />
          </div>

          {isLoginExpired ? (
            <>
              <h3 className="text-xl font-bold text-gray-800 mb-3">登录已过期</h3>
              <p className="text-gray-600 mb-6">您的登录状态已过期，请重新登录以查看书籍详情</p>
              <div className="space-y-3">
                <button
                  onClick={() => window.location.href = '/login'}
                  className="bg-gradient-to-r from-sky-500 to-sky-600 hover:from-sky-600 hover:to-sky-700 text-white font-semibold px-6 py-3 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105 w-full"
                >
                  重新登录
                </button>
                <Link
                  to="/"
                  className="block bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold px-6 py-3 rounded-xl transition-all duration-200"
                >
                  返回书架
                </Link>
              </div>
            </>
          ) : isBookUnavailable ? (
            <>
              <h3 className="text-xl font-bold text-gray-800 mb-3">书籍详情暂时不可用</h3>
              <p className="text-gray-600 mb-6">暂时无法获取该书籍的详细信息，请稍后重试</p>
              <div className="space-y-3">
                <button
                  onClick={() => window.location.reload()}
                  className="bg-gradient-to-r from-sky-500 to-sky-600 hover:from-sky-600 hover:to-sky-700 text-white font-semibold px-6 py-3 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105 w-full"
                >
                  重新加载
                </button>
                <Link
                  to="/"
                  className="block bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold px-6 py-3 rounded-xl transition-all duration-200"
                >
                  返回书架
                </Link>
              </div>
            </>
          ) : (
            <>
              <h3 className="text-xl font-bold text-gray-800 mb-3">加载失败</h3>
              <p className="text-gray-600 mb-6">抱歉，无法获取书籍详情，请检查网络连接或稍后重试</p>
              <div className="space-y-3">
                <button
                  onClick={() => window.location.reload()}
                  className="bg-gradient-to-r from-sky-500 to-sky-600 hover:from-sky-600 hover:to-sky-700 text-white font-semibold px-6 py-3 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105 w-full"
                >
                  重新加载
                </button>
                <Link
                  to="/"
                  className="block bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold px-6 py-3 rounded-xl transition-all duration-200"
                >
                  返回书架
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Back Button */}
        <Link
          to="/"
          className="inline-flex items-center space-x-3 bg-white/80 backdrop-blur-sm text-gray-700 hover:text-sky-600 hover:bg-white px-4 py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 mb-8 border border-white/20 group"
        >
          <div className="bg-gradient-to-r from-sky-500 to-sky-600 rounded-lg p-1.5 group-hover:from-sky-600 group-hover:to-sky-700 transition-all duration-200">
            <ArrowLeft className="h-4 w-4 text-white" />
          </div>
          <span className="font-medium">返回书架</span>
        </Link>

        {/* Book Details */}
        <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-2xl border border-white/30 overflow-hidden">
          <div className="grid md:grid-cols-3 gap-8 p-8">
            {/* Cover */}
            <div className="flex justify-center">
              <div
                className="relative group cursor-pointer"
                onClick={() => setShowImageModal(true)}
              >
                {/* 简化的封面容器 */}
                <div className="relative bg-white p-2 rounded-xl shadow-lg group-hover:shadow-xl transition-all duration-200">
                  <img
                    src={book.cover}
                    alt={book.title}
                    className="w-full max-w-xs mx-auto rounded-lg transform group-hover:scale-[1.02] transition-all duration-200 ease-out"
                  />

                  {/* 简洁的hover提示 */}
                  <div className="absolute inset-0 rounded-lg bg-black/0 group-hover:bg-black/20 transition-all duration-200 flex items-center justify-center">
                    <div className="text-white text-sm font-medium bg-black/70 px-3 py-1 rounded-lg backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-all duration-200">
                      点击查看大图
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Info */}
            <div className="md:col-span-2 space-y-6">
              <div>
                <h1 className="text-4xl font-bold text-gray-900 mb-3 leading-tight">{book.title}</h1>
                <p className="text-xl text-gray-600 font-medium">{book.author}</p>
              </div>

              {/* Tags */}
              <div className="flex flex-wrap gap-3">
                {book.category && (
                  <span className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-sky-100 to-sky-200 text-sky-800 rounded-full text-sm font-medium border border-sky-300/50">
                    <BookIcon className="h-4 w-4 mr-2" />
                    {book.category}
                  </span>
                )}

                {book.newRatingDetail && (
                  <span className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-yellow-100 to-yellow-200 text-yellow-800 rounded-full text-sm font-medium border border-yellow-300/50">
                    <Star className="h-4 w-4 mr-2" />
                    {book.newRatingDetail}
                  </span>
                )}
              </div>

              {/* Introduction */}
              {book.intro && (
                <div className="bg-gradient-to-r from-gray-50 to-blue-50 rounded-xl p-6 border border-gray-200/50">
                  <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center">
                    <FileText className="h-5 w-5 mr-2 text-sky-600" />
                    内容简介
                  </h3>
                  <p className="text-gray-700 leading-relaxed text-base">{book.intro}</p>
                </div>
              )}

              {/* Publisher */}
              {book.publisher && (
                <div className="text-gray-600 bg-gray-50 rounded-lg px-4 py-3 border border-gray-200/50">
                  <span className="font-semibold text-gray-800">出版社：</span>
                  <span className="ml-2">{book.publisher}</span>
                </div>
              )}

              {/* Actions */}
              <div className="space-y-6 pt-6">
                <div className="border-t border-gray-200 pt-6">
                  <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                    <FileText className="h-6 w-6 mr-3 text-sky-600" />
                    阅读笔记
                  </h3>
                  <div className="grid sm:grid-cols-1 lg:grid-cols-2 gap-6">
                    <Link
                      to={`/books/${bookId}/notes?option=1`}
                      className="group bg-gradient-to-r from-sky-500 to-sky-600 hover:from-sky-600 hover:to-sky-700 text-white font-semibold px-6 py-5 rounded-xl transition-all duration-300 shadow-lg hover:shadow-2xl transform hover:scale-[1.02] flex items-center space-x-4 border border-sky-400/20"
                    >
                      <div className="bg-white/20 rounded-lg p-3 group-hover:bg-white/30 transition-all duration-300">
                        <FileText className="h-6 w-6" />
                      </div>
                      <div className="text-left">
                        <div className="font-bold text-lg">完整笔记</div>
                        <div className="text-sm text-white/90">包含所有主要章节内容</div>
                      </div>
                    </Link>

                    <Link
                      to={`/books/${bookId}/notes?option=2`}
                      className="group bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white font-semibold px-6 py-5 rounded-xl transition-all duration-300 shadow-lg hover:shadow-2xl transform hover:scale-[1.02] flex items-center space-x-4 border border-orange-400/20"
                    >
                      <div className="bg-white/20 rounded-lg p-3 group-hover:bg-white/30 transition-all duration-300">
                        <FileText className="h-6 w-6" />
                      </div>
                      <div className="text-left">
                        <div className="font-bold text-lg">精选笔记</div>
                        <div className="text-sm text-white/90">仅显示有标注的章节</div>
                      </div>
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Image Modal */}
        {showImageModal && (
          <div
            className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4"
            onClick={() => setShowImageModal(false)}
          >
            <div className="relative max-w-5xl max-h-[95vh] animate-fadeIn">
              {/* Close Button */}
              <button
                onClick={() => setShowImageModal(false)}
                className="absolute -top-12 right-0 bg-white/10 hover:bg-white/20 text-white rounded-full p-3 transition-all duration-200 backdrop-blur-sm border border-white/20"
              >
                <X className="h-5 w-5" />
              </button>

              {/* Pure Large Image */}
              <img
                src={getHighResolutionCover(book.cover)}
                alt={book.title}
                className="max-w-full max-h-full rounded-lg shadow-2xl"
                onClick={(e) => e.stopPropagation()}
              />
            </div>
          </div>
        )}
    </div>
  )
}