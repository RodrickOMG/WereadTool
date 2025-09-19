import React, { useState, useEffect } from 'react'
import { useQuery, useQueryClient } from 'react-query'
import { Link, useLocation } from 'react-router-dom'
import { RefreshCw, Star, Book as BookIcon, CheckCircle, Loader } from 'lucide-react'
import { booksAPI } from '../lib/api'
import { useDynamicPageSize } from '../lib/hooks/useDynamicPageSize'
import type { Book } from '../lib/api'
import toast from 'react-hot-toast'

export default function HomePage() {
  const [page, setPage] = useState(1)
  const [loadingMode, setLoadingMode] = useState<'rawbooks' | 'all' | 'complete'>('rawbooks')
  const [showAllBooks, setShowAllBooks] = useState(false)

  // 使用动态计算的每页书籍数量
  const { pageSize, windowWidth } = useDynamicPageSize()

  const queryClient = useQueryClient()
  const location = useLocation()

  // 当pageSize改变时，重置到第一页
  useEffect(() => {
    if (page > 1) {
      setPage(1)
    }
  }, [pageSize])

  // 主查询：根据加载模式获取书籍
  const {
    data: response,
    isLoading,
    error,
    refetch,
  } = useQuery(
    ['books', page, pageSize, loadingMode],
    () => booksAPI.getBooks(page, pageSize, loadingMode),
    {
      retry: 1,
      staleTime: 1 * 60 * 1000,
      cacheTime: 10 * 60 * 1000,
      onSuccess: (data) => {
        // 当rawbooks模式加载完成且有待同步书籍时，自动开始加载完整数据
        if (loadingMode === 'rawbooks' && data?.data?.data?.loading_info?.has_more_to_sync) {
          setTimeout(() => {
            setLoadingMode('all')
            setShowAllBooks(true)
            toast.info('正在加载剩余书籍数据...', { duration: 2000 })
          }, 1500)
        } else if (loadingMode === 'all') {
          setLoadingMode('complete')
          toast.success('所有书籍数据加载完成')
        }
      }
    }
  )

  // 检测是否从登录页跳转过来，如果是则强制刷新数据
  useEffect(() => {
    // 检查是否是从登录页面跳转来的（通过 replace: true 跳转）
    const fromLogin = location.state?.fromLogin ||
                     sessionStorage.getItem('justLoggedIn') === 'true'

    if (fromLogin) {
      console.log('🔄 检测到登录跳转，强制刷新书籍数据')
      // 清除登录标记
      sessionStorage.removeItem('justLoggedIn')
      // 显示加载提示
      toast.loading('正在加载完整书架数据...', { id: 'loading-books' })
      // 清除查询缓存并重新获取
      queryClient.removeQueries(['books'])
      refetch().then(() => {
        toast.dismiss('loading-books')
        toast.success('书架数据加载完成')
      }).catch(() => {
        toast.dismiss('loading-books')
        toast.error('书架数据加载失败，请手动刷新')
      })
    }
  }, [location, queryClient, refetch])

  const books = response?.data?.data?.books || []
  const totalPages = response?.data?.data?.total_pages || 1
  const total = response?.data?.data?.total || 0
  const loadingInfo = response?.data?.data?.loading_info

  // 计算显示状态
  const isInitialLoading = isLoading && loadingMode === 'rawbooks' && !showAllBooks
  const isAutoLoading = loadingMode === 'all' && !isLoading
  const showLoadingIndicator = isInitialLoading || isAutoLoading

  const handleRefresh = async () => {
    try {
      await booksAPI.refreshBooks()
      refetch()
      toast.success('书架已刷新')
    } catch (error) {
      toast.error('刷新失败')
    }
  }

  const getRatingImage = (rating: string) => {
    const imageMap: { [key: string]: string } = {
      '神作': '/static/images/outstanding.png',
      '好评如潮': '/static/images/rave_reviews.png',
      '脍炙人口': '/static/images/win_universal_praise.png',
      '值得一读': '/static/images/worth_reading.png',
      '褒贬不一': '/static/images/medium.png',
      '不值一读': '/static/images/bad.png'
    }
    return imageMap[rating] || null
  }

  const getRatingColor = (rating: string) => {
    switch (rating) {
      case '神作':
        return 'bg-purple-100 text-purple-800'
      case '好评如潮':
        return 'bg-green-100 text-green-800'
      case '脍炙人口':
        return 'bg-blue-100 text-blue-800'
      case '值得一读':
        return 'bg-yellow-100 text-yellow-800'
      case '褒贬不一':
        return 'bg-orange-100 text-orange-800'
      case '不值一读':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getRatingBadgeClass = (rating: string) => {
    switch (rating) {
      case '神作':
        return 'badge-masterpiece'
      case '好评如潮':
        return 'badge-excellent'
      case '脍炙人口':
        return 'badge-popular'
      case '值得一读':
        return 'badge-worth'
      case '褒贬不一':
        return 'badge-mixed'
      case '不值一读':
        return 'badge-poor'
      default:
        return 'badge-default'
    }
  }

  const renderPageNumbers = () => {
    const pages = []

    if (totalPages <= 7) {
      // 如果总页数少于等于7页，显示所有页码
      for (let i = 1; i <= totalPages; i++) {
        pages.push(
          <button
            key={i}
            onClick={() => setPage(i)}
            className={`page-number ${page === i ? 'active' : ''}`}
          >
            {i}
          </button>
        )
      }
    } else {
      // 复杂的分页逻辑，参考原模板
      if (page < 5) {
        // 当前页在前部
        for (let i = 1; i <= 5; i++) {
          pages.push(
            <button
              key={i}
              onClick={() => setPage(i)}
              className={`page-number ${page === i ? 'active' : ''}`}
            >
              {i}
            </button>
          )
        }
        pages.push(<span key="ellipsis1" className="page-ellipsis">...</span>)
        pages.push(
          <button
            key={totalPages}
            onClick={() => setPage(totalPages)}
            className={`page-number ${page === totalPages ? 'active' : ''}`}
          >
            {totalPages}
          </button>
        )
      } else if (page > totalPages - 4) {
        // 当前页在后部
        pages.push(
          <button
            key={1}
            onClick={() => setPage(1)}
            className={`page-number ${page === 1 ? 'active' : ''}`}
          >
            1
          </button>
        )
        pages.push(<span key="ellipsis2" className="page-ellipsis">...</span>)
        for (let i = totalPages - 4; i <= totalPages; i++) {
          pages.push(
            <button
              key={i}
              onClick={() => setPage(i)}
              className={`page-number ${page === i ? 'active' : ''}`}
            >
              {i}
            </button>
          )
        }
      } else {
        // 当前页在中部
        pages.push(
          <button
            key={1}
            onClick={() => setPage(1)}
            className={`page-number ${page === 1 ? 'active' : ''}`}
          >
            1
          </button>
        )
        if (page !== 5) {
          pages.push(<span key="ellipsis3" className="page-ellipsis">...</span>)
        }
        for (let i = page - 2; i <= page + 2; i++) {
          pages.push(
            <button
              key={i}
              onClick={() => setPage(i)}
              className={`page-number ${page === i ? 'active' : ''}`}
            >
              {i}
            </button>
          )
        }
        if (page !== totalPages - 4) {
          pages.push(<span key="ellipsis4" className="page-ellipsis">...</span>)
        }
        pages.push(
          <button
            key={totalPages}
            onClick={() => setPage(totalPages)}
            className={`page-number ${page === totalPages ? 'active' : ''}`}
          >
            {totalPages}
          </button>
        )
      }
    }

    return pages
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">加载失败</div>
        <button onClick={() => refetch()} className="btn btn-primary">
          重试
        </button>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-12">
          <div className="space-y-3">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
              我的书架
            </h1>
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-3">
                <p className="text-gray-700 font-medium text-lg">
                  📚 共 {total} 本书
                </p>
                <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded-md">
                  每页 {pageSize} 本
                </span>
              </div>
              {loadingInfo && (
                <div className="flex items-center gap-4 text-sm">
                  {loadingInfo.synced_books_count > 0 && (
                    <span className="text-amber-600 bg-amber-50 px-3 py-1 rounded-full border border-amber-200">
                      🔄 {loadingInfo.synced_books_count} 本待同步
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
          <button
            onClick={handleRefresh}
            className="btn btn-secondary flex items-center space-x-2 shadow-md hover:shadow-lg transition-all duration-200"
          >
            <RefreshCw className="h-4 w-4" />
            <span>刷新</span>
          </button>
        </div>

      {/* Loading Status */}
      {showLoadingIndicator && (
        <div className="mb-8 p-6 bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-white/30">
          <div className="flex items-center gap-4">
            <div className="relative">
              <Loader className="h-6 w-6 text-blue-600 animate-spin" />
              <div className="absolute inset-0 rounded-full border-2 border-blue-200 animate-ping opacity-20"></div>
            </div>
            <div className="flex-1">
              <p className="text-base font-semibold text-gray-900 mb-2">
                {isInitialLoading && '📖 正在加载完整书籍数据...'}
                {isAutoLoading && '🔄 正在同步剩余书籍数据...'}
              </p>
              <div className="relative">
                <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                  <div className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-1000 ease-out"
                       style={{ width: loadingMode === 'complete' ? '100%' : '60%' }}>
                  </div>
                </div>
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse"></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="book-showcase">
          {Array.from({ length: pageSize }).map((_, i) => (
            <div key={i} className="book-card">
              <div className="book-card-inner card animate-pulse">
                <div className="bg-gray-300 w-full h-full rounded-2xl"></div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Books Grid - 仿照原模板的书籍卡片设计 */}
      {!isLoading && books.length > 0 && (
        <>
          <div className="book-showcase">
            {books.map((book: Book) => (
              <Link
                key={book.bookId}
                to={`/books/${book.bookId}`}
                className="book-card group"
              >
                <div className="book-card-inner">
                  <img
                    src={book.cover}
                    alt={book.title}
                    className="book-cover-image"
                  />

                  {/* 悬浮覆盖层 */}
                  <div className="book-overlay">
                    <div className="book-info">
                      <h3 className="book-title">{book.title}</h3>
                      <p className="book-author">{book.author}</p>
                      {book.category && (
                        <p className="book-category">{book.category}</p>
                      )}
                    </div>

                    {/* 状态标记 */}
                    <div className="book-badges">
                      {book.finishReading === 1 && (
                        <div className="badge badge-finished">
                          <CheckCircle className="h-4 w-4" />
                          <span>已读完</span>
                        </div>
                      )}

                      {book.newRatingDetail && (
                        <div className="rating-badge-container">
                          {getRatingImage(book.newRatingDetail) ? (
                            <img
                              src={getRatingImage(book.newRatingDetail)!}
                              alt={book.newRatingDetail}
                              className="rating-image"
                              title={book.newRatingDetail}
                            />
                          ) : (
                            <div className={`badge badge-rating ${getRatingBadgeClass(book.newRatingDetail)}`}>
                              {book.newRatingDetail}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>

          {/* Pagination - 参考原模板样式 */}
          {totalPages > 1 && (
            <div className="pagination-container">
              <div className="pagination">
                {/* 首页 */}
                <button
                  onClick={() => setPage(1)}
                  className="page-btn"
                  disabled={page === 1}
                >
                  首页
                </button>

                {/* 上一页 */}
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="page-btn"
                >
                  &lt; 上一页
                </button>

                {/* 页码 */}
                <div className="page-numbers">
                  {renderPageNumbers()}
                </div>

                {/* 下一页 */}
                <button
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages}
                  className="page-btn"
                >
                  下一页 &gt;
                </button>

                {/* 尾页 */}
                <button
                  onClick={() => setPage(totalPages)}
                  className="page-btn"
                  disabled={page === totalPages}
                >
                  尾页
                </button>

                {/* 跳转 */}
                <div className="page-jump">
                  <input
                    type="number"
                    min="1"
                    max={totalPages}
                    placeholder="页码"
                    className="page-input"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        const target = e.target as HTMLInputElement
                        const pageNum = parseInt(target.value)
                        if (pageNum >= 1 && pageNum <= totalPages) {
                          setPage(pageNum)
                          target.value = ''
                        }
                      }
                    }}
                  />
                  <button
                    className="page-confirm"
                    onClick={() => {
                      const input = document.querySelector('.page-input') as HTMLInputElement
                      const pageNum = parseInt(input.value)
                      if (pageNum >= 1 && pageNum <= totalPages) {
                        setPage(pageNum)
                        input.value = ''
                      }
                    }}
                  >
                    前往
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Empty State */}
      {!isLoading && books.length === 0 && (
        <div className="text-center py-12">
          <BookIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">暂无书籍</h3>
          <p className="text-gray-600 mb-4">
            书架是空的，可能需要刷新来加载最新数据
          </p>
          <div className="space-y-3">
            <button onClick={handleRefresh} className="btn btn-primary">
              刷新书架
            </button>
            <p className="text-sm text-gray-500">
              如果刷新后仍无数据，请检查微信读书是否有书籍或重新登录
            </p>
          </div>
        </div>
      )}
      </div>
    </div>
  )
}