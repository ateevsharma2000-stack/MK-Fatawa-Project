"use client";

import type { SearchResult } from "@/lib/types";
import ResultCard from "./ResultCard";

interface SearchResultsProps {
  results: SearchResult[];
  isLoading: boolean;
  hasSearched: boolean;
}

export default function SearchResults({ results, isLoading, hasSearched }: SearchResultsProps) {
  if (isLoading) {
    return (
      <div className="w-full max-w-2xl mx-auto mt-8 space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white border border-gray-200 rounded-lg p-5 animate-pulse">
            <div className="flex gap-2 mb-3">
              <div className="h-5 w-16 bg-gray-200 rounded-full" />
              <div className="h-5 w-24 bg-gray-200 rounded-full" />
            </div>
            <div className="space-y-2">
              <div className="h-4 bg-gray-200 rounded w-full" />
              <div className="h-4 bg-gray-200 rounded w-4/5" />
              <div className="h-4 bg-gray-200 rounded w-3/5" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (hasSearched && results.length === 0) {
    return (
      <div className="w-full max-w-2xl mx-auto mt-8 text-center">
        <p className="text-gray-500">No results found. Try a different query.</p>
      </div>
    );
  }

  if (results.length === 0) return null;

  return (
    <div className="w-full max-w-2xl mx-auto mt-8 space-y-4">
      <p className="text-sm text-gray-500">{results.length} results found</p>
      {results.map((result, idx) => (
        <ResultCard key={result.id} result={result} rank={idx + 1} />
      ))}
    </div>
  );
}
