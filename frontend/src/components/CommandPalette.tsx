import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Command, Home, Upload, BarChart3, FolderOpen, FileText, Share2, GitCompare, X } from 'lucide-react'

interface Command {
  id: string
  label: string
  icon: any
  action: () => void
  category: string
}

export default function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [filteredCommands, setFilteredCommands] = useState<Command[]>([])
  const navigate = useNavigate()

  const commands: Command[] = [
    {
      id: 'home',
      label: 'Go to Home',
      icon: Home,
      action: () => navigate('/'),
      category: 'Navigation'
    },
    {
      id: 'dashboard',
      label: 'Go to Dashboard',
      icon: FolderOpen,
      action: () => navigate('/dashboard'),
      category: 'Navigation'
    },
    {
      id: 'upload',
      label: 'Upload Blueprint',
      icon: Upload,
      action: () => navigate('/upload'),
      category: 'Actions'
    },
    {
      id: 'analytics',
      label: 'Enterprise Analytics',
      icon: BarChart3,
      action: () => navigate('/enterprise-dashboard'),
      category: 'Navigation'
    },
    {
      id: 'floor-compare',
      label: 'Floor Comparison',
      icon: GitCompare,
      action: () => navigate('/floor-comparison/default'),
      category: 'Actions'
    },
    {
      id: 'share',
      label: 'Client Share Portal',
      icon: Share2,
      action: () => navigate('/public-share/default'),
      category: 'Actions'
    },
    {
      id: 'recent-files',
      label: 'View Recent Files',
      icon: FileText,
      action: () => navigate('/dashboard'),
      category: 'Actions'
    }
  ]

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setIsOpen(true)
      }
      if (e.key === 'Escape') {
        setIsOpen(false)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  useEffect(() => {
    if (query) {
      const filtered = commands.filter(cmd =>
        cmd.label.toLowerCase().includes(query.toLowerCase())
      )
      setFilteredCommands(filtered)
    } else {
      setFilteredCommands(commands)
    }
  }, [query])

  const handleCommandSelect = (command: Command) => {
    command.action()
    setIsOpen(false)
    setQuery('')
  }

  const getCategoryCommands = (category: string) => {
    return filteredCommands.filter(cmd => cmd.category === category)
  }

  const categories = Array.from(new Set(filteredCommands.map(cmd => cmd.category)))

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]">
      <div className="absolute inset-0 bg-black/50" onClick={() => setIsOpen(false)} />
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-2xl mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center px-4 py-3 border-b">
          <Search className="w-5 h-5 text-gray-400 mr-3" />
          <input
            type="text"
            placeholder="Search commands..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 outline-none text-gray-900 placeholder-gray-400"
            autoFocus
          />
          <button
            onClick={() => setIsOpen(false)}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Keyboard shortcut hint */}
        <div className="px-4 py-2 bg-gray-50 border-b flex items-center justify-between text-xs text-gray-500">
          <span>Press <kbd className="px-1.5 py-0.5 bg-gray-200 rounded text-gray-700">Esc</kbd> to close</span>
          <span className="flex items-center gap-1">
            <kbd className="px-1.5 py-0.5 bg-gray-200 rounded text-gray-700">↑↓</kbd> to navigate
            <kbd className="px-1.5 py-0.5 bg-gray-200 rounded text-gray-700">Enter</kbd> to select
          </span>
        </div>

        {/* Commands list */}
        <div className="max-h-[400px] overflow-y-auto">
          {filteredCommands.length === 0 ? (
            <div className="px-4 py-8 text-center text-gray-500">
              No commands found
            </div>
          ) : (
            categories.map(category => (
              <div key={category}>
                <div className="px-4 py-2 bg-gray-50 text-xs font-medium text-gray-500 uppercase">
                  {category}
                </div>
                {getCategoryCommands(category).map((command, index) => (
                  <button
                    key={command.id}
                    onClick={() => handleCommandSelect(command)}
                    className="w-full flex items-center px-4 py-3 hover:bg-gray-50 transition-colors"
                  >
                    <command.icon className="w-5 h-5 text-gray-400 mr-3" />
                    <span className="flex-1 text-left text-gray-900">{command.label}</span>
                  </button>
                ))}
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 bg-gray-50 border-t flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center gap-2">
            <Command className="w-4 h-4" />
            <span>Press</span>
            <kbd className="px-1.5 py-0.5 bg-gray-200 rounded text-gray-700">Cmd</kbd>
            <span>+</span>
            <kbd className="px-1.5 py-0.5 bg-gray-200 rounded text-gray-700">K</kbd>
            <span>to open</span>
          </div>
        </div>
      </div>
    </div>
  )
}
