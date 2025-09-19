import React, { useState } from 'react'
import { useQuery } from 'react-query'
import { Link } from 'react-router-dom'
import { RefreshCw, Star, Book as BookIcon, CheckCircle } from 'lucide-react'
import { booksAPI } from '../lib/api'
import type { Book } from '../lib/api'
import toast from 'react-hot-toast'

export default function HomePage() {
  const [page, setPage] = useState(1)
  const pageSize = 12

  const {
    data: response,
    isLoading,
    error,
    refetch,
  } = useQuery(['books', page], () => booksAPI.getBooks(page, pageSize))

  const books = response?.data?.data?.books || []
  const totalPages = response?.data?.data?.total_pages || 1
  const total = response?.data?.data?.total || 0

  const handleRefresh = async () => {
    try {
      await booksAPI.refreshBooks()
      refetch()
      toast.success('书架已刷新')
    } catch (error) {
      toast.error('刷新失败')
    }
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
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">我的书架</h1>
          <p className="text-gray-600 mt-1">共 {total} 本书</p>
        </div>
        <button
          onClick={handleRefresh}
          className="btn btn-secondary flex items-center space-x-2"
        >
          <RefreshCw className="h-4 w-4" />
          <span>刷新</span>
        </button>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {Array.from({ length: pageSize }).map((_, i) => (
            <div key={i} className="card p-4 animate-pulse">
              <div className="bg-gray-300 h-48 rounded mb-4"></div>
              <div className="bg-gray-300 h-4 rounded mb-2"></div>
              <div className="bg-gray-300 h-3 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      )}

      {/* Books Grid */}
      {!isLoading && books.length > 0 && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {books.map((book: Book) => (
              <Link
                key={book.bookId}
                to={`/books/${book.bookId}`}
                className="card p-4 hover:shadow-md transition-shadow group"
              >
                <div className="relative">
                  <img
                    src={book.cover}
                    alt={book.title}
                    className="w-full h-48 object-cover rounded mb-4 group-hover:scale-105 transition-transform"
                  />

                  {/* Badges */}
                  <div className="absolute top-2 left-2 space-y-1">
                    {book.finishReading === 1 && (
                      <div className="flex items-center space-x-1 bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs">
                        <CheckCircle className="h-3 w-3" />
                        <span>已读完</span>
                      </div>
                    )}
                  </div>

                  {book.newRatingDetail && (
                    <div className="absolute top-2 right-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRatingColor(book.newRatingDetail)}`}>
                        {book.newRatingDetail}
                      </span>
                    </div>
                  )}
                </div>

                <h3 className="font-semibold text-gray-900 mb-1 line-clamp-2">
                  {book.title}
                </h3>
                <p className="text-sm text-gray-600 mb-2">{book.author}</p>

                {book.category && (
                  <div className="flex items-center space-x-1 text-xs text-gray-500">
                    <BookIcon className="h-3 w-3" />
                    <span>{book.category}</span>
                  </div>
                )}
              </Link>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center space-x-2 mt-8">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="btn btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                上一页
              </button>

              <div className="flex items-center space-x-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  const pageNum = i + 1
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setPage(pageNum)}
                      className={`px-3 py-1 rounded ${
                        page === pageNum
                          ? 'bg-primary-600 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      {pageNum}
                    </button>
                  )
                })}
                {totalPages > 5 && (
                  <>
                    <span className="px-2">...</span>
                    <button
                      onClick={() => setPage(totalPages)}
                      className={`px-3 py-1 rounded ${
                        page === totalPages
                          ? 'bg-primary-600 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      {totalPages}
                    </button>
                  </>
                )}
              </div>

              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
                className="btn btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                下一页
              </button>
            </div>
          )}
        </>
      )}

      {/* Empty State */}
      {!isLoading && books.length === 0 && (
        <div className="text-center py-12">
          <BookIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">暂无书籍</h3>
          <p className="text-gray-600 mb-4">你的书架是空的，去微信读书添加一些书籍吧</p>
          <button onClick={handleRefresh} className="btn btn-primary">
            刷新书架
          </button>
        </div>
      )}
    </div>
  )
}