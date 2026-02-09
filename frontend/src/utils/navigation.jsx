// NextJS Requirement
export const isWindowAvailable = () => typeof window !== 'undefined';

export const findCurrentRoute = (routes, pathname) => {
  for (let route of routes) {
    if (route.items) {
      const found = findCurrentRoute(route.items, pathname);
      if (found) return found;
    }
    if (pathname?.match(route.path) && route) {
      return route;
    }
  }
};

export const getActiveRoute = (routes, pathname) => {
  const route = findCurrentRoute(routes, pathname);
  return route?.name || 'All Templates';
};

export const getActiveNavbar = (routes, pathname) => {
  const route = findCurrentRoute(routes, pathname);
  if (route?.secondary) return route?.secondary;
  else return false;
};

export const getActiveNavbarText = (routes, pathname) => {
  return getActiveRoute(routes, pathname) || false;
};
