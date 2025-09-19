import React, { useState } from 'react'
import { useQuery } from 'react-query'
import { Link } from 'react-router-dom'
import { Search, Book } from 'lucide-react'
import { searchAPI } from '../lib/api'
import type { SearchResult } from '../lib/api'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [page, setPage] = useState(1)
  const pageSize = 12

  const {
    data: response,
    isLoading,
    error,
  } = useQuery(
    ['search', searchQuery, page],
    () => searchAPI.searchBooks(searchQuery, page, pageSize),
    { enabled: !!searchQuery }
  )

  const results = response?.data?.data?.results || []
  const totalPages = response?.data?.data?.total_pages || 1
  const total = response?.data?.data?.total || 0

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      setSearchQuery(query.trim())
      setPage(1)
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">搜索书籍</h1>

        {/* Search Form */}
        <form onSubmit={handleSearch} className="flex space-x-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="输入书名或作者名..."
              className="input pl-10"
            />
          </div>
          <button type="submit" className="btn btn-primary">
            搜索
          </button>
        </form>
      </div>

      {/* Search Results */}
      {searchQuery && (
        <div>
          <div className="mb-6">
            <p className="text-gray-600">
              搜索 "{searchQuery}" 的结果，共找到 {total} 本书
            </p>
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

          {/* Results */}
          {!isLoading && results.length > 0 && (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {results.map((result: SearchResult) => (
                  <Link
                    key={result.bookId}
                    to={`/books/${result.bookId}`}
                    className="card p-4 hover:shadow-md transition-shadow group"
                  >
                    <img
                      src={result.cover}
                      alt={result.title}
                      className="w-full h-48 object-cover rounded mb-4 group-hover:scale-105 transition-transform"
                    />
                    <h3 className="font-semibold text-gray-900 mb-1 line-clamp-2">
                      {result.title}
                    </h3>
                    <p className="text-sm text-gray-600 mb-2">{result.author}</p>
                    <div className="text-xs text-gray-500">
                      匹配度: {result.ratio}%
                    </div>
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

          {/* No Results */}
          {!isLoading && results.length === 0 && searchQuery && (
            <div className="text-center py-12">
              <Book className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">未找到相关书籍</h3>
              <p className="text-gray-600">请尝试其他关键词</p>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="text-center py-12">
              <div className="text-red-600 mb-4">搜索失败</div>
              <button onClick={() => window.location.reload()} className="btn btn-primary">
                重试
              </button>
            </div>
          )}
        </div>
      )}

      {/* Initial State */}
      {!searchQuery && (
        <div className="text-center py-20">
          <Search className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">搜索你的书籍</h3>
          <p className="text-gray-600">输入书名或作者名开始搜索</p>
        </div>
      )}
    </div>
  )
}