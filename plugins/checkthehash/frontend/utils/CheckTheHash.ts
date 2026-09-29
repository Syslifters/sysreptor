import HashInfo from "~~/domain/hashinfo";

export default function checkHash(hash: string, prototypes: any[]): HashInfo[] {
  const returnData: HashInfo[] = [];
  prototypes.forEach(hashType => {
    const regex = new RegExp(hashType.regex.source, hashType.regex.options);
    const match = regex.test(hash);
    if (match) {
      returnData.push(...hashType.modes.map((m: any) => new HashInfo(m.john, m.hashcat, m.extended, m.name)))
    }
  });
  return returnData;
}
