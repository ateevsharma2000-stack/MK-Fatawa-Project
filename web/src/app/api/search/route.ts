import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";
import { embedQuery } from "@/lib/openai";
import type { SearchResult } from "@/lib/types";

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

    const embedding = await embedQuery(query.trim());

    const { data, error } = await getSupabase().rpc("match_fatawa", {
      query_embedding: embedding,
      match_threshold: 0.3,
      match_count: limit,
      filter_collection: collection || null,
    });

    if (error) {
      console.error("Supabase error:", error);
      return NextResponse.json(
        { error: "Search failed" },
        { status: 500 }
      );
    }

    const results: SearchResult[] = data || [];

    return NextResponse.json({ results });
  } catch (err) {
    console.error("Search error:", err);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
