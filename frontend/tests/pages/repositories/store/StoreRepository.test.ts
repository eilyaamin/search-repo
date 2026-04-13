import { describe, it, expect, vi, beforeEach } from "vitest";
import { StoreRepository } from "../../../../src/pages/repositories/store/StoreRepository";
import { RepositoryService } from "../../../../src/pages/repositories/services/RepositoryService";
import { LOAD_STATE } from "../../../../src/pages/repositories/constants";
import { ApiError } from "../../../../src/shared/api/apiClient";

// Mock the RepositoryService
vi.mock("@/pages/repositories/services/RepositoryService", () => ({
  RepositoryService: {
    search: vi.fn(),
    getSortedTopics: vi.fn(),
  },
}));

describe("StoreRepository", () => {
  let store: StoreRepository;

  beforeEach(() => {
    vi.clearAllMocks();
    // Mock search to prevent initial search in constructor
    vi.mocked(RepositoryService.search).mockResolvedValue({
      items: [],
      pagination: {
        page: 1,
        per_page: 25,
        total: 0,
        has_next: false,
        has_previous: false,
      },
    });
  });

  describe("initialization", () => {
    it("should initialize with default values", async () => {
      store = new StoreRepository();

      // Wait for initial search to complete
      await vi.waitFor(() => {
        expect(store.state).toBe(LOAD_STATE.SUCCESS);
      });

      expect(store.selectedLanguages).toEqual([]);
      expect(store.languageInput).toBe("");
      expect(store.createdAfter).toBe("");
      expect(store.page).toBe(1);
      expect(store.perPage).toBe(25);
      expect(store.errorMessage).toBeNull();
      expect(store.repos).toEqual([]);
      expect(store.paginationMeta).not.toBeNull();
    });

    it("should call search on initialization", () => {
      store = new StoreRepository();
      expect(RepositoryService.search).toHaveBeenCalledTimes(1);
    });
  });

  describe("computed properties", () => {
    beforeEach(() => {
      store = new StoreRepository();
    });

    describe("isLoading", () => {
      it("should return true when state is LOADING", () => {
        store.state = LOAD_STATE.LOADING;
        expect(store.isLoading).toBe(true);
      });

      it("should return false when state is not LOADING", () => {
        store.state = LOAD_STATE.SUCCESS;
        expect(store.isLoading).toBe(false);
      });
    });

    describe("hasError", () => {
      it("should return true when state is ERROR", () => {
        store.state = LOAD_STATE.ERROR;
        expect(store.hasError).toBe(true);
      });

      it("should return false when state is not ERROR", () => {
        store.state = LOAD_STATE.SUCCESS;
        expect(store.hasError).toBe(false);
      });
    });

    describe("resultCount", () => {
      it("should return the number of repositories", () => {
        store.repos = [{ id: 1 }, { id: 2 }, { id: 3 }] as any;
        expect(store.resultCount).toBe(3);
      });
    });

    describe("pagination computed values", () => {
      it("should compute hasNext correctly", () => {
        store.paginationMeta = { has_next: true } as any;
        expect(store.hasNext).toBe(true);

        store.paginationMeta = { has_next: false } as any;
        expect(store.hasNext).toBe(false);

        store.paginationMeta = null;
        expect(store.hasNext).toBe(false);
      });

      it("should compute hasPrevious correctly", () => {
        store.paginationMeta = { has_previous: true } as any;
        expect(store.hasPrevious).toBe(true);

        store.paginationMeta = { has_previous: false } as any;
        expect(store.hasPrevious).toBe(false);
      });

      it("should compute canGoToNextPage correctly", () => {
        store.paginationMeta = { has_next: true } as any;
        store.state = LOAD_STATE.SUCCESS;
        expect(store.canGoToNextPage).toBe(true);

        store.state = LOAD_STATE.LOADING;
        expect(store.canGoToNextPage).toBe(false);
      });

      it("should compute canGoToPreviousPage correctly", () => {
        store.paginationMeta = { has_previous: true } as any;
        store.state = LOAD_STATE.SUCCESS;
        expect(store.canGoToPreviousPage).toBe(true);

        store.state = LOAD_STATE.LOADING;
        expect(store.canGoToPreviousPage).toBe(false);
      });
    });

    describe("canSearch", () => {
      it("should return true when not loading", () => {
        store.state = LOAD_STATE.SUCCESS;
        expect(store.canSearch).toBe(true);
      });

      it("should return false when loading", () => {
        store.state = LOAD_STATE.LOADING;
        expect(store.canSearch).toBe(false);
      });
    });

    describe("rows", () => {
      it("should transform repositories into row format", () => {
        vi.mocked(RepositoryService.getSortedTopics).mockReturnValue([
          "topic1",
          "topic2",
        ]);

        store.repos = [
          {
            id: 123,
            full_name: "user/repo",
            url: "https://github.com/user/repo",
            language: "TypeScript",
            topics: ["topic1", "topic2", "topic3"],
            stars: 1234,
            forks: 567,
            watchers: 890,
            score: 8.5432,
            updated_at: "2024-01-15T12:00:00Z",
          },
        ] as any;

        const rows = store.rows;

        expect(rows).toHaveLength(1);
        expect(rows[0]).toEqual({
          id: 123,
          fullName: "user/repo",
          url: "https://github.com/user/repo",
          language: "TypeScript",
          topics: ["topic1", "topic2"],
          starsText: "1,234",
          forksText: "567",
          watchersText: "890",
          score: "8.5432",
          updatedDate: "2024-01-15",
        });
      });

      it("should handle missing updated_at date", () => {
        vi.mocked(RepositoryService.getSortedTopics).mockReturnValue([]);

        store.repos = [
          {
            id: 123,
            full_name: "user/repo",
            url: "https://github.com/user/repo",
            language: null,
            topics: [],
            stars: 0,
            forks: 0,
            watchers: 0,
            score: 0,
            updated_at: null,
          },
        ] as any;

        const rows = store.rows;

        expect(rows[0].updatedDate).toBe("—");
      });

      it("should call RepositoryService.getSortedTopics with correct parameters", () => {
        store.selectedLanguages = ["TypeScript", "JavaScript"];
        store.repos = [
          {
            id: 123,
            full_name: "user/repo",
            url: "https://github.com/user/repo",
            topics: ["react", "vue", "angular"],
            language: "TypeScript",
            stars: 100,
            forks: 50,
            watchers: 25,
            score: 5.5,
            updated_at: "2024-01-01T00:00:00Z",
          },
        ] as any;

        store.rows; // Access to trigger computation

        expect(RepositoryService.getSortedTopics).toHaveBeenCalledWith(
          ["react", "vue", "angular"],
          "TypeScript",
          ["TypeScript", "JavaScript"],
        );
      });
    });
  });

  describe("language management actions", () => {
    beforeEach(() => {
      store = new StoreRepository();
    });

    describe("setLanguageInput", () => {
      it("should update languageInput", () => {
        store.setLanguageInput("Python");
        expect(store.languageInput).toBe("Python");
      });
    });

    describe("addLanguage", () => {
      it("should add a new language and clear input", () => {
        store.languageInput = "TypeScript";
        store.addLanguage("TypeScript");

        expect(store.selectedLanguages).toContain("TypeScript");
        expect(store.languageInput).toBe("");
      });

      it("should trim whitespace from language", () => {
        store.addLanguage("  JavaScript  ");
        expect(store.selectedLanguages).toContain("JavaScript");
      });

      it("should not add duplicate languages", () => {
        store.addLanguage("Python");
        store.addLanguage("Python");

        expect(
          store.selectedLanguages.filter((l) => l === "Python"),
        ).toHaveLength(1);
      });

      it("should not add empty strings", () => {
        store.addLanguage("");
        store.addLanguage("   ");

        expect(store.selectedLanguages).toHaveLength(0);
      });
    });

    describe("removeLanguage", () => {
      it("should remove a language from the list", () => {
        store.selectedLanguages = ["TypeScript", "JavaScript", "Python"];
        store.removeLanguage("JavaScript");

        expect(store.selectedLanguages).toEqual(["TypeScript", "Python"]);
      });
    });

    describe("clearLanguages", () => {
      it("should clear all selected languages", () => {
        store.selectedLanguages = ["TypeScript", "JavaScript", "Python"];
        store.clearLanguages();

        expect(store.selectedLanguages).toEqual([]);
      });
    });
  });

  describe("date filter actions", () => {
    beforeEach(() => {
      store = new StoreRepository();
    });

    it("should update createdAfter", () => {
      store.setCreatedAfter("2024-01-01");
      expect(store.createdAfter).toBe("2024-01-01");
    });
  });

  describe("pagination actions", () => {
    beforeEach(() => {
      store = new StoreRepository();
    });

    describe("setPage", () => {
      it("should update page and trigger search", () => {
        vi.clearAllMocks();
        store.state = LOAD_STATE.SUCCESS;

        store.setPage(2);

        expect(store.page).toBe(2);
        expect(RepositoryService.search).toHaveBeenCalled();
      });

      it("should not update page when loading", () => {
        store.state = LOAD_STATE.LOADING;
        store.page = 1;

        store.setPage(2);

        expect(store.page).toBe(1);
      });
    });

    describe("nextPage", () => {
      it("should increment page", () => {
        vi.clearAllMocks();
        store.state = LOAD_STATE.SUCCESS;
        store.page = 1;

        store.nextPage();

        expect(store.page).toBe(2);
      });

      it("should not increment when loading", () => {
        store.state = LOAD_STATE.LOADING;
        store.page = 1;

        store.nextPage();

        expect(store.page).toBe(1);
      });
    });

    describe("previousPage", () => {
      it("should decrement page when greater than 1", () => {
        store.state = LOAD_STATE.SUCCESS;
        store.page = 3;

        store.previousPage();

        expect(store.page).toBe(2);
      });

      it("should not go below page 1", () => {
        store.state = LOAD_STATE.SUCCESS;
        store.page = 1;

        store.previousPage();

        expect(store.page).toBe(1);
      });
    });

    describe("goToPage", () => {
      it("should navigate to specific page", () => {
        store.state = LOAD_STATE.SUCCESS;
        store.page = 1;

        store.goToPage(5);

        expect(store.page).toBe(5);
      });

      it("should not navigate to current page", () => {
        vi.clearAllMocks();
        store.state = LOAD_STATE.SUCCESS;
        store.page = 3;

        store.goToPage(3);

        expect(RepositoryService.search).not.toHaveBeenCalled();
      });

      it("should not navigate to page less than 1", () => {
        store.state = LOAD_STATE.SUCCESS;
        store.page = 2;

        store.goToPage(0);

        expect(store.page).toBe(2);
      });
    });

    describe("resetPaging", () => {
      it("should reset page to 1", () => {
        store.page = 5;
        store.resetPaging();

        expect(store.page).toBe(1);
      });
    });
  });

  describe("search actions", () => {
    beforeEach(() => {
      store = new StoreRepository();
      vi.clearAllMocks();
    });

    describe("performSearch", () => {
      it("should reset paging and perform search", async () => {
        store.page = 5;

        await store.performSearch();

        expect(store.page).toBe(1);
        expect(RepositoryService.search).toHaveBeenCalled();
      });
    });

    describe("search", () => {
      it("should set loading state and call service", async () => {
        const mockResponse = {
          items: [{ id: 1 }],
          pagination: {
            page: 1,
            per_page: 25,
            total: 1,
            has_next: false,
            has_previous: false,
          },
        };
        vi.mocked(RepositoryService.search).mockResolvedValue(
          mockResponse as any,
        );

        await store.search();

        expect(store.state).toBe(LOAD_STATE.SUCCESS);
        expect(store.repos).toEqual([{ id: 1 }]);
        expect(store.paginationMeta).toEqual(mockResponse.pagination);
      });

      it("should handle search errors", async () => {
        vi.mocked(RepositoryService.search).mockRejectedValue(
          new Error("Network error"),
        );

        await store.search();

        expect(store.state).toBe(LOAD_STATE.ERROR);
        expect(store.errorMessage).toBe("Network error");
        expect(store.repos).toEqual([]);
        expect(store.isRateLimitError).toBe(false);
      });

      it("should detect and handle rate limit errors (503)", async () => {
        vi.mocked(RepositoryService.search).mockRejectedValue(
          new ApiError("Service unavailable", 503, null),
        );

        await store.search();

        expect(store.state).toBe(LOAD_STATE.ERROR);
        expect(store.errorMessage).toBe("GitHub API rate limit reached. Please wait a few minutes before trying again.");
        expect(store.isRateLimitError).toBe(true);
        expect(store.repos).toEqual([]);
      });

      it("should handle ApiError with non-503 status", async () => {
        vi.mocked(RepositoryService.search).mockRejectedValue(
          new ApiError("Bad request", 400, null),
        );

        await store.search();

        expect(store.state).toBe(LOAD_STATE.ERROR);
        expect(store.errorMessage).toBe("Bad request");
        expect(store.isRateLimitError).toBe(false);
        expect(store.repos).toEqual([]);
      });

      it("should prevent duplicate simultaneous requests", async () => {
        vi.clearAllMocks();
        const mockResponse = {
          items: [],
          pagination: {
            page: 1,
            per_page: 25,
            total: 0,
            has_next: false,
            has_previous: false,
          },
        };

        // Make search slow
        vi.mocked(RepositoryService.search).mockImplementation(
          () =>
            new Promise((resolve) =>
              setTimeout(() => resolve(mockResponse as any), 100),
            ),
        );

        const promise1 = store.search();
        const promise2 = store.search();

        // Both should resolve
        await Promise.all([promise1, promise2]);

        // Service should only be called once due to deduplication
        expect(RepositoryService.search).toHaveBeenCalledTimes(1);
      });

      it("should pass correct parameters to service", async () => {
        store.selectedLanguages = ["TypeScript"];
        store.createdAfter = "2024-01-01";
        store.page = 2;

        await store.search();

        expect(RepositoryService.search).toHaveBeenCalledWith({
          languages: ["TypeScript"],
          createdAfter: "2024-01-01",
          page: 2,
          perPage: 25,
        });
      });
    });

    describe("onSubmitSearch", () => {
      it("should reset page to 1 and trigger search", async () => {
        vi.clearAllMocks();
        store.page = 5;

        store.onSubmitSearch();

        // Wait for the async operation
        await vi.waitFor(() => {
          expect(store.page).toBe(1);
        });

        // Should have called search
        expect(RepositoryService.search).toHaveBeenCalled();
      });
    });
  });

  describe("error handling", () => {
    beforeEach(() => {
      store = new StoreRepository();
    });

    describe("clearError", () => {
      it("should clear error message and rate limit flag", () => {
        store.errorMessage = "Some error";
        store.isRateLimitError = true;
        store.clearError();

        expect(store.errorMessage).toBeNull();
        expect(store.isRateLimitError).toBe(false);
      });

      it("should reset state from ERROR to IDLE", () => {
        store.state = LOAD_STATE.ERROR;
        store.errorMessage = "Some error";

        store.clearError();

        expect(store.state).toBe(LOAD_STATE.IDLE);
      });

      it("should not change state if not in ERROR state", () => {
        store.state = LOAD_STATE.SUCCESS;
        store.clearError();

        expect(store.state).toBe(LOAD_STATE.SUCCESS);
      });
    });
  });
});
