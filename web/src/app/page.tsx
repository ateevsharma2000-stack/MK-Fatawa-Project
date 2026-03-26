"use client";

import { useState, useCallback } from "react";
import SearchBar from "@/components/SearchBar";
import SearchResults from "@/components/SearchResults";
import type { SearchResult } from "@/lib/types";

export default function Home() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = useCallback(async (query: string, collection: string) => {
    setIsLoading(true);
    setHasSearched(true);
    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, collection: collection || undefined, limit: 10 }),
      });
      const data = await res.json();
      setResults(data.results || []);
    } catch {
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return (
    <main className="flex-1 px-4 py-12">
      <div className="text-center mb-10">
        <h1 className="text-4xl font-bold text-gray-900 mb-3">
          Fatawa Search
        </h1>
        <p className="text-gray-500 max-w-lg mx-auto">
          Search across Majmoo&apos; al-Fatawa of Ibn Bazz, Permanent Committee
          Fatwas, and Noor ala al-Darb using semantic search.
        </p>
      </div>

      <SearchBar onSearch={handleSearch} isLoading={isLoading} />
      <SearchResults results={results} isLoading={isLoading} hasSearched={hasSearched} />

      {!hasSearched && (
        <div className="w-full max-w-2xl mx-auto mt-12 text-center">
          <p className="text-sm text-gray-400 mb-4">Try searching for:</p>
          <div className="flex flex-wrap justify-center gap-2">
            {[
              "ruling on fasting while traveling",
              "prayer times",
              "zakat on gold",
              "marriage without wali",
              "conditions of shahada",
            ].map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => handleSearch(suggestion, "")}
                className="text-sm px-3 py-1.5 rounded-full border border-gray-200 text-gray-600 hover:border-emerald-300 hover:text-emerald-700 transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}
    </main>
  );
}
