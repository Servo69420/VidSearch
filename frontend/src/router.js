import { useState, useEffect, useCallback } from 'react'

function matchRoute(hash, pattern) {
  const path = hash.replace(/^#/, '') || '/'
  const pathParts = path.split('/').filter(Boolean)
  const patternParts = pattern.split('/').filter(Boolean)

  if (pattern === '/' && pathParts.length === 0) return {}
  if (pattern === '/' && pathParts.length > 0) return null
  if (patternParts.length !== pathParts.length) return null

  const params = {}
  for (let i = 0; i < patternParts.length; i++) {
    if (patternParts[i].startsWith(':')) {
      params[patternParts[i].slice(1)] = decodeURIComponent(pathParts[i])
    } else if (patternParts[i] !== pathParts[i]) {
      return null
    }
  }
  return params
}

export function useHashRouter(routes) {
  const [state, setState] = useState(() => resolve(routes))

  function resolve(routeTable) {
    const hash = window.location.hash || '#/'
    for (const route of routeTable) {
      const params = matchRoute(hash, route.path)
      if (params !== null) {
        return { route, params, hash }
      }
    }
    // Fallback to first route
    return { route: routeTable[0], params: {}, hash }
  }

  useEffect(() => {
    function onHashChange() {
      setState(resolve(routes))
    }
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [routes])

  const navigate = useCallback((path) => {
    window.location.hash = path
  }, [])

  return {
    current: state.route,
    params: state.params,
    navigate,
    path: (state.hash || '#/').replace(/^#/, '') || '/',
  }
}

export function navigate(path) {
  window.location.hash = path
}
