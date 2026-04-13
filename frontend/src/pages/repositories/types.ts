import type { LOAD_STATE } from "./constants"

export type RepoSearchParams = {
  languages?: string[]
  createdAfter?: string
  page?: number
  perPage?: number
}

export type GitHubRepository = {
  id: number
  name?: string
  full_name: string
  url: string
  stars: number
  forks: number
  watchers: number
  language: string | null
  topics: string[]
  updated_at: string
  score: number
}

export type PaginationMetadata = {
  current_page: number
  per_page: number
  has_next: boolean
  has_previous: boolean
}

export type RepositoryRow = {
  id: number;
  fullName: string;
  url: string;
  language: string | null;
  topics: string[];
  starsText: string;
  forksText: string;
  watchersText: string;
  score: string;
  updatedDate: string;
};

export type RepoSearchResponse = {
  items: GitHubRepository[]
  pagination: PaginationMetadata
}

export type LoadState = typeof LOAD_STATE[keyof typeof LOAD_STATE];