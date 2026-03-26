"use client";

import { useState } from "react";

interface SearchBarProps {
  onSearch: (query: string, collection: string) => void;
  isLoading: boolean;
}

export default function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [collection, setCollection] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (query.trim().length >= 3) {
      onSearch(query.trim(), collection);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search fatawa... (e.g. ruling on fasting while traveling)"
          className="flex-1 px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-gray-900 bg-white"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || query.trim().length < 3}
          className="px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {isLoading ? "..." : "Search"}
        </button>
      </div>
      <div className="mt-3 flex items-center gap-3">
        <label className="text-sm text-gray-500">Filter:</label>
        <select
          value={collection}
          onChange={(e) => setCollection(e.target.value)}
          className="text-sm px-3 py-1.5 rounded border border-gray-300 bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-emerald-500"
        >
          <option value="">All Collections</option>
          <option value="ibn_bazz">Majmoo&apos; al-Fatawa (Ibn Bazz)</option>
          <option value="iftaa">Permanent Committee (Iftaa)</option>
          <option value="noor_ala_darb">Noor ala al-Darb</option>
        </select>
      </div>
    </form>
  );
}
