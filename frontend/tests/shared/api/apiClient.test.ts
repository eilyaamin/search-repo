import { describe, it, expect, vi, beforeEach } from "vitest";
import { ApiClient, ApiError } from "../../../src/shared/api/apiClient";

describe("ApiClient", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  describe("ApiError", () => {
    it("should create ApiError with message, status, and body", () => {
      const error = new ApiError("Not found", 404, {
        detail: "Resource not found",
      });

      expect(error.message).toBe("Not found");
      expect(error.status).toBe(404);
      expect(error.body).toEqual({ detail: "Resource not found" });
      expect(error.name).toBe("ApiError");
    });
  });

  describe("request", () => {
    it("should make GET request with query parameters", async () => {
      const mockResponse = { data: "test" };
      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => mockResponse,
      } as Response);

      const result = await ApiClient.request("GET", "/api/test", {
        query: { page: 1, limit: 10 },
      });

      expect(global.fetch).toHaveBeenCalledWith(
        "/api/test?page=1&limit=10",
        expect.objectContaining({
          method: "GET",
          headers: expect.objectContaining({
            Accept: "application/json",
          }),
        }),
      );
      expect(result).toEqual(mockResponse);
    });

    it("should make POST request with JSON body", async () => {
      const mockResponse = { success: true };
      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => mockResponse,
      } as Response);

      const body = { name: "test", value: 123 };
      const result = await ApiClient.request("POST", "/api/test", { body });

      expect(global.fetch).toHaveBeenCalledWith(
        "/api/test",
        expect.objectContaining({
          method: "POST",
          headers: expect.objectContaining({
            Accept: "application/json",
            "Content-Type": "application/json",
          }),
          body: JSON.stringify(body),
        }),
      );
      expect(result).toEqual(mockResponse);
    });

    it("should handle non-JSON responses", async () => {
      const textResponse = "Plain text response";
      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        headers: new Headers({ "content-type": "text/plain" }),
        text: async () => textResponse,
        json: async () => {
          throw new Error("Not JSON");
        },
      } as any);

      const result = await ApiClient.request("GET", "/api/test");

      expect(result).toBe(textResponse);
    });

    it("should throw ApiError on non-ok response", async () => {
      const errorBody = { error: "Bad request" };
      vi.mocked(global.fetch).mockResolvedValue({
        ok: false,
        status: 400,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => errorBody,
      } as Response);

      await expect(ApiClient.request("GET", "/api/test")).rejects.toThrow(
        ApiError,
      );

      try {
        await ApiClient.request("GET", "/api/test");
      } catch (e) {
        expect(e).toBeInstanceOf(ApiError);
        if (e instanceof ApiError) {
          expect(e.status).toBe(400);
          expect(e.message).toBe("Bad request");
          expect(e.body).toEqual(errorBody);
        }
      }
    });

    it("should skip query parameters with undefined values", async () => {
      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({}),
      } as Response);

      await ApiClient.request("GET", "/api/test", {
        query: { page: 1, filter: undefined, search: null },
      });

      const callUrl = vi.mocked(global.fetch).mock.calls[0][0];
      expect(callUrl).not.toContain("filter");
      expect(callUrl).not.toContain("search");
      expect(callUrl).toContain("page=1");
    });
  });

  describe("getJson", () => {
    it("should make GET request and parse JSON", async () => {
      const mockData = { items: [1, 2, 3] };
      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => mockData,
      } as Response);

      const result = await ApiClient.getJson("/api/items");

      expect(result).toEqual(mockData);
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/items",
        expect.objectContaining({ method: "GET" }),
      );
    });
  });

  describe("postJson", () => {
    it("should make POST request with JSON body", async () => {
      const mockResponse = { id: 123 };
      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => mockResponse,
      } as Response);

      const data = { name: "test" };
      const result = await ApiClient.postJson("/api/create", data);

      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/create",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify(data),
        }),
      );
    });
  });
});
