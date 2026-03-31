import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";
import { embedQuery } from "@/lib/openai";
import type { SearchResult } from "@/lib/types";

function keywordScore(content: string, query: string): number {
  const words = query.toLowerCase().split(/\s+/).filter((w) => w.length > 2);
  if (words.length === 0) return 0;
  const lower = content.toLowerCase();
  const matched = words.filter((w) => lower.includes(w)).length;
  return matched / words.length;
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { query, limit = 10, collection } = body;

    if (!query || typeof query !== "string" || query.trim().length < 3) {
      return NextResponse.json(
        { error: "Query must be at least 3 characters" },
        { status: 400 }
      );
    }

    const trimmed = query.trim();
    const embedding = await embedQuery(trimmed);

    // Fetch more candidates than needed, then re-rank
    const { data, error } = await getSupabase().rpc("match_fatawa", {
      query_embedding: embedding,
      match_threshold: 0.4,
      match_count: Math.min(limit * 3, 30),
      filter_collection: collection || null,
    });

    if (error) {
      console.error("Supabase error:", error);
      return NextResponse.json(
        { error: "Search failed" },
        { status: 500 }
      );
    }

    // Re-rank: blend semantic similarity (70%) with keyword overlap (30%)
    const reranked = (data || [])
      .map((r: SearchResult) => ({
        ...r,
        similarity:
          r.similarity * 0.7 + keywordScore(r.content, trimmed) * 0.3,
      }))
      .sort((a: SearchResult, b: SearchResult) => b.similarity - a.similarity)
      .slice(0, limit);

    return NextResponse.json({ results: reranked });
  } catch (err) {
    console.error("Search error:", err);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
