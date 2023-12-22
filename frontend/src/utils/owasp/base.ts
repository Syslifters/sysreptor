// * Backup
// export type OwaspMetricDefinition = {
//   id: string;
//   name: string;
//   description: string;
//   choices: {
//     id: string;
//     name: string;
//     description: string;
//   }[];
// };

export type OwaspMetricDefinition = {
  id: string;
  name: string;
  choices: {
    id: string;
    name: string;
  }[];
};

export type OwaspDefinition = {
  [key: string]: OwaspMetricDefinition;
};

export type OwaspMetricsValue = {
  [key: string]: number | null | any;
};

export type OwaspMetricsValueCollection = {
  [key: string]: OwaspMetricsValue;
};
