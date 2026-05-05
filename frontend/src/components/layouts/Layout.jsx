import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { useState } from 'react'
import {
  Home, Search, Users, FileText, BarChart3,
  Users2, Brain, Menu, X,
  ChevronRight
} from 'lucide-react'
import { useAppStore } from '../../store'
import { clsx } from 'clsx'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home, desc: 'Overview & key metrics' },
  { name: 'Publications', href: '/publications', icon: FileText, desc: 'Browse all research papers' },
  { name: 'Authors', href: '/authors', icon: Users, desc: 'Search faculty & researchers' },
  { name: 'Search', href: '/search', icon: Search, desc: 'Keyword & semantic search' },
  { name: 'Team Builder', href: '/teams', icon: Users2, desc: 'Explore themes & build teams' },
  { name: 'Analytics', href: '/analytics', icon: BarChart3, desc: 'Research analytics' },
  { name: 'RAG Analysis', href: '/rag', icon: Brain, desc: 'AI-powered research insights' },
]

export default function Layout() {
  const location = useLocation()
  const { sidebarOpen, toggleSidebar } = useAppStore()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile menu button */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 rounded-lg bg-white shadow-md hover:bg-gray-50"
        >
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-40 flex flex-col bg-white border-r border-gray-200 transition-all duration-300',
          sidebarOpen ? 'w-64' : 'w-20',
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        {/* Logo */}
        <div className="flex items-center h-16 px-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <img
              src="/sastra-logo.png"
              alt="SASTRA"
              className={clsx(
                'h-10 rounded-lg flex-shrink-0 object-contain',
                sidebarOpen ? 'w-auto max-w-[40px]' : 'w-10 object-cover object-left'
              )}
            />
            {sidebarOpen && (
              <div className="animate-fade-in">
                <h1 className="font-bold text-gray-900">SASTRA</h1>
                <p className="text-xs text-gray-500">Research Finder</p>
              </div>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto custom-scrollbar">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href
            const Icon = item.icon

            return (
              <NavLink
                key={item.name}
                to={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200',
                  isActive
                    ? 'bg-primary-50 text-primary-700 font-medium'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                )}
              >
                <Icon size={20} className={clsx('flex-shrink-0', isActive ? 'text-primary-600' : '')} />
                {sidebarOpen && (
                  <div className="animate-fade-in min-w-0">
                    <span className="block leading-tight">{item.name}</span>
                    <span className="block text-[11px] leading-tight text-gray-400 font-normal truncate">{item.desc}</span>
                  </div>
                )}
              </NavLink>
            )
          })}
        </nav>

        {/* Sidebar footer: collapse */}
        <div className="hidden lg:block p-4 border-t border-gray-200">
          <button
            onClick={toggleSidebar}
            className="flex items-center justify-center w-full p-2 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-gray-900 transition-colors"
          >
            <ChevronRight
              size={20}
              className={clsx(
                'transition-transform duration-300',
                sidebarOpen ? 'rotate-180' : ''
              )}
            />
          </button>
        </div>
      </aside>

      {/* Mobile overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Main content */}
      <main
        className={clsx(
          'transition-all duration-300 min-h-screen flex flex-col',
          sidebarOpen ? 'lg:pl-64' : 'lg:pl-20'
        )}
      >
        <div className="p-4 lg:p-8 flex-1">
          <Outlet />
        </div>
        <footer className="px-4 lg:px-8 py-3 border-t border-gray-100">
          <p className="text-[11px] text-gray-400 text-center">
            Developed by <span className="text-gray-500">Devarakonda Satyasai</span> (B.Tech CSBS - III Year)
            <span className="mx-1.5">·</span>
            Guided by <span className="text-gray-500">Dr. Brindha G.R</span>, Assistant Professor (AP3)
          </p>
        </footer>
      </main>
    </div>
  )
}
