import { observer } from "mobx-react-lite";
import { ExternalLink, Loader2 } from "lucide-react";

import { useRepositoryStore } from "./store/hooks";
import { RepositoryService } from "./services/RepositoryService";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { LanguageSelector } from "@/shared/ui/language-selector";
import { Pagination } from "@/shared/ui/pagination";
import {
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";

export const RepositoriesPage = observer(function RepositoriesPage() {
  const store = useRepositoryStore();

  return (
    <main className="container py-8">
      <Card>
        <CardHeader className="gap-2">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-1">
              <CardTitle>Repositories</CardTitle>
              <CardDescription>Search GitHub repositories.</CardDescription>
            </div>

            {store.hasError && store.errorMessage ? (
              <div
                className={`rounded-md border w-full max-w-96 min-w-fit p-3 text-sm ${
                  store.isRateLimitError
                    ? "border-yellow-500/40 bg-yellow-500/10 text-yellow-700 dark:text-yellow-400"
                    : "border-destructive/40 bg-destructive/10 text-destructive"
                }`}
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="leading-relaxed">{store.errorMessage}</p>
                  <Button variant="ghost" size="sm" onClick={store.clearError}>
                    Dismiss
                  </Button>
                </div>
              </div>
            ) : null}
          </div>

          <section className="flex flex-col md:flex-row items-start">
            <div className="grid gap-4 pt-2 sm:grid-cols-2 items-start w-full">
              <LanguageSelector
                selectedLanguages={store.selectedLanguages}
                onAdd={store.addLanguage}
                onRemove={store.removeLanguage}
                onClear={store.clearLanguages}
                onInputChange={store.setLanguageInput}
                inputValue={store.languageInput}
                onFetchSuggestions={RepositoryService.getLanguageSuggestions}
              />

              <div className="grid gap-2">
                <Label htmlFor="created-after">Created after</Label>
                <Input
                  className="w-fit"
                  id="created-after"
                  type="date"
                  value={store.createdAfter}
                  onChange={(e) => store.setCreatedAfter(e.target.value)}
                />
              </div>
            </div>
            <div className="flex items-center gap-2 w-full md:w-fit pb-4 translate-y-6">
              <Button
                onClick={store.onSubmitSearch}
                disabled={!store.canSearch}
                className="w-full"
              >
                {store.isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : null}
                Search
              </Button>
            </div>
          </section>
        </CardHeader>

        <CardContent>
          <div className="rounded-lg border relative">
            {/* Loading overlay for smooth transitions */}
            {store.isLoading && store.repos.length > 0 && (
              <div className="absolute inset-0 bg-background/50 backdrop-blur-sm z-20 flex items-center justify-center">
                <div className="flex items-center gap-2 text-sm text-muted-foreground bg-background px-4 py-2 rounded-md shadow-lg border">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Loading…</span>
                </div>
              </div>
            )}

            <div className="max-h-[600px] overflow-y-auto w-full">
              <table className="w-full caption-bottom text-sm">
                <TableHeader>
                  <TableRow>
                    <TableHead>Repository</TableHead>
                    <TableHead className="hidden md:table-cell">
                      Topics
                    </TableHead>
                    <TableHead className="text-right">Stars</TableHead>
                    <TableHead className="text-right hidden sm:table-cell">
                      Forks
                    </TableHead>
                    <TableHead className="hidden lg:table-cell">
                      Updated
                    </TableHead>
                    <TableHead className="w-0" />
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {store.rows.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium">{row.fullName}</span>
                          <a
                            className="text-xs text-muted-foreground hover:underline"
                            href={row.url}
                            target="_blank"
                            rel="noreferrer"
                          >
                            {row.url}
                          </a>
                        </div>
                      </TableCell>
                      <TableCell className="hidden md:table-cell">
                        {row.topics && row.topics.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {row.topics.map((topic, idx) => (
                              <Badge key={idx} variant="secondary">
                                {topic}
                              </Badge>
                            ))}
                          </div>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {row.starsText}
                      </TableCell>
                      <TableCell className="text-right tabular-nums hidden sm:table-cell">
                        {row.forksText}
                      </TableCell>
                      <TableCell className="hidden lg:table-cell text-muted-foreground">
                        {row.updatedDate}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="icon">
                          <a
                            href={row.url}
                            target="_blank"
                            rel="noreferrer"
                            aria-label="Open on GitHub"
                          >
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}

                  {!store.isLoading && store.resultCount === 0 ? (
                    <TableRow>
                      <TableCell
                        colSpan={6}
                        className="py-10 text-center text-muted-foreground"
                      >
                        No repositories found.
                      </TableCell>
                    </TableRow>
                  ) : null}

                  {store.isLoading && store.repos.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="py-10">
                        <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                          <Loader2 className="h-4 w-4 animate-spin" />
                          Loading…
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : null}
                </TableBody>
              </table>
            </div>
          </div>

          <div className="pt-4">
            <Pagination
              currentPage={store.page}
              onPageChange={store.goToPage}
              disabled={store.isLoading}
              hasMorePages={store.hasNext}
            />
          </div>
        </CardContent>
      </Card>
    </main>
  );
});
