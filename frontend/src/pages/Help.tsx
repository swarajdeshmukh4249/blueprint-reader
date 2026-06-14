import { SignedIn } from '@clerk/clerk-react'
import { Book, FileText, Video, MessageCircle, Search, ChevronRight } from 'lucide-react'
import Container from '@/components/Container'
import { useState } from 'react'

export default function Help() {
  const [searchQuery, setSearchQuery] = useState('')
  const [activeCategory, setActiveCategory] = useState('getting-started')

  const categories = [
    { id: 'getting-started', label: 'Getting Started', icon: Book },
    { id: 'user-guide', label: 'User Guide', icon: FileText },
    { id: 'video-tutorials', label: 'Video Tutorials', icon: Video },
    { id: 'faq', label: 'FAQ', icon: MessageCircle },
  ]

  const helpItems: Record<string, Array<{ id: string; title: string; description: string; category: string; duration?: string }>> = {
    'getting-started': [
      {
        id: '1',
        title: 'Quick Start Guide',
        description: 'Learn the basics of Blueprint Reader in 5 minutes',
        category: 'Basics'
      },
      {
        id: '2',
        title: 'Account Setup',
        description: 'How to create and configure your account',
        category: 'Account'
      },
      {
        id: '3',
        title: 'First Blueprint Analysis',
        description: 'Step-by-step guide to analyze your first blueprint',
        category: 'Tutorial'
      },
      {
        id: '4',
        title: 'Understanding Results',
        description: 'How to interpret and use analysis results',
        category: 'Results'
      }
    ],
    'user-guide': [
      {
        id: '5',
        title: 'Upload Blueprints',
        description: 'Supported formats and upload best practices',
        category: 'Upload'
      },
      {
        id: '6',
        title: 'Analysis Settings',
        description: 'Configure analysis parameters for better results',
        category: 'Settings'
      },
      {
        id: '7',
        title: 'BOQ Generation',
        description: 'Generate and customize Bill of Quantities',
        category: 'BOQ'
      },
      {
        id: '8',
        title: 'Export Options',
        description: 'Download results in various formats',
        category: 'Export'
      }
    ],
    'video-tutorials': [
      {
        id: '9',
        title: 'Introduction to Blueprint Reader',
        description: 'Overview video of all features',
        category: 'Overview',
        duration: '5:30'
      },
      {
        id: '10',
        title: 'Advanced Analysis Techniques',
        description: 'Tips for better blueprint analysis',
        category: 'Advanced',
        duration: '8:15'
      },
      {
        id: '11',
        title: 'Team Collaboration',
        description: 'Working with teams on projects',
        category: 'Collaboration',
        duration: '6:45'
      }
    ],
    'faq': [
      {
        id: '12',
        title: 'What file formats are supported?',
        description: 'We support PDF, PNG, JPG, DXF, and DWG files',
        category: 'General'
      },
      {
        id: '13',
        title: 'How accurate is the analysis?',
        description: 'Our AI achieves 85-95% accuracy depending on blueprint quality',
        category: 'Accuracy'
      },
      {
        id: '14',
        title: 'Can I analyze multi-floor buildings?',
        description: 'Yes, our system can detect and analyze multiple floors',
        category: 'Features'
      },
      {
        id: '15',
        title: 'Is my data secure?',
        description: 'All data is encrypted and stored securely',
        category: 'Security'
      }
    ]
  }

  const currentItems = helpItems[activeCategory as keyof typeof helpItems] || []
  const filteredItems = currentItems.filter(item =>
    item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <SignedIn>
      <div className="min-h-screen">
        <Container className="py-8">
          <div className="mb-8">
            <h1 className="font-display text-3xl tracking-tight text-ink">Help Center</h1>
            <p className="mt-2 text-sm text-ink/70">
              Find answers, guides, and tutorials to help you get the most out of Blueprint Reader
            </p>
          </div>

          {/* Search */}
          <div className="mb-8">
            <div className="relative max-w-2xl">
              <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-ink/50" />
              <input
                type="text"
                placeholder="Search for help articles, guides, and FAQs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-lg border border-ink/15 bg-paper pl-12 pr-4 py-4 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              />
            </div>
          </div>

          <div className="flex gap-8">
            {/* Sidebar */}
            <aside className="w-64 flex-shrink-0">
              <nav className="space-y-1">
                {categories.map((category) => {
                  const Icon = category.icon
                  return (
                    <button
                      key={category.id}
                      onClick={() => setActiveCategory(category.id)}
                      className={`flex w-full items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition-colors ${
                        activeCategory === category.id
                          ? 'bg-accent/10 text-accent'
                          : 'text-ink/70 hover:bg-paper-2 hover:text-ink'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      {category.label}
                    </button>
                  )
                })}
              </nav>

              {/* Quick Links */}
              <div className="mt-8 rounded-lg border border-ink/10 bg-paper-2/50 p-4">
                <h3 className="text-sm font-medium text-ink">Quick Links</h3>
                <div className="mt-3 space-y-2">
                  <a href="#" className="flex items-center gap-2 text-xs text-ink/70 hover:text-accent">
                    <ChevronRight className="h-3 w-3" />
                    Contact Support
                  </a>
                  <a href="#" className="flex items-center gap-2 text-xs text-ink/70 hover:text-accent">
                    <ChevronRight className="h-3 w-3" />
                    API Documentation
                  </a>
                  <a href="#" className="flex items-center gap-2 text-xs text-ink/70 hover:text-accent">
                    <ChevronRight className="h-3 w-3" />
                    Community Forum
                  </a>
                </div>
              </div>
            </aside>

            {/* Content */}
            <main className="flex-1">
              <div className="mb-6">
                <h2 className="font-display text-xl tracking-tight text-ink">
                  {categories.find(c => c.id === activeCategory)?.label}
                </h2>
              </div>

              <div className="space-y-4">
                {filteredItems.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-lg border border-ink/10 bg-paper-2/50 p-6 transition hover:border-accent/30 hover:shadow-md"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="text-base font-medium text-ink">{item.title}</h3>
                          {item.duration && (
                            <span className="rounded-full bg-accent/10 px-2 py-0.5 text-xs text-accent">
                              {item.duration}
                            </span>
                          )}
                        </div>
                        <p className="mt-2 text-sm text-ink/70">{item.description}</p>
                        <div className="mt-3">
                          <span className="rounded-full border border-ink/15 bg-paper px-2 py-0.5 text-xs text-ink/70">
                            {item.category}
                          </span>
                        </div>
                      </div>
                      <button className="ml-4 flex h-8 w-8 items-center justify-center rounded-full border border-ink/15 bg-paper text-ink/70 transition hover:bg-accent hover:text-paper">
                        <ChevronRight className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {filteredItems.length === 0 && (
                <div className="rounded-lg border border-ink/10 bg-paper-2/50 p-12 text-center">
                  <Search className="mx-auto h-12 w-12 text-ink/30" />
                  <h3 className="mt-4 font-display text-lg tracking-tight text-ink">No results found</h3>
                  <p className="mt-2 text-sm text-ink/70">
                    Try adjusting your search terms
                  </p>
                </div>
              )}

              {/* Contact Support */}
              <div className="mt-8 rounded-lg border border-accent/20 bg-accent/5 p-6">
                <div className="flex items-start gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-accent/10 text-accent">
                    <MessageCircle className="h-6 w-6" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-display text-lg tracking-tight text-ink">Still need help?</h3>
                    <p className="mt-1 text-sm text-ink/70">
                      Our support team is available 24/7 to assist you with any questions.
                    </p>
                    <button className="mt-3 rounded-full bg-accent px-4 py-2 text-sm font-medium text-paper transition hover:bg-accent/90">
                      Contact Support
                    </button>
                  </div>
                </div>
              </div>
            </main>
          </div>
        </Container>
      </div>
    </SignedIn>
  )
}
