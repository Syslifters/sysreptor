export default class HashInfo {
    john: string | null;
    hashcat: number | null;
    extended: boolean;
    name: string;
  
    constructor(
      john: string | null,
      hashcat: number | null,
      extended: boolean,
      name: string,
    ) {
      this.john = john;
      this.hashcat = hashcat;
      this.extended = extended;
      this.name = name;
    }
  }