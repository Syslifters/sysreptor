

export type ParsedPentestFinding = PentestFinding & {
  template_info: {
    is_fallback: boolean;
    language: string;
    search_path: string[];
  };
}
