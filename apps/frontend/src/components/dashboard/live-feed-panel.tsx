"use client";

import { useEffect, useState } from "react";
import { Radio } from "lucide-react";
import { apiFetch, getTokens } from "@/lib/api";
import type { LiveFeedItem } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge, statusBadgeVariant } from "@/components/ui/badge";
import { usePageVisible } from "@/hooks/use-page-visible";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:6002";

export function LiveFeedPanel() {
  const pageVisible = usePageVisible();
  const [feed, setFeed] = useState<LiveFeedItem[]>([]);

  useEffect(() => {
    if (!pageVisible) return;
    let cancelled = false;

    const loadOnce = () =>
      apiFetch<LiveFeedItem[]>("/api/dashboard/live-feed")
        .then((data) => {
          if (!cancelled) setFeed(data);
        })
        .catch(() => null);

    loadOnce();

    const { access } = getTokens();
    let abort: AbortController | null = null;

    if (access) {
      abort = new AbortController();
      (async () => {
        try {
          const res = await fetch(`${API_URL}/api/dashboard/live-feed/stream`, {
            headers: { Authorization: `Bearer ${access}` },
            signal: abort!.signal,
          });
          const reader = res.body?.getReader();
          if (!reader) return;
          const decoder = new TextDecoder();
          let buffer = "";
          while (!cancelled) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const parts = buffer.split("\n\n");
            buffer = parts.pop() || "";
            for (const part of parts) {
              const line = part.split("\n").find((l) => l.startsWith("data: "));
              if (!line) continue;
              try {
                const parsed = JSON.parse(line.slice(6)) as LiveFeedItem[];
                if (!cancelled) setFeed(parsed);
              } catch {
                /* ignore */
              }
            }
          }
        } catch {
          /* fall back to polling */
        }
      })();
    }

    const poll = setInterval(loadOnce, 20_000);

    return () => {
      cancelled = true;
      abort?.abort();
      clearInterval(poll);
    };
  }, [pageVisible]);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75 motion-reduce:animate-none" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
          </span>
          <CardTitle>Live attendance feed</CardTitle>
        </div>
        <Radio className="h-4 w-4 text-slate-400" aria-hidden />
      </CardHeader>
      <CardContent className="max-h-72 overflow-y-auto p-0">
        {feed.length === 0 ? (
          <p className="px-6 py-8 text-center text-sm text-slate-500">Waiting for kiosk check-ins and check-outs…</p>
        ) : (
          <ul className="divide-y divide-slate-100">
            {feed.map((item) => (
              <li
                key={item.id}
                className="flex items-center justify-between gap-4 px-6 py-3 transition hover:bg-slate-50/80"
              >
                <div className="min-w-0">
                  <p className="font-medium text-slate-900">{item.employee_name}</p>
                  <p className="text-sm text-slate-500">
                    <Badge variant={statusBadgeVariant(item.event_type)} className="mr-2">
                      {item.event_type.replace(/_/g, " ")}
                    </Badge>
                    {item.kiosk_name && <>@ {item.kiosk_name}</>}
                  </p>
                </div>
                <time className="shrink-0 font-mono text-sm text-slate-400">
                  {new Date(item.timestamp).toLocaleTimeString()}
                </time>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
