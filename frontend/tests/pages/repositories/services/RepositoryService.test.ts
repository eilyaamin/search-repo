import { describe, it, expect, vi, beforeEach } from "vitest";
import { RepositoryService } from "../../../../src/pages/repositories/services/RepositoryService";
import { ApiClient } from "../../../../src/shared/api/apiClient";

// Mock the ApiClient
vi.mock("@/shared/api/apiClient", () => ({
  ApiClient: {
    postJson: vi.fn(),
    getJson: vi.fn(),
  },
}));

describe("RepositoryService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("search", () => {
    it("should call ApiClient.postJson with correct endpoint and body", async () => {
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

      vi.mocked(ApiClient.postJson).mockResolvedValue(mockResponse);

      const params = {
        languages: ["TypeScript", "JavaScript"],
        createdAfter: "2024-01-01",
        page: 1,
        perPage: 25,
      };

      const result = await RepositoryService.search(params);

      expect(ApiClient.postJson).toHaveBeenCalledWith("/api/repositories", {
        languages: ["TypeScript", "JavaScript"],
        created_after: "2024-01-01",
        page: 1,
        per_page: 25,
      });
      expect(result).toEqual(mockResponse);
    });

    it("should omit empty languages array from request body", async () => {
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

      vi.mocked(ApiClient.postJson).mockResolvedValue(mockResponse);

      await RepositoryService.search({
        languages: [],
        createdAfter: "",
        page: 1,
        perPage: 25,
      });

      expect(ApiClient.postJson).toHaveBeenCalledWith("/api/repositories", {
        languages: undefined,
        created_after: undefined,
        page: 1,
        per_page: 25,
      });
    });

    it("should trim createdAfter date string", async () => {
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

      vi.mocked(ApiClient.postJson).mockResolvedValue(mockResponse);

      await RepositoryService.search({
        languages: [],
        createdAfter: "  2024-01-01  ",
        page: 1,
        perPage: 25,
      });

      expect(ApiClient.postJson).toHaveBeenCalledWith("/api/repositories", {
        languages: undefined,
        created_after: "2024-01-01",
        page: 1,
        per_page: 25,
      });
    });

    it("should use default values for page and perPage when not provided", async () => {
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

      vi.mocked(ApiClient.postJson).mockResolvedValue(mockResponse);

      await RepositoryService.search({
        languages: [],
        createdAfter: "",
      });

      expect(ApiClient.postJson).toHaveBeenCalledWith("/api/repositories", {
        languages: undefined,
        created_after: undefined,
        page: 1,
        per_page: 25,
      });
    });
  });

  describe("getLanguageSuggestions", () => {
    it("should call ApiClient.getJson with correct endpoint and query", async () => {
      const mockLanguages = ["JavaScript", "Java", "Python"];
      vi.mocked(ApiClient.getJson).mockResolvedValue(mockLanguages);

      const result = await RepositoryService.getLanguageSuggestions("java");

      expect(ApiClient.getJson).toHaveBeenCalledWith("/api/languages", {
        q: "java",
      });
      expect(result).toEqual(mockLanguages);
    });

    it("should handle empty query string", async () => {
      const mockLanguages = ["JavaScript", "TypeScript", "Python"];
      vi.mocked(ApiClient.getJson).mockResolvedValue(mockLanguages);

      const result = await RepositoryService.getLanguageSuggestions("");

      expect(ApiClient.getJson).toHaveBeenCalledWith("/api/languages", {
        q: "",
      });
      expect(result).toEqual(mockLanguages);
    });

    it("should use empty string as default query parameter", async () => {
      const mockLanguages = ["JavaScript", "TypeScript", "Python"];
      vi.mocked(ApiClient.getJson).mockResolvedValue(mockLanguages);

      const result = await RepositoryService.getLanguageSuggestions();

      expect(ApiClient.getJson).toHaveBeenCalledWith("/api/languages", {
        q: "",
      });
      expect(result).toEqual(mockLanguages);
    });
  });

  describe("getSortedTopics", () => {
    describe("edge cases", () => {
      it("should return empty array when topics is empty and no primary language", () => {
        const result = RepositoryService.getSortedTopics([], null, []);
        expect(result).toEqual([]);
      });

      it("should return primary language when topics is empty but primary language exists", () => {
        const result = RepositoryService.getSortedTopics([], "JavaScript", []);
        expect(result).toEqual(["JavaScript"]);
      });

      it("should handle null topics array", () => {
        const result = RepositoryService.getSortedTopics(
          null as any,
          "Python",
          [],
        );
        expect(result).toEqual(["Python"]);
      });
    });

    describe("sorting priority", () => {
      it("should prioritize selected languages first", () => {
        const topics = ["react", "typescript", "nodejs", "express"];
        const selectedLanguages = ["TypeScript"];

        const result = RepositoryService.getSortedTopics(
          topics,
          "JavaScript",
          selectedLanguages,
          3,
        );

        expect(result[0]).toBe("typescript");
      });

      it("should prioritize primary language second (case-insensitive)", () => {
        const topics = ["react", "javascript", "nodejs", "express"];
        const selectedLanguages: string[] = [];

        const result = RepositoryService.getSortedTopics(
          topics,
          "JavaScript",
          selectedLanguages,
          3,
        );

        expect(result[0]).toBe("javascript");
      });

      it("should sort alphabetically when no priority matches", () => {
        const topics = ["webpack", "babel", "eslint"];
        const selectedLanguages: string[] = [];

        const result = RepositoryService.getSortedTopics(
          topics,
          null,
          selectedLanguages,
          3,
        );

        expect(result).toEqual(["babel", "eslint", "webpack"]);
      });

      it("should combine all three sorting rules correctly", () => {
        const topics = [
          "webpack", // alphabetically 3rd
          "python", // selected language (1st priority)
          "javascript", // primary language (2nd priority)
          "babel", // alphabetically 1st
          "react", // alphabetically 2nd
        ];
        const selectedLanguages = ["Python"];

        const result = RepositoryService.getSortedTopics(
          topics,
          "JavaScript",
          selectedLanguages,
          5,
        );

        expect(result).toEqual([
          "python", // selected language
          "javascript", // primary language
          "babel", // alphabetical
          "react", // alphabetical
          "webpack", // alphabetical
        ]);
      });
    });

    describe("case sensitivity", () => {
      it("should match selected languages case-insensitively", () => {
        const topics = ["TYPESCRIPT", "react", "nodejs"];
        const selectedLanguages = ["typescript"];

        const result = RepositoryService.getSortedTopics(
          topics,
          null,
          selectedLanguages,
          3,
        );

        expect(result[0]).toBe("TYPESCRIPT");
      });

      it("should match primary language case-insensitively", () => {
        const topics = ["react", "JAVASCRIPT", "nodejs"];
        const selectedLanguages: string[] = [];

        const result = RepositoryService.getSortedTopics(
          topics,
          "javascript",
          selectedLanguages,
          3,
        );

        expect(result[0]).toBe("JAVASCRIPT");
      });

      it("should preserve original casing in results", () => {
        const topics = ["React", "TypeScript", "NodeJS"];
        const selectedLanguages: string[] = [];

        const result = RepositoryService.getSortedTopics(
          topics,
          null,
          selectedLanguages,
          3,
        );

        expect(result).toEqual(["NodeJS", "React", "TypeScript"]);
      });
    });

    describe("maxTopics parameter", () => {
      it("should limit results to 3 topics by default", () => {
        const topics = ["a", "b", "c", "d", "e", "f"];
        const result = RepositoryService.getSortedTopics(topics, null, []);

        expect(result).toHaveLength(3);
      });

      it("should respect custom maxTopics parameter", () => {
        const topics = ["a", "b", "c", "d", "e", "f"];
        const result = RepositoryService.getSortedTopics(topics, null, [], 5);

        expect(result).toHaveLength(5);
      });

      it("should return all topics if maxTopics exceeds topics length", () => {
        const topics = ["a", "b", "c"];
        const result = RepositoryService.getSortedTopics(topics, null, [], 10);

        expect(result).toHaveLength(3);
      });

      it("should return 1 topic when maxTopics is 1", () => {
        const topics = ["a", "b", "c"];
        const result = RepositoryService.getSortedTopics(topics, null, [], 1);

        expect(result).toEqual(["a"]);
      });
    });

    describe("multiple selected languages", () => {
      it("should prioritize all selected languages before others", () => {
        const topics = ["react", "typescript", "python", "javascript", "vue"];
        const selectedLanguages = ["TypeScript", "Python"];

        const result = RepositoryService.getSortedTopics(
          topics,
          null,
          selectedLanguages,
          5,
        );

        expect(result[0]).toBe("python");
        expect(result[1]).toBe("typescript");
        expect(["javascript", "react", "vue"]).toContain(result[2]);
      });

      it("should sort selected languages alphabetically among themselves", () => {
        const topics = ["vue", "typescript", "python", "react"];
        const selectedLanguages = ["Python", "TypeScript", "Vue"];

        const result = RepositoryService.getSortedTopics(
          topics,
          null,
          selectedLanguages,
          4,
        );

        expect(result).toEqual(["python", "typescript", "vue", "react"]);
      });
    });

    describe("real-world scenarios", () => {
      it("should correctly sort a typical repository topic list", () => {
        const topics = [
          "hacktoberfest",
          "api",
          "education",
          "javascript",
          "typescript",
          "books",
        ];
        const selectedLanguages = ["TypeScript"];
        const primaryLanguage = "JavaScript";

        const result = RepositoryService.getSortedTopics(
          topics,
          primaryLanguage,
          selectedLanguages,
          3,
        );

        expect(result).toEqual([
          "typescript", // selected language
          "javascript", // primary language
          "api", // alphabetically first of remaining
        ]);
      });

      it("should handle repository with no matching languages", () => {
        const topics = ["webpack", "babel", "eslint", "prettier"];
        const selectedLanguages = ["Python", "Ruby"];
        const primaryLanguage = "Go";

        const result = RepositoryService.getSortedTopics(
          topics,
          primaryLanguage,
          selectedLanguages,
          3,
        );

        // All sorted alphabetically since none match
        expect(result).toEqual(["babel", "eslint", "prettier"]);
      });
    });
  });
});
