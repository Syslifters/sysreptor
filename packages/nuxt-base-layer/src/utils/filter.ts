import type { LocationQuery } from 'vue-router';
import type { FilterProperties, FilterValue } from '@base/utils/types';

/**
 * Parse URL query parameters into filter values
 * @param query - The route query object
 * @param filterProperties - The filter properties to parse
 * @returns An array of parsed filter values
 */
export function parseFiltersFromQuery(
  query: LocationQuery, 
  filterProperties: FilterProperties[]
): FilterValue[] {
  const filtersFromUrl: FilterValue[] = [];
  
  // Process query parameters and create filter objects
  filterProperties.forEach(filterProp => {
    const filterType = filterProp.type;
    const filterId = filterProp.id || '';
    
    // Handle daterange and timerange types separately
    if (filterType === 'daterange' || filterType === 'timerange') {
      const rangeKey = filterId;
      const notRangeKey = `not_${filterId}`;
      
      // Check for both regular and excluded ranges
      [
        { key: rangeKey, isExcluded: false },
        { key: notRangeKey, isExcluded: true }
      ].forEach(({ key, isExcluded }) => {
        if (query[key]) {
          // Handle both single value and array of values
          const values = Array.isArray(query[key]) 
            ? query[key] as string[] 
            : [query[key] as string];
          
          values.forEach(value => {
            // Split the range value using the separator
            const [start, end] = String(value || '').split('|');
            
            filtersFromUrl.push({
              id: filterId,
              value: [
                String(start || ''),
                String(end || '')
              ],
              exclude: isExcluded,
              regex: false
            });
          });
        }
      });
    } else {
      // Handle other filter types (select, text, etc.)
      // Check for regular filter parameters
      if (query[filterId]) {
        // Handle both single value and array of values
        const values = Array.isArray(query[filterId]) 
          ? query[filterId] as string[] 
          : [query[filterId] as string];
        
        values.forEach(value => {
          filtersFromUrl.push({
            id: filterId,
            value: String(value || ''),
            exclude: false,
            regex: false
          });
        });
      }
      
      // Check for regex filter parameters
      if (query[`${filterId}_regex`]) {
        // Handle both single value and array of values
        const values = Array.isArray(query[`${filterId}_regex`]) 
          ? query[`${filterId}_regex`] as string[] 
          : [query[`${filterId}_regex`] as string];
        
        values.forEach(value => {
          filtersFromUrl.push({
            id: filterId,
            value: String(value || ''),
            exclude: false,
            regex: true
          });
        });
      }
      
      // Check for excluded filter parameters
      if (query[`not_${filterId}`]) {
        // Handle both single value and array of values
        const values = Array.isArray(query[`not_${filterId}`]) 
          ? query[`not_${filterId}`] as string[] 
          : [query[`not_${filterId}`] as string];
        
        values.forEach(value => {
          filtersFromUrl.push({
            id: filterId,
            value: String(value || ''),
            exclude: true,
            regex: false
          });
        });
      }
      
      // Check for excluded regex filter parameters
      if (query[`not_${filterId}_regex`]) {
        // Handle both single value and array of values
        const values = Array.isArray(query[`not_${filterId}_regex`]) 
          ? query[`not_${filterId}_regex`] as string[] 
          : [query[`not_${filterId}_regex`] as string];
        
        values.forEach(value => {
          filtersFromUrl.push({
            id: filterId,
            value: String(value || ''),
            exclude: true,
            regex: true
          });
        });
      }
    }
  });
  
  return filtersFromUrl;
}

/**
 * Convert filter values to URL query parameters
 * @param filters - The active filters to convert
 * @param filterProperties - The filter properties for type information
 * @returns Object with query parameters
 */
export function filtersToQueryParams(
  filters: FilterValue[], 
  filterProperties: FilterProperties[]
): Record<string, string | string[]> {
  // Use URLSearchParams to allow multiple parameters with the same name
  const searchParams = new URLSearchParams();

  filters.forEach((filter) => {
    const filterType = filterProperties.find(f => f.id === filter.id)?.type || 'select';
    const paramPrefix = filter.exclude ? 'not_' : '';
    const filterId = filter.id || '';
    
    // Handle daterange and timerange types
    if (filterType === 'daterange' || filterType === 'timerange') {
      if (Array.isArray(filter.value) && filter.value.length > 0) {
        // Combine start and end values using a separator
        const start = filter.value[0] || '';
        const end = filter.value[1] || '';
        
        if (start || end) {
          // Use a single parameter with pipe separator
          const rangeValue = `${start}|${end}`;
          searchParams.append(`${paramPrefix}${filterId}`, rangeValue);
        }
      }
    } else {
      // For other filter types (select, text)
      if (filter.value) {
        // Always append to handle multiple occurrences of the same filter
        const regexSuffix = filter.regex ? '_regex' : '';
        searchParams.append(`${paramPrefix}${filterId}${regexSuffix}`, String(filter.value));
      }
    }
  });

  // Convert URLSearchParams to a standard object for router.replace
  const params: Record<string, string | string[]> = {};
  for (const [key, value] of searchParams.entries()) {
    // If the parameter already exists, make it an array
    if (params[key] !== undefined) {
      if (Array.isArray(params[key])) {
        (params[key] as string[]).push(value);
      } else {
        params[key] = [params[key] as string, value];
      }
    } else {
      params[key] = value;
    }
  }

  return params;
}

/**
 * Add a filter to the active filters array, preventing duplicates
 * @param activeFilters - The reactive array of active filters
 * @param filter - The filter to add
 */
export function addFilter(activeFilters: FilterValue[], filter: FilterValue) {
  // Check if filter already exists
  const existingIndex = activeFilters.findIndex(
    (f: FilterValue) => f.id === filter.id && f.value === filter.value
  );
  
  // If it doesn't exist, add it
  if (existingIndex === -1) {
    activeFilters.push(filter);
  }
}
