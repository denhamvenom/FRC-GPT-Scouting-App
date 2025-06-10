import { useState, useEffect, useCallback, useRef } from 'react'

export interface AsyncState<T> {
  /** The resolved data */
  data: T | null
  /** Loading state */
  loading: boolean
  /** Error state */
  error: Error | null
  /** Whether the operation has been called */
  called: boolean
}

export interface UseAsyncOptions<T> {
  /** Execute immediately on mount */
  immediate?: boolean
  /** Callback when operation succeeds */
  onSuccess?: (data: T) => void
  /** Callback when operation fails */
  onError?: (error: Error) => void
  /** Dependencies to re-run the operation */
  deps?: React.DependencyList
  /** Whether to reset state before executing */
  resetOnExecute?: boolean
}

/**
 * Hook for managing async operations with loading states
 * 
 * @param asyncFunction - The async function to execute
 * @param options - Configuration options
 * @returns Object with state and control methods
 * 
 * @example
 * ```tsx
 * // Basic usage
 * const fetchUser = async (id: string) => {
 *   const response = await fetch(`/api/users/${id}`)
 *   return response.json()
 * }
 * 
 * const { data: user, loading, error, execute } = useAsync(fetchUser)
 * 
 * return (
 *   <div>
 *     <button onClick={() => execute('123')}>Load User</button>
 *     {loading && <p>Loading...</p>}
 *     {error && <p>Error: {error.message}</p>}
 *     {user && <p>User: {user.name}</p>}
 *   </div>
 * )
 * ```
 * 
 * @example
 * ```tsx
 * // With immediate execution and dependencies
 * const { data: posts, loading, error, refetch } = useAsync(
 *   () => fetchPosts(userId),
 *   {
 *     immediate: true,
 *     deps: [userId],
 *     onSuccess: (posts) => console.log('Loaded posts:', posts),
 *     onError: (error) => console.error('Failed to load posts:', error)
 *   }
 * )
 * 
 * return (
 *   <div>
 *     <button onClick={refetch}>Refresh</button>
 *     {loading && <LoadingSpinner />}
 *     {error && <ErrorMessage error={error} />}
 *     {posts && <PostsList posts={posts} />}
 *   </div>
 * )
 * ```
 */
export function useAsync<T, P extends any[] = []>(
  asyncFunction: (...args: P) => Promise<T>,
  options: UseAsyncOptions<T> = {}
) {
  const {
    immediate = false,
    onSuccess,
    onError,
    deps = [],
    resetOnExecute = false
  } = options

  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    loading: false,
    error: null,
    called: false
  })

  const mountedRef = useRef(true)
  const lastExecutionRef = useRef<Promise<T> | null>(null)

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false
    }
  }, [])

  const execute = useCallback(
    async (...args: P): Promise<T | undefined> => {
      // Reset state if requested
      if (resetOnExecute) {
        setState({
          data: null,
          loading: true,
          error: null,
          called: true
        })
      } else {
        setState(prev => ({
          ...prev,
          loading: true,
          error: null,
          called: true
        }))
      }

      try {
        const promise = asyncFunction(...args)
        lastExecutionRef.current = promise
        const data = await promise

        // Only update state if component is still mounted and this is the latest execution
        if (mountedRef.current && lastExecutionRef.current === promise) {
          setState(prev => ({
            ...prev,
            data,
            loading: false,
            error: null
          }))
          onSuccess?.(data)
          return data
        }
      } catch (error) {
        // Only update state if component is still mounted and this is the latest execution
        if (mountedRef.current && lastExecutionRef.current) {
          const errorObject = error instanceof Error ? error : new Error(String(error))
          setState(prev => ({
            ...prev,
            loading: false,
            error: errorObject
          }))
          onError?.(errorObject)
        }
      }
    },
    [asyncFunction, onSuccess, onError, resetOnExecute]
  )

  // Execute immediately if requested
  useEffect(() => {
    if (immediate) {
      execute()
    }
  }, [immediate, execute, ...deps])

  // Reset function
  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
      called: false
    })
    lastExecutionRef.current = null
  }, [])

  // Refetch function (only works if no parameters required)
  const refetch = useCallback(() => {
    if (state.called) {
      return execute()
    }
  }, [execute, state.called])

  return {
    ...state,
    execute,
    reset,
    refetch
  }
}

/**
 * Hook for managing async operations with manual trigger
 * 
 * @param asyncFunction - The async function to execute
 * @returns Tuple with [execute function, state]
 * 
 * @example
 * ```tsx
 * const [createUser, { loading, error, data }] = useAsyncCallback(async (userData) => {
 *   const response = await fetch('/api/users', {
 *     method: 'POST',
 *     body: JSON.stringify(userData)
 *   })
 *   return response.json()
 * })
 * 
 * const handleSubmit = async (formData) => {
 *   try {
 *     const user = await createUser(formData)
 *     console.log('User created:', user)
 *   } catch (error) {
 *     console.error('Failed to create user:', error)
 *   }
 * }
 * ```
 */
export function useAsyncCallback<T, P extends any[] = []>(
  asyncFunction: (...args: P) => Promise<T>
): [(...args: P) => Promise<T | undefined>, AsyncState<T>] {
  const { execute, ...state } = useAsync(asyncFunction, { immediate: false })
  return [execute, state]
}

/**
 * Hook for managing async data fetching with cache
 * 
 * @param key - Cache key
 * @param asyncFunction - Function to fetch data
 * @param options - Configuration options
 * @returns State and control methods with caching
 * 
 * @example
 * ```tsx
 * const { data: user, loading, error, refresh } = useAsyncData(
 *   `user-${userId}`,
 *   () => fetchUser(userId),
 *   {
 *     cacheTime: 5 * 60 * 1000, // 5 minutes
 *     staleTime: 1 * 60 * 1000,  // 1 minute
 *     deps: [userId]
 *   }
 * )
 * ```
 */
export function useAsyncData<T>(
  key: string,
  asyncFunction: () => Promise<T>,
  options: UseAsyncOptions<T> & {
    /** Cache time in milliseconds */
    cacheTime?: number
    /** Stale time in milliseconds */
    staleTime?: number
  } = {}
) {
  const { cacheTime = 5 * 60 * 1000, staleTime = 0, ...asyncOptions } = options
  
  // Simple in-memory cache (in a real app, you might use a more sophisticated cache)
  const cacheRef = useRef<Map<string, { data: T; timestamp: number }>>(new Map())
  
  const cachedAsyncFunction = useCallback(async (): Promise<T> => {
    const cache = cacheRef.current
    const cached = cache.get(key)
    const now = Date.now()
    
    // Return cached data if it's still fresh
    if (cached && (now - cached.timestamp) < staleTime) {
      return cached.data
    }
    
    // Fetch new data
    const data = await asyncFunction()
    
    // Cache the new data
    cache.set(key, { data, timestamp: now })
    
    // Clean up old cache entries
    for (const [cacheKey, cacheValue] of cache.entries()) {
      if ((now - cacheValue.timestamp) > cacheTime) {
        cache.delete(cacheKey)
      }
    }
    
    return data
  }, [key, asyncFunction, staleTime, cacheTime])
  
  const result = useAsync(cachedAsyncFunction, { immediate: true, ...asyncOptions })
  
  const refresh = useCallback(() => {
    // Clear cache for this key and refetch
    cacheRef.current.delete(key)
    return result.execute()
  }, [key, result.execute])
  
  return {
    ...result,
    refresh
  }
}

/**
 * Hook for managing multiple async operations
 * 
 * @param operations - Object with named async operations
 * @returns Object with state for each operation
 * 
 * @example
 * ```tsx
 * const { user, posts, comments } = useAsyncMultiple({
 *   user: () => fetchUser(userId),
 *   posts: () => fetchUserPosts(userId),
 *   comments: () => fetchUserComments(userId)
 * })
 * 
 * return (
 *   <div>
 *     {user.loading && <p>Loading user...</p>}
 *     {posts.loading && <p>Loading posts...</p>}
 *     {comments.loading && <p>Loading comments...</p>}
 *     
 *     {user.data && <UserProfile user={user.data} />}
 *     {posts.data && <PostsList posts={posts.data} />}
 *     {comments.data && <CommentsList comments={comments.data} />}
 *   </div>
 * )
 * ```
 */
export function useAsyncMultiple<T extends Record<string, () => Promise<any>>>(
  operations: T
): {
  [K in keyof T]: ReturnType<typeof useAsync<Awaited<ReturnType<T[K]>>>>
} {
  const results = {} as any
  
  for (const [key, operation] of Object.entries(operations)) {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    results[key] = useAsync(operation, { immediate: true })
  }
  
  return results
}

export default useAsync