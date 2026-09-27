import { useInfiniteQuery, useQuery, useQueryClient } from '@tanstack/react-query';
import { request } from './client';
import type { Page } from './types';

export function useResource<T>(path: string) {
  return useQuery({ queryKey: [path], queryFn: ({ signal }) => request<T>(path, { signal }) });
}
export function useOptions<T>(path: string) {
  const query = useInfiniteQuery({
    queryKey: ['options', path],
    initialPageParam: 0,
    queryFn: ({ pageParam, signal }) =>
      request<Page<T>>(`${path}?limit=50&offset=${pageParam}`, { signal }),
    getNextPageParam: (page) =>
      page.offset + page.items.length < page.total ? page.offset + page.limit : undefined,
  });
  return { ...query, items: query.data?.pages.flatMap((page) => page.items) ?? [] };
}
export function useRefresh() {
  const cache = useQueryClient();
  return () => cache.invalidateQueries();
}
