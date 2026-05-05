import { clsx } from 'clsx'
import { useState } from 'react'
import { Loader2, ArrowLeft, RotateCw } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

// Loading Spinner
export function Spinner({ size = 'md', className = '' }) {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12',
  }

  return (
    <Loader2 className={clsx('animate-spin text-primary-600', sizes[size], className)} />
  )
}

// Loading State
export function Loading({ message = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <Spinner size="lg" />
      <p className="mt-4 text-gray-500">{message}</p>
    </div>
  )
}

// Error State
export function ErrorState({ message = 'An error occurred', onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="w-16 h-16 rounded-full bg-danger-50 flex items-center justify-center mb-4">
        <span className="text-danger-500 text-2xl">!</span>
      </div>
      <p className="text-gray-600 mb-4">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn btn-primary">
          Try Again
        </button>
      )}
    </div>
  )
}

// Empty State
export function EmptyState({ title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
        <span className="text-gray-400 text-2xl">&#8709;</span>
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      {description && <p className="text-gray-500 text-center max-w-md mb-4">{description}</p>}
      {action}
    </div>
  )
}

// Card component
export function Card({ children, className = '', hover = false, onClick }) {
  return (
    <div
      onClick={onClick}
      className={clsx(
        'card p-6',
        hover && 'card-hover cursor-pointer',
        className
      )}
    >
      {children}
    </div>
  )
}

// Stat Card
export function StatCard({ label, value, icon: Icon, trend, className = '' }) {
  return (
    <Card className={className}>
      <div className="flex items-start justify-between">
        <div>
          <p className="stat-label">{label}</p>
          <p className="stat-value mt-1">{value}</p>
          {trend !== undefined && (
            <p className={clsx(
              'text-sm mt-2',
              trend > 0 ? 'text-success-600' : trend < 0 ? 'text-danger-500' : 'text-gray-500'
            )}>
              {trend > 0 ? '+' : ''}{trend}% from last year
            </p>
          )}
        </div>
        {Icon && (
          <div className="w-12 h-12 rounded-lg bg-primary-50 flex items-center justify-center">
            <Icon className="text-primary-600" size={24} />
          </div>
        )}
      </div>
    </Card>
  )
}

// Badge component
export function Badge({ children, variant = 'gray', className = '' }) {
  const variants = {
    primary: 'badge-primary',
    success: 'badge-success',
    warning: 'badge-warning',
    danger: 'badge-danger',
    gray: 'badge-gray',
  }

  return (
    <span className={clsx('badge', variants[variant], className)}>
      {children}
    </span>
  )
}

// Faculty Badge
export function FacultyBadge({ className = '' }) {
  return (
    <Badge variant="success" className={className}>
      🎓 Current Faculty
    </Badge>
  )
}

// Skeleton components
export function Skeleton({ className = '' }) {
  return <div className={clsx('skeleton', className)} />
}

export function SkeletonCard() {
  return (
    <Card>
      <Skeleton className="h-4 w-3/4 mb-4" />
      <Skeleton className="h-3 w-full mb-2" />
      <Skeleton className="h-3 w-5/6 mb-4" />
      <div className="flex gap-2">
        <Skeleton className="h-6 w-16 rounded-full" />
        <Skeleton className="h-6 w-20 rounded-full" />
      </div>
    </Card>
  )
}

export function SkeletonTable({ rows = 5 }) {
  return (
    <div className="space-y-3">
      {Array(rows).fill(0).map((_, i) => (
        <div key={i} className="flex gap-4">
          <Skeleton className="h-4 w-1/4" />
          <Skeleton className="h-4 w-1/3" />
          <Skeleton className="h-4 w-1/6" />
          <Skeleton className="h-4 w-1/6" />
        </div>
      ))}
    </div>
  )
}

// Page Header
export function PageHeader({ title, subtitle, actions, showBack = false, showRefresh = false, onRefresh }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [spinning, setSpinning] = useState(false)

  const handleRefresh = async () => {
    if (spinning) return
    setSpinning(true)
    try {
      // Page-specific reset (clears form inputs / selections / generated output).
      if (onRefresh) await onRefresh()
      // Always invalidate React Query caches so server data refetches too.
      await queryClient.invalidateQueries()
      toast.success('Page reset', { id: 'page-refresh', duration: 1200 })
    } catch (err) {
      toast.error('Refresh failed', { id: 'page-refresh' })
    } finally {
      // Keep the spin visible briefly so the click always feels responsive.
      setTimeout(() => setSpinning(false), 400)
    }
  }

  return (
    <div className="page-header flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div className="flex items-center gap-3">
        {showBack && (
          <button
            onClick={() => navigate(-1)}
            className="inline-flex items-center justify-center w-9 h-9 rounded-lg text-gray-500 hover:text-gray-900 hover:bg-gray-100 transition-colors"
            title="Go back"
          >
            <ArrowLeft size={20} />
          </button>
        )}
        <div>
          <h1 className="page-title">{title}</h1>
          {subtitle && <p className="page-subtitle">{subtitle}</p>}
        </div>
      </div>
      <div className="flex gap-3 items-center">
        {showRefresh && (
          <button
            onClick={handleRefresh}
            disabled={spinning}
            className="inline-flex items-center justify-center w-9 h-9 rounded-lg text-gray-500 hover:text-gray-900 hover:bg-gray-100 transition-colors disabled:opacity-60"
            title="Refresh"
          >
            <RotateCw size={18} className={clsx(spinning && 'animate-spin')} />
          </button>
        )}
        {actions}
      </div>
    </div>
  )
}

// Section Header
export function SectionHeader({ title, action }) {
  return (
    <div className="flex items-center justify-between mb-6">
      <h2 className="section-title mb-0">{title}</h2>
      {action}
    </div>
  )
}

// Tabs
export function Tabs({ tabs, activeTab, onChange }) {
  return (
    <div className="border-b border-gray-200">
      <nav className="flex gap-8" aria-label="Tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={clsx(
              'py-4 px-1 border-b-2 font-medium text-sm transition-colors',
              activeTab === tab.id
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            )}
          >
            {tab.icon && <tab.icon className="inline-block mr-2" size={18} />}
            {tab.label}
            {tab.count !== undefined && (
              <span className="ml-2 bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </nav>
    </div>
  )
}

// Search Input
export function SearchInput({ value, onChange, placeholder = 'Search...', className = '' }) {
  return (
    <div className={clsx('relative', className)}>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="input pl-10"
      />
      <svg
        className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.35-4.35" />
      </svg>
    </div>
  )
}

// Select
export function Select({ options, value, onChange, placeholder = 'Select...', className = '' }) {
  return (
    <select
      value={value || ''}
      onChange={(e) => onChange(e.target.value || null)}
      className={clsx('input', className)}
    >
      <option value="">{placeholder}</option>
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  )
}

// Pagination
export function Pagination({ currentPage, totalPages, onPageChange }) {
  const pages = []
  const showPages = 5

  let start = Math.max(1, currentPage - Math.floor(showPages / 2))
  let end = Math.min(totalPages, start + showPages - 1)

  if (end - start + 1 < showPages) {
    start = Math.max(1, end - showPages + 1)
  }

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }

  if (totalPages <= 1) return null

  return (
    <div className="flex items-center justify-center gap-2 mt-6">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="btn btn-outline btn-sm disabled:opacity-50"
      >
        Previous
      </button>

      {start > 1 && (
        <>
          <button onClick={() => onPageChange(1)} className="btn btn-outline btn-sm">
            1
          </button>
          {start > 2 && <span className="px-2">...</span>}
        </>
      )}

      {pages.map((page) => (
        <button
          key={page}
          onClick={() => onPageChange(page)}
          className={clsx(
            'btn btn-sm',
            page === currentPage ? 'btn-primary' : 'btn-outline'
          )}
        >
          {page}
        </button>
      ))}

      {end < totalPages && (
        <>
          {end < totalPages - 1 && <span className="px-2">...</span>}
          <button onClick={() => onPageChange(totalPages)} className="btn btn-outline btn-sm">
            {totalPages}
          </button>
        </>
      )}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="btn btn-outline btn-sm disabled:opacity-50"
      >
        Next
      </button>
    </div>
  )
}

// Modal
export function Modal({ isOpen, onClose, title, children, size = 'md' }) {
  if (!isOpen) return null

  const sizes = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-6xl',
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="fixed inset-0 bg-black/50" onClick={onClose} />
        <div className={clsx(
          'relative bg-white rounded-xl shadow-xl w-full p-6 animate-slide-up',
          sizes[size]
        )}>
          {title && (
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                &#10005;
              </button>
            </div>
          )}
          {children}
        </div>
      </div>
    </div>
  )
}
