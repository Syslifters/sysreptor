import type {
  OwaspDefinition,
  OwaspMetricsValue,
  OwaspMetricsValueCollection,
} from "../owasp/base";

export const OWASP_DEFINITION: OwaspDefinition = Object.freeze({
  LF: {
    id: "LF",
    name: "Likelihood Factors",
    choices: [
      {
        id: 'I',
        name: "Info",
      },
      {
        id: 'L',
        name: "Low",
      },
      {
        id: 'M',
        name: "Medium",
      },
      {
        id: 'H',
        name: "High",
      },
    ],
  },
  IF: {
    id: "IF",
    name: "Impact Factors",
    choices: [
      {
        id: 'I',
        name: "Info",
      },
      {
        id: 'L',
        name: "Low",
      },
      {
        id: 'M',
        name: "Medium",
      },
      {
        id: 'H',
        name: "High",
      },
    ],
  },
  ORS: {
    id: "ORS",
    name: "Overall Risk Severity",
    choices: [
      {
        id: 'I',
        name: "Info",
      },
      {
        id: 'L',
        name: "Low",
      },
      {
        id: 'M',
        name: "Medium",
      },
      {
        id: 'H',
        name: "High",
      },
    ],
  },
});
const OWASP_METRICS_BASE: OwaspMetricsValueCollection = Object.freeze({
  LF: { I: 0, L: 1, M: 2, H: 3 },
  IF: { I: 0, L: 1, M: 2, H: 3 },
  ORS: { I: 0, L: 1, M: 2, H: 3 },
});
const OWASP_METRICS: OwaspMetricsValueCollection = Object.freeze(
  Object.assign({}, OWASP_METRICS_BASE)
);

export function parseVector(vector?: string | null): OwaspMetricsValue {
  // Vector to string
  const out = {} as OwaspMetricsValue;
  for (const part of (vector || "").slice(7).split("/")) {
    const kv = part.split(":");
    out[kv[0]] = kv.length > 1 ? kv[1] : null;
  }

  // Set undefined metrics
  for (const m of Object.keys(OWASP_METRICS)) {
    if (!(m in out)) {
      out[m] = "X";
    }
  }
  return out;
}
export function stringifyVector(parsedVector: OwaspMetricsValue): string {
  let out = "OWASP:";
  
  for (const [k, vs] of Object.entries(OWASP_METRICS)) {
    if (k in parsedVector && parsedVector[k] in vs && parsedVector[k] !== 'X') {
      out += `/${k}:${parsedVector[k]}`;
    }
  }
  return out;
}
export function levelNumberFromScore(score?: number | null) {
  if (score === null || score === undefined) {
    return 1;
  }

  if (score >= 9.0) {
    return 5;
  } else if (score >= 7.0) {
    return 4;
  } else if (score >= 4.0) {
    return 3;
  } else if (score > 0.0) {
    return 2;
  } else {
    return 1;
  }
}

export function levelNameFromScore(score?: number | null) {
  return ["Info", "Low", "Medium", "High", "Critical"][
    levelNumberFromScore(score) - 1
  ];
}

export function levelNumberFromLevelName(levelName?: string | null) {
  return (
    Math.max(
      ["info", "low", "medium", "high", "critical"].indexOf(
        levelName?.toLowerCase() || ""
      ),
      0
    ) + 1
  );
}
