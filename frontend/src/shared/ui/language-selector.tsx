import { useState, useEffect, useRef } from "react";
import { X, Search } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import { Badge } from "./badge";
import { Input } from "./input";
import { Label } from "./label";

interface LanguageSelectorProps {
  selectedLanguages: string[];
  onAdd: (language: string) => void;
  onRemove: (language: string) => void;
  onClear: () => void;
  onInputChange: (value: string) => void;
  inputValue: string;
  onFetchSuggestions: (query: string) => Promise<string[]>;
}

export function LanguageSelector({
  selectedLanguages,
  onAdd,
  onRemove,
  onClear,
  onInputChange,
  inputValue,
  onFetchSuggestions,
}: LanguageSelectorProps) {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchSuggestions = async () => {
      if (inputValue.trim()) {
        try {
          const results = await onFetchSuggestions(inputValue);
          setSuggestions(
            results.filter((lang) => !selectedLanguages.includes(lang)),
          );
          setShowDropdown(true);
          setHighlightedIndex(-1);
        } catch (error) {
          console.error("Failed to fetch suggestions:", error);
          setSuggestions([]);
        }
      } else {
        setSuggestions([]);
        setShowDropdown(false);
      }
    };

    const timer = setTimeout(fetchSuggestions, 200);
    return () => clearTimeout(timer);
  }, [inputValue, selectedLanguages, onFetchSuggestions]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setShowDropdown(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      if (highlightedIndex >= 0 && highlightedIndex < suggestions.length) {
        onAdd(suggestions[highlightedIndex]);
      } else if (inputValue.trim()) {
        onAdd(inputValue.trim());
      }
      setShowDropdown(false);
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlightedIndex((prev) => Math.min(prev + 1, suggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlightedIndex((prev) => Math.max(prev - 1, -1));
    } else if (e.key === "Escape") {
      setShowDropdown(false);
    }
  };

  const handleSuggestionClick = (language: string) => {
    onAdd(language);
    setShowDropdown(false);
    inputRef.current?.focus();
  };

  return (
    <div className="grid gap-2">
      <Label htmlFor="languages">Programming Languages</Label>

      {/* Input with Autocomplete */}
      <div className="relative" ref={containerRef}>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            ref={inputRef}
            id="languages"
            placeholder="Type to search languages (e.g., Python, JavaScript)..."
            value={inputValue}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => inputValue && setShowDropdown(true)}
            className="pl-10"
          />
        </div>

        {/* Suggestions Dropdown */}
        {showDropdown && suggestions.length > 0 && (
          <div className="absolute z-50 w-full mt-1 bg-card border border-border rounded-md shadow-lg max-h-60 overflow-auto">
            {suggestions.map((language, index) => (
              <button
                key={language}
                onClick={() => handleSuggestionClick(language)}
                className={cn(
                  "w-full text-left px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground transition-colors cursor-pointer",
                  highlightedIndex === index &&
                    "bg-accent text-accent-foreground",
                )}
              >
                {language}
              </button>
            ))}
          </div>
        )}
      </div>

      <p className="text-xs text-muted-foreground">
        Type to search, press{" "}
        <kbd className="px-1.5 py-0.5 text-xs rounded border bg-muted">
          Enter
        </kbd>{" "}
        to add. Selected: {selectedLanguages.length}
      </p>

      {/* Selected Languages */}
      {selectedLanguages.length > 0 && (
        <div className="flex flex-wrap gap-2 p-2 border rounded-md bg-muted/30">
          {selectedLanguages.map((lang) => (
            <Badge key={lang} variant="secondary" className="gap-1">
              {lang}
              <button
                onClick={() => onRemove(lang)}
                className="ml-1 rounded-full hover:bg-background/80"
                aria-label={`Remove ${lang}`}
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
          <button
            onClick={onClear}
            className="text-xs text-muted-foreground hover:text-foreground underline"
          >
            Clear all
          </button>
        </div>
      )}
    </div>
  );
}
