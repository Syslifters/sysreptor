export type CvssMetricDefinition = {
  id: string;
  name: string;
  description: string;
  choices: {
    id: string;
    name: string;
    description: string;
  }[];
};

export type CvssDefinition = Record<string, CvssMetricDefinition>;
export type CvssMetricsValue = Record<string, number|null|any>;
export type CvssMetricsValueCollection = Record<string, CvssMetricsValue>;

export enum CvssVersion {
  CVSS30 = 'CVSS:3.0',
  CVSS31 = 'CVSS:3.1',
  CVSS40 = 'CVSS:4.0',
};

export type ParsedCvssVector = {
  version: CvssVersion|null;
  metrics: CvssMetricsValue;
};
