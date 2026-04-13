import { GitCompare } from 'lucide-react'

export function Navbar() {
  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-green-950 text-white">
      <div className="container flex h-16 items-center justify-center">
        <div className="flex items-center gap-2">
          <GitCompare className="h-6 w-6" />
          <span className="text-lg font-semibold">Repository Search</span>
        </div>
      </div>
    </nav>
  )
}
