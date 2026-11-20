"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError, apiFetch, toApiError } from "./client";

type State<T> = { data: T | null; error: ApiError | null; loading: boolean };

/** GET sederhana dengan state loading/error. Kirim `null` untuk menunda request. */
export function useApi<T>(path: string | null) {
  const [state, setState] = useState<State<T>>({
    data: null,
    error: null,
    loading: path !== null,
  });
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (path === null) return;
    let cancelled = false;
    setState((prev) => ({ ...prev, loading: true }));

    apiFetch<T>(path)
      .then((data) => {
        if (!cancelled) setState({ data, error: null, loading: false });
      })
      .catch((error: unknown) => {
        if (!cancelled) setState({ data: null, error: toApiError(error), loading: false });
      });

    return () => {
      cancelled = true;
    };
  }, [path, tick]);

  const reload = useCallback(() => setTick((value) => value + 1), []);
  return { ...state, reload };
}
