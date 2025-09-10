import { useState, useRef } from "react";
import { isInvisiblySmallElement } from "@excalidraw/excalidraw";
import { OrderedExcalidrawElement } from "@excalidraw/excalidraw/element/types";


export function useTheme() {
  const colorSchemeQueryList = window.matchMedia('(prefers-color-scheme: dark)');
  const [isDarkTheme, setIsDarkTheme] = useState(colorSchemeQueryList.matches);
  colorSchemeQueryList.addEventListener('change', (event) => {
    setIsDarkTheme(event.matches);
  });

  return { 
    isDarkTheme,
  }
}


export function useResolvablePromise<T>() {
  let resolve: (value: T|PromiseLike<T>) => void;
  let reject: (error: Error) => void;
  let promise = new Promise<T>((r, j) => { resolve = r; reject = j; });
  const ref = useRef({ promise, resolve: resolve!, reject: reject!, reset });

  function reset() {
    promise = new Promise<T>((r, j) => { resolve = r; reject = j; });
    ref.current = {
      promise,
      resolve: resolve!,
      reject: reject!,
      reset,
    };
  }
  return ref;
}


export function isSyncableElement(element: OrderedExcalidrawElement): boolean {
  if (element.isDeleted) {
    if (element.updated > Date.now() - 24 * 60 * 60 * 1000) {
      return true;
    }
    return false;
  }
  return !isInvisiblySmallElement(element);
}

