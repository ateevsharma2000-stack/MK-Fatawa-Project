"use client";

import { useState } from "react";
import type { SearchResult } from "@/lib/types";
import { COLLECTION_LABELS, COLLECTION_COLORS } from "@/lib/types";

interface ResultCardProps {
  result: SearchResult;
  rank: number;
}

export default function ResultCard({ result, rank }: ResultCardProps) {
  const [expanded, setExpanded] = useState(false);
  const similarity = Math.round(result.similarity * 100);
  const label = COLLECTION_LABELS[result.collection] || result.collection;
  const colorClass = COLLECTION_COLORS[result.collection] || "bg-gray-100 text-gray-800";

  const previewLength = 300;
  const isLong = result.content.length > previewLength;
  const displayText = expanded ? result.content : result.content.slice(0, previewLength);

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-gray-400">#{rank}</span>
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${colorClass}`}>
            {label}
          </span>
          <span className="text-xs text-gray-500">
            Vol. {result.volume}
            {result.page_no_start > 0 && (
              <>, Pages {result.page_no_start}
                {result.page_no_end > result.page_no_start && `-${result.page_no_end}`}
              </>
            )}
          </span>
        </div>
        <span className="text-sm font-semibold text-emerald-600 whitespace-nowrap">
          {similarity}% match
        </span>
      </div>

      {result.section_title && (
        <h3 className="text-sm font-semibold text-gray-800 mb-2">
          {result.section_title}
        </h3>
      )}

      <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">
        {displayText}
        {isLong && !expanded && "..."}
      </p>

      {isLong && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 text-xs text-emerald-600 hover:text-emerald-700 font-medium"
        >
          {expanded ? "Show less" : "Show more"}
        </button>
      )}
    </div>
  );
}
