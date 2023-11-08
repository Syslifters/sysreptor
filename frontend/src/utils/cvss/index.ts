import { CvssVersion, ParsedCvssVector } from './base';
import { calculateScoreCvss31, calculateScoreCvss30, stringifyVectorCvss31, stringifyVectorCvss30, isValidVectorCvss3, parseVectorCvss3 } from './cvss3';
import { calculateScoreCvss40, isValidVectorCvss4, stringifyVectorCvss40, parseVectorCvss4 } from './cvss4';

export function parseVector(vector?: string|null, version?: CvssVersion|null): ParsedCvssVector {
  const cvssParsers = [
    { version: CvssVersion.CVSS40, parse: parseVectorCvss4 },
    { version: CvssVersion.CVSS31, parse: parseVectorCvss3 },
    { version: CvssVersion.CVSS30, parse: parseVectorCvss3 },
  ];
  if (version) {
    return {
      version,
      metrics: cvssParsers.find(parser => parser.version === version)?.parse(vector) || {},
    };
  }

  for (const cvssParser of cvssParsers) {
    if (vector && vector.startsWith(cvssParser.version)) {
      return { version: cvssParser.version, metrics: cvssParser.parse(vector) };
    }
  }
  return {
    version: null,
    metrics: parseVectorCvss3(vector),
  };
}

export function isValidVector(vector?: string|null) {
  return isValidVectorCvss4(vector) || isValidVectorCvss3(vector);
}

export function scoreFromVector(vector?: string|null) {
  if (isValidVectorCvss4(vector)) {
    return calculateScoreCvss40(vector);
  } else if (isValidVectorCvss3(vector) && vector?.startsWith(CvssVersion.CVSS31)) {
    return calculateScoreCvss31(vector);
  } else if (isValidVectorCvss3(vector) && vector?.startsWith(CvssVersion.CVSS30)) {
    return calculateScoreCvss30(vector);
  } else {
    return null;
  }
}

export function stringifyVector(parsedVector: ParsedCvssVector) {
  if (parsedVector.version === CvssVersion.CVSS40) {
    return stringifyVectorCvss40(parsedVector.metrics);
  } else if (parsedVector.version === CvssVersion.CVSS31) {
    return stringifyVectorCvss31(parsedVector.metrics);
  } else if (parsedVector.version === CvssVersion.CVSS30) {
    return stringifyVectorCvss30(parsedVector.metrics);
  } else {
    return 'n/a';
  }
}

export function levelNumberFromScore(score?: number|null) {
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

export function levelNameFromScore(score?: number|null) {
  return ['Info', 'Low', 'Medium', 'High', 'Critical'][levelNumberFromScore(score) - 1];
}

export function levelNumberFromLevelName(levelName?: string|null) {
  return Math.max(['info', 'low', 'medium', 'high', 'critical'].indexOf(levelName?.toLowerCase() || ''), 0) + 1;
}
