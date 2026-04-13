import { makeAutoObservable, runInAction } from "mobx";

import { ApiError } from "@/shared/api/apiClient";
import { RepositoryService } from "../services/RepositoryService";
import type {
  GitHubRepository,
  LoadState,
  PaginationMetadata,
  RepositoryRow,
} from "../types";
import { LOAD_STATE } from "../constants";

export interface IRepositoryStore {
  // State properties
  selectedLanguages: string[];
  languageInput: string;
  createdAfter: string;
  page: number;
  readonly perPage: number;
  state: LoadState;
  errorMessage: string | null;
  repos: GitHubRepository[];
  paginationMeta: PaginationMetadata | null;

  // Computed getters
  readonly isLoading: boolean;
  readonly hasError: boolean;
  readonly resultCount: number;
  readonly hasNext: boolean;
  readonly hasPrevious: boolean;
  readonly canGoToNextPage: boolean;
  readonly canGoToPreviousPage: boolean;
  readonly rows: RepositoryRow[];
  readonly canSearch: boolean;

  // Actions
  setLanguageInput(value: string): void;
  addLanguage(language: string): void;
  removeLanguage(language: string): void;
  clearLanguages(): void;
  setCreatedAfter(value: string): void;
  setPage(value: number): void;
  nextPage(): void;
  previousPage(): void;
  goToPage(page: number): void;
  resetPaging(): void;
  performSearch(): Promise<void>;
  search(): Promise<void>;
  onSubmitSearch(): void;
  clearError(): void;
}

export class StoreRepository implements IRepositoryStore {
  selectedLanguages: string[] = [];
  languageInput = "";
  createdAfter = "";

  page = 1;
  readonly perPage = 25; // Fixed page size

  state: LoadState = LOAD_STATE.IDLE;
  errorMessage: string | null = null;
  isRateLimitError = false;
  repos: GitHubRepository[] = [];
  paginationMeta: PaginationMetadata | null = null;

  // Track pending request to prevent duplicates
  private pendingRequest: Promise<void> | null = null;

  constructor() {
    makeAutoObservable(this, {}, { autoBind: true });
    void this.search();
  }

  get isLoading() {
    return this.state === LOAD_STATE.LOADING;
  }

  get hasError() {
    return this.state === LOAD_STATE.ERROR;
  }

  get resultCount() {
    return this.repos.length;
  }

  get hasNext() {
    return this.paginationMeta?.has_next ?? false;
  }

  get hasPrevious() {
    return this.paginationMeta?.has_previous ?? false;
  }

  get canGoToNextPage() {
    return this.hasNext && !this.isLoading;
  }

  get canGoToPreviousPage() {
    return this.hasPrevious && !this.isLoading;
  }

  get rows(): RepositoryRow[] {
    return (this.repos || []).map((repo): RepositoryRow => {
      const updatedDate = repo.updated_at ? repo.updated_at.slice(0, 10) : "—";

      // Sort topics using service business logic
      const relevantTopics = RepositoryService.getSortedTopics(
        repo.topics,
        repo.language,
        this.selectedLanguages,
      );

      return {
        id: repo.id,
        fullName: repo.full_name,
        url: repo.url,
        language: repo.language,
        topics: relevantTopics,
        starsText: repo.stars.toLocaleString(),
        forksText: repo.forks.toLocaleString(),
        watchersText: repo.watchers.toLocaleString(),
        score: repo.score.toFixed(4),
        updatedDate,
      };
    });
  }

  get canSearch() {
    return !this.isLoading;
  }

  setLanguageInput(value: string) {
    this.languageInput = value;
  }

  addLanguage(language: string) {
    const trimmed = language.trim();
    if (trimmed && !this.selectedLanguages.includes(trimmed)) {
      this.selectedLanguages.push(trimmed);
      this.languageInput = "";
    }
  }

  removeLanguage(language: string) {
    this.selectedLanguages = this.selectedLanguages.filter(
      (l) => l !== language,
    );
  }

  clearLanguages() {
    this.selectedLanguages = [];
  }

  setCreatedAfter(value: string) {
    this.createdAfter = value;
  }

  setPage(value: number) {
    // Prevent page changes during loading to avoid race conditions
    if (this.isLoading) return;

    this.page = value;
    void this.search();
  }

  nextPage() {
    if (this.isLoading) return;
    this.setPage(this.page + 1);
  }

  previousPage() {
    if (this.isLoading) return;
    if (this.page > 1) {
      this.setPage(this.page - 1);
    }
  }

  goToPage(page: number) {
    if (this.isLoading) return;
    if (page >= 1 && page !== this.page) {
      this.setPage(page);
    }
  }

  resetPaging() {
    this.page = 1;
  }

  async performSearch() {
    this.resetPaging();
    await this.search();
  }

  async search() {
    // Prevent duplicate simultaneous requests
    if (this.pendingRequest) {
      return this.pendingRequest;
    }

    // Always set loading state to prevent race conditions and spam-clicking
    // This ensures pagination buttons are properly disabled during requests
    this.state = LOAD_STATE.LOADING;
    this.errorMessage = null;

    const request = (async () => {
      try {
        const response = await RepositoryService.search({
          languages: this.selectedLanguages,
          createdAfter: this.createdAfter,
          page: this.page,
          perPage: this.perPage,
        });

        runInAction(() => {
          this.repos = response.items || [];
          this.paginationMeta = response.pagination;
          this.state = LOAD_STATE.SUCCESS;
          this.pendingRequest = null;
        });
      } catch (err) {
        let message = "Failed to load repositories";
        let isRateLimit = false;

        if (err instanceof ApiError) {
          // Check if this is a rate limit error (503 from backend when GitHub rate limits)
          if (err.status === 503) {
            message =
              "GitHub API rate limit reached. Please wait a few minutes before trying again.";
            isRateLimit = true;
          } else {
            message = err.message;
          }
        } else if (err instanceof Error) {
          message = err.message;
        }

        runInAction(() => {
          this.state = LOAD_STATE.ERROR;
          this.errorMessage = message;
          this.isRateLimitError = isRateLimit;
          this.repos = [];
          this.pendingRequest = null;
        });
      }
    })();

    this.pendingRequest = request;
    return request;
  }

  onSubmitSearch() {
    void this.performSearch();
  }

  clearError() {
    this.errorMessage = null;
    this.isRateLimitError = false;
    if (this.state === LOAD_STATE.ERROR) this.state = LOAD_STATE.IDLE;
  }
}
