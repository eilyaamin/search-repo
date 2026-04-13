import { ChevronLeft, ChevronRight, ChevronsLeft } from 'lucide-react'

import { Button } from './button'

export type PaginationProps = {
  currentPage: number
  onPageChange: (page: number) => void
  disabled?: boolean
  hasMorePages?: boolean
}

export function Pagination({
  currentPage,
  onPageChange,
  disabled = false,
  hasMorePages = true,
}: PaginationProps) {
  const isFirstPage = currentPage === 1

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span>
          Page {currentPage}
        </span>
      </div>

      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          size="icon"
          onClick={() => onPageChange(1)}
          disabled={disabled || isFirstPage}
          aria-label="First page"
        >
          <ChevronsLeft className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={disabled || isFirstPage}
          aria-label="Previous page"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>

        <div className="flex items-center gap-1 px-2">
          <span className="text-sm font-medium">
            Page {currentPage}
          </span>
        </div>

        <Button
          variant="outline"
          size="icon"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={disabled || !hasMorePages}
          aria-label="Next page"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
