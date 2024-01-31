import setWith from "lodash/setWith";
import clone from "lodash/clone";

/**
 * Immutable version of lodash.set
 */
export function setNested(obj: any, path: string|string[], value: any) {
  return setWith(clone(obj), path, value, clone);
}
