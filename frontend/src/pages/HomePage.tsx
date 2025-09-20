import React, { useState, useEffect, useMemo } from 'react'
import { useQuery, useQueryClient } from 'react-query'
import { Link, useLocation } from 'react-router-dom'
import { RefreshCw, Star, Book as BookIcon, CheckCircle, Loader, Search, X, Filter } from 'lucide-react'
import { booksAPI, searchAPI } from '../lib/api'
import { useDynamicPageSize } from '../lib/hooks/useDynamicPageSize'
import type { Book } from '../lib/api'
import toast from 'react-hot-toast'

export default function HomePage() {
  const [page, setPage] = useState(1)
  const [loadingMode, setLoadingMode] = useState<'rawbooks' | 'all' | 'complete'>('rawbooks')
  const [showAllBooks, setShowAllBooks] = useState(false)

  // 搜索相关状态
  const [searchQuery, setSearchQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [searchFilter, setSearchFilter] = useState<'all' | 'read' | 'unread'>('all')
  const [debouncedQuery, setDebouncedQuery] = useState('')

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

  // 搜索防抖
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery)
    }, 300)

    return () => clearTimeout(timer)
  }, [searchQuery])

  // 当搜索查询改变时，重置页码
  useEffect(() => {
    if (page > 1) {
      setPage(1)
    }
  }, [debouncedQuery, searchFilter])

  // 主查询：根据加载模式获取书籍
  const {
    data: response,
    isLoading,
    error,
    refetch,
  } = useQuery(
    ['books', page, pageSize, loadingMode, searchFilter],
    () => booksAPI.getBooks(page, pageSize, loadingMode, searchFilter),
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

  // 搜索查询
  const {
    data: searchResponse,
    isLoading: isSearchLoading,
  } = useQuery(
    ['search', debouncedQuery, page, pageSize],
    () => searchAPI.searchBooks(debouncedQuery, page, pageSize),
    {
      enabled: !!debouncedQuery.trim() && debouncedQuery.length >= 2,
      retry: 1,
      staleTime: 2 * 60 * 1000,
      cacheTime: 5 * 60 * 1000,
    }
  )

  // 根据搜索状态决定使用哪个数据源
  const isActiveSearch = !!debouncedQuery.trim() && debouncedQuery.length >= 2
  const currentResponse = isActiveSearch ? searchResponse : response
  const currentIsLoading = isActiveSearch ? isSearchLoading : isLoading

  const books = currentResponse?.data?.data?.books || currentResponse?.data?.data?.results || []
  const totalPages = currentResponse?.data?.data?.total_pages || 1
  const total = currentResponse?.data?.data?.total || 0
  const loadingInfo = response?.data?.data?.loading_info

  // 书籍列表（筛选已在后端完成）
  const filteredBooks = useMemo(() => {
    // 如果是搜索状态，直接返回搜索结果
    if (isActiveSearch) return books

    // 对于普通书架，后端已经完成筛选，直接返回
    return books
  }, [books, isActiveSearch])

  // 计算显示状态
  const isInitialLoading = isLoading && loadingMode === 'rawbooks' && !showAllBooks && !isActiveSearch
  const isAutoLoading = loadingMode === 'all' && !isLoading && !isActiveSearch
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
      '神作': '/src/static/images/outstanding.png',
      '好评如潮': '/src/static/images/rave_reviews.png',
      '脍炙人口': '/src/static/images/win_universal_praise.png',
      '值得一读': '/src/static/images/worth_reading.png',
      '褒贬不一': '/src/static/images/medium.png',
      '不值一读': '/src/static/images/bad.png'
    }

    // 调试日志：检查评分映射是否正确
    if (rating && !imageMap[rating]) {
      console.log(`📊 未找到评分图片映射: "${rating}"`);
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
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-8 bg-gradient-to-br from-white/95 to-red-50/80 backdrop-blur-sm rounded-2xl shadow-xl border border-red-200/50">
          <div className="bg-gradient-to-br from-red-500 to-red-600 rounded-full p-4 w-20 h-20 mx-auto mb-6 shadow-lg">
            <BookIcon className="h-12 w-12 text-white" />
          </div>
          <h3 className="text-xl font-bold text-gray-800 mb-3">书架加载失败</h3>
          <p className="text-gray-600 mb-6">抱歉，无法获取书籍数据，请检查网络连接或稍后重试</p>
          <button
            onClick={() => refetch()}
            className="bg-gradient-to-r from-sky-500 to-sky-600 hover:from-sky-600 hover:to-sky-700 text-white font-semibold px-6 py-3 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            <RefreshCw className="h-4 w-4 inline mr-2" />
            重新加载
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="space-y-6 mb-12">
          <div className="flex items-center justify-between">
            <div className="space-y-3">
              <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
                我的书架
              </h1>
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-3">
                  <p className="text-gray-700 font-medium text-lg">
                    📚 共 {total} 本书{isActiveSearch && ` | 搜索 "${debouncedQuery}"`}
                  </p>
                </div>
                {loadingInfo && !isActiveSearch && (
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

          {/* 搜索栏 */}
          <div className="flex flex-col sm:flex-row gap-4 items-stretch sm:items-center">
            <div className="relative flex-1 max-w-md">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜索书名、作者..."
                className="w-full pl-10 pr-10 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white/80 backdrop-blur-sm transition-all duration-200"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  <X className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                </button>
              )}
            </div>

            {/* 筛选器 */}
            <div className="flex items-center gap-2">
              <Filter className="h-5 w-5 text-gray-500" />
              <select
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value as 'all' | 'read' | 'unread')}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white/80 backdrop-blur-sm"
              >
                <option value="all">全部</option>
                <option value="read">已读完</option>
                <option value="unread">未读完</option>
              </select>
            </div>

            {isActiveSearch && (
              <div className="text-sm bg-gradient-to-r from-sky-50 to-blue-50 px-4 py-3 rounded-xl border border-sky-200/50 shadow-sm">
                {currentIsLoading ? (
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <Loader className="h-4 w-4 animate-spin text-sky-600" />
                      <div className="absolute inset-0 rounded-full border border-sky-300 animate-ping opacity-25"></div>
                    </div>
                    <span className="text-sky-700 font-medium">正在搜索书籍...</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <Search className="h-4 w-4 text-sky-600" />
                    <span className="text-sky-700 font-medium">找到 {filteredBooks.length} 本书</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

      {/* Loading Status */}
      {showLoadingIndicator && (
        <div className="mb-8 p-6 bg-gradient-to-br from-white/95 to-sky-50/80 backdrop-blur-sm rounded-2xl shadow-xl border border-sky-200/50">
          <div className="flex items-center gap-5">
            <div className="relative">
              <div className="bg-gradient-to-br from-sky-500 to-sky-600 rounded-full p-3 shadow-lg">
                <Loader className="h-6 w-6 text-white animate-spin" />
              </div>
              <div className="absolute inset-0 rounded-full border-2 border-sky-300 animate-ping opacity-30"></div>
              <div className="absolute inset-0 rounded-full bg-sky-400/20 animate-pulse"></div>
            </div>
            <div className="flex-1">
              <p className="text-lg font-bold text-gray-800 mb-3 tracking-wide">
                {isInitialLoading && '📖 正在加载完整书籍数据...'}
                {isAutoLoading && '🔄 正在同步剩余书籍数据...'}
              </p>
              <div className="relative">
                <div className="w-full bg-gradient-to-r from-gray-200 to-gray-300 rounded-full h-4 overflow-hidden shadow-inner">
                  <div className="bg-gradient-to-r from-sky-500 via-sky-600 to-sky-700 h-4 rounded-full transition-all duration-1000 ease-out shadow-sm"
                       style={{ width: loadingMode === 'complete' ? '100%' : '65%' }}>
                  </div>
                </div>
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-pulse rounded-full"></div>
              </div>
              <p className="text-sm text-gray-600 mt-2 font-medium">
                {isInitialLoading && '正在获取书架数据，请稍候...'}
                {isAutoLoading && '即将完成，正在处理剩余内容...'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Loading Skeleton */}
      {currentIsLoading && (
        <div className="book-showcase">
          {Array.from({ length: pageSize }).map((_, i) => (
            <div key={i} className="book-card">
              <div className="book-card-inner card animate-pulse">
                <div className="bg-gradient-to-br from-gray-200 via-gray-100 to-gray-200 w-full h-full rounded-2xl relative overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent -skew-x-12 animate-pulse-shimmer"></div>
                  <div className="absolute bottom-4 left-4 right-4">
                    <div className="bg-gray-300 h-4 rounded mb-2"></div>
                    <div className="bg-gray-300 h-3 rounded w-3/4"></div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Books Grid - 仿照原模板的书籍卡片设计 */}
      {!currentIsLoading && filteredBooks.length > 0 && (
        <>
          <div className="book-showcase">
            {filteredBooks.map((book: Book) => {
              // 验证bookId有效性
              const isValidBookId = book.bookId &&
                                   typeof book.bookId === 'string' &&
                                   book.bookId.trim() !== '' &&
                                   book.bookId !== 'undefined' &&
                                   book.bookId !== 'null'

              // 添加调试日志
              console.log('📖 渲染书籍卡片:', {
                bookId: book.bookId,
                title: book.title,
                bookIdType: typeof book.bookId,
                bookIdLength: book.bookId?.length,
                isValidBookId: isValidBookId,
                linkTo: isValidBookId ? `/books/${encodeURIComponent(book.bookId)}` : '#invalid'
              })

              // 如果bookId无效，显示警告而不是链接
              if (!isValidBookId) {
                console.warn('⚠️ 无效的bookId，跳过渲染:', book)
                return (
                  <div
                    key={`invalid-${book.title}-${Math.random()}`}
                    className="book-card group opacity-50 cursor-not-allowed"
                    title="书籍ID无效，无法查看详情"
                  >
                    <div className="book-card-inner">
                      <img
                        src={book.cover}
                        alt={book.title}
                        className="book-cover-image"
                      />
                      <div className="book-overlay">
                        <div className="book-info">
                          <h3 className="book-title">{book.title}</h3>
                          <p className="book-author">{book.author}</p>
                          <p className="text-red-500 text-sm">⚠️ 书籍ID无效</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )
              }

              return (
                <Link
                  key={book.bookId}
                  to={`/books/${encodeURIComponent(book.bookId)}`}
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
                      {/* 左侧：已读完标记 */}
                      <div className="book-badges-left">
                        {book.finishReading === 1 && (
                          <div className="rating-badge-container">
                            <img
                              src="/src/static/images/finished_reading.jpg"
                              alt="已读完"
                              className="rating-image finished-reading"
                              title="已读完"
                            />
                          </div>
                        )}
                      </div>

                      {/* 右侧：评分标记 */}
                      <div className="book-badges-right">
                        {book.newRatingDetail && (
                          <div className="rating-badge-container">
                            {(() => {
                              // 调试日志：显示书籍评分信息
                              console.log(`📚 书籍评分信息 - 书名: ${book.title}, 评分: "${book.newRatingDetail}", 加载模式: ${loadingMode}`);

                              const ratingImage = getRatingImage(book.newRatingDetail);
                              return ratingImage ? (
                                <img
                                  src={ratingImage}
                                  alt={book.newRatingDetail}
                                  className="rating-image"
                                  title={book.newRatingDetail}
                                />
                              ) : (
                                <div className={`badge badge-rating ${getRatingBadgeClass(book.newRatingDetail)}`}>
                                  {book.newRatingDetail}
                                </div>
                              );
                            })()}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </Link>
            )})}


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
      {!currentIsLoading && filteredBooks.length === 0 && (
        <div className="text-center py-12">
          {isActiveSearch ? (
            <>
              <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">未找到相关书籍</h3>
              <p className="text-gray-600 mb-4">
                没有找到包含 "{debouncedQuery}" 的书籍
              </p>
              <div className="space-y-3">
                <button
                  onClick={() => setSearchQuery('')}
                  className="btn btn-primary"
                >
                  清除搜索
                </button>
                <p className="text-sm text-gray-500">
                  尝试使用不同的关键词或清除筛选条件
                </p>
              </div>
            </>
          ) : searchFilter !== 'all' ? (
            <>
              <Filter className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                没有{searchFilter === 'read' ? '已读' : '未读'}的书籍
              </h3>
              <p className="text-gray-600 mb-4">
                当前筛选条件下没有找到书籍
              </p>
              <button
                onClick={() => setSearchFilter('all')}
                className="btn btn-primary"
              >
                显示全部书籍
              </button>
            </>
          ) : (
            <>
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
            </>
          )}
        </div>
      )}
      </div>
    </div>
  )
}