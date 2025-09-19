import React from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from 'react-query'
import { ArrowLeft, FileText, Download } from 'lucide-react'
import { booksAPI } from '../lib/api'

export default function BookDetailPage() {
  const { bookId } = useParams<{ bookId: string }>()

  const { data: response, isLoading, error } = useQuery(
    ['book', bookId],
    () => booksAPI.getBook(bookId!),
    { enabled: !!bookId }
  )

  const book = response?.data?.data

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 bg-gray-300 rounded w-32 mb-8"></div>
        <div className="grid md:grid-cols-3 gap-8">
          <div className="bg-gray-300 h-64 rounded"></div>
          <div className="md:col-span-2 space-y-4">
            <div className="h-8 bg-gray-300 rounded"></div>
            <div className="h-4 bg-gray-300 rounded w-1/2"></div>
            <div className="space-y-2">
              <div className="h-4 bg-gray-300 rounded"></div>
              <div className="h-4 bg-gray-300 rounded"></div>
              <div className="h-4 bg-gray-300 rounded w-3/4"></div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error || !book) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">加载失败</div>
        <Link to="/" className="btn btn-primary">
          返回书架
        </Link>
      </div>
    )
  }

  return (
    <div>
      {/* Back Button */}
      <Link
        to="/"
        className="inline-flex items-center space-x-2 text-gray-600 hover:text-gray-900 mb-8"
      >
        <ArrowLeft className="h-4 w-4" />
        <span>返回书架</span>
      </Link>

      {/* Book Details */}
      <div className="grid md:grid-cols-3 gap-8">
        {/* Cover */}
        <div>
          <img
            src={book.cover}
            alt={book.title}
            className="w-full max-w-xs mx-auto rounded-lg shadow-lg"
          />
        </div>

        {/* Info */}
        <div className="md:col-span-2">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{book.title}</h1>
          <p className="text-xl text-gray-600 mb-4">{book.author}</p>

          {book.category && (
            <div className="mb-4">
              <span className="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                {book.category}
              </span>
            </div>
          )}

          {book.newRatingDetail && (
            <div className="mb-4">
              <span className="inline-block bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-sm">
                {book.newRatingDetail}
              </span>
            </div>
          )}

          {book.intro && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">简介</h3>
              <p className="text-gray-700 leading-relaxed">{book.intro}</p>
            </div>
          )}

          {book.publisher && (
            <div className="text-sm text-gray-600 mb-6">
              <strong>出版社：</strong>{book.publisher}
            </div>
          )}

          {/* Actions */}
          <div className="space-y-3">
            <Link
              to={`/books/${bookId}/notes?option=1`}
              className="btn btn-primary flex items-center space-x-2 w-full md:w-auto"
            >
              <FileText className="h-4 w-4" />
              <span>查看笔记（包含所有章节）</span>
            </Link>
            <Link
              to={`/books/${bookId}/notes?option=2`}
              className="btn btn-secondary flex items-center space-x-2 w-full md:w-auto"
            >
              <FileText className="h-4 w-4" />
              <span>查看笔记（仅包含有标注的章节）</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}