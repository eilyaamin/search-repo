import { ApiClient } from "@/shared/api/apiClient";
import type { RepoSearchParams, RepoSearchResponse } from "../types";

/**
 * Handles repository-related API operations and business logic.
 */
export class RepositoryService {
  /**
   * Search GitHub repositories using filters and pagination.
   */
  static async search(params: RepoSearchParams): Promise<RepoSearchResponse> {
    const body = {
      languages:
        params.languages && params.languages.length > 0
          ? params.languages
          : undefined,
      created_after: params.createdAfter?.trim() || undefined,
      page: params.page ?? 1,
      per_page: params.perPage ?? 25,
    };

    return ApiClient.postJson<RepoSearchResponse>("/api/repositories", body);
  }

  /**
   * Get language suggestions for autocomplete.
   */
  static async getLanguageSuggestions(query: string = ""): Promise<string[]> {
    return ApiClient.getJson<string[]>("/api/languages", { q: query });
  }

  /**
   * Sort topics by relevance:
   * 1. Selected languages
   * 2. Primary language
   * 3. Alphabetically
   */
  static getSortedTopics(
    topics: string[],
    primaryLanguage: string | null,
    selectedLanguages: string[],
    maxTopics: number = 3,
  ): string[] {
    if (!topics || topics.length === 0) {
      return primaryLanguage ? [primaryLanguage] : [];
    }

    const selectedLangsLower = selectedLanguages.map((l) => l.toLowerCase());
    const primaryLangLower = primaryLanguage?.toLowerCase();

    const sorted = [...topics].sort((a, b) => {
      const aLower = a.toLowerCase();
      const bLower = b.toLowerCase();

      // 1. Selected languages
      const aIsSelected = selectedLangsLower.includes(aLower);
      const bIsSelected = selectedLangsLower.includes(bLower);
      if (aIsSelected && !bIsSelected) return -1;
      if (!aIsSelected && bIsSelected) return 1;

      // 2. Primary language
      if (primaryLangLower) {
        const aIsPrimary = aLower === primaryLangLower;
        const bIsPrimary = bLower === primaryLangLower;
        if (aIsPrimary && !bIsPrimary) return -1;
        if (!aIsPrimary && bIsPrimary) return 1;
      }

      // 3. Alphabetical
      return a.localeCompare(b);
    });

    return sorted.slice(0, maxTopics);
  }
}
