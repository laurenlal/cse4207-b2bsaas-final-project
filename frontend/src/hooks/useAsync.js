import { useEffect, useState } from "react";

// Calls fetcher(arg, signal) whenever `arg` changes. Returns
// { status: "loading" | "error" | "ready", data, error }.
// `fetcher` must be a stable (module-level) function.
export function useAsync(fetcher, arg) {
  const [result, setResult] = useState({
    arg: undefined,
    data: null,
    error: null,
  });

  useEffect(() => {
    const controller = new AbortController();

    fetcher(arg, controller.signal).then(
      (data) => setResult({ arg, data, error: null }),
      (error) => {
        if (error.name !== "AbortError") setResult({ arg, data: null, error });
      },
    );

    return () => controller.abort();
  }, [fetcher, arg]);

  if (result.arg !== arg) return { status: "loading", data: null, error: null };
  if (result.error) return { status: "error", data: null, error: result.error };
  return { status: "ready", data: result.data, error: null };
}
