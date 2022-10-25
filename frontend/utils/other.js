import { sortBy } from "lodash";
import { scoreFromVector } from "./cvss";

export function sortFindings(findings) {
  return sortBy(findings, [f => -scoreFromVector(f.data ? f.data.cvss : f.cvss), f => f.data ? f.data.created : f.id]);
}
