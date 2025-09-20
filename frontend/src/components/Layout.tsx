import React from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { Book, Search, LogOut, User, BookOpen } from 'lucide-react'

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const isActive = (path: string) => {
    return location.pathname === path
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-sky-600 to-sky-700 shadow-lg border-b border-sky-500/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-lg overflow-hidden bg-white/10 backdrop-blur-sm p-1">
                <img
                  src="/src/static/images/weread.png"
                  alt="微信读书"
                  className="w-full h-full object-cover rounded-lg"
                />
              </div>
              <h1 className="text-xl font-bold text-white tracking-wide">微信读书助手</h1>
            </div>

            {/* User Menu */}
            <div className="flex items-center space-x-6">
              {user && (
                <>
                  <div className="flex items-center space-x-3 bg-white/10 backdrop-blur-sm rounded-full px-4 py-2 hover:bg-white/20 transition-all duration-200">
                    {user.wr_avatar ? (
                      <img
                        src={user.wr_avatar}
                        alt={user.wr_name || '用户头像'}
                        className="h-8 w-8 rounded-full border-2 border-white/30 shadow-sm object-cover"
                        onError={(e) => {
                          const target = e.target as HTMLImageElement;
                          target.style.display = 'none';
                          target.nextElementSibling?.classList.remove('hidden');
                        }}
                      />
                    ) : null}
                    <div className={`bg-gradient-to-br from-sky-300 to-sky-400 h-8 w-8 rounded-full flex items-center justify-center text-white font-semibold text-sm border-2 border-white/30 shadow-sm ${user.wr_avatar ? 'hidden' : ''}`}>
                      {user.wr_name ? user.wr_name.charAt(0).toUpperCase() : 'U'}
                    </div>
                    <span className="text-white font-medium text-sm">{user.wr_name || '用户'}</span>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="flex items-center space-x-2 text-white/90 hover:text-white hover:bg-white/10 px-3 py-2 rounded-lg transition-all duration-200 backdrop-blur-sm"
                  >
                    <LogOut className="h-4 w-4" />
                    <span className="text-sm font-medium">退出</span>
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main>
        {children}
      </main>
    </div>
  )
}