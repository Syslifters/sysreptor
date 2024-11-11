import HashInfo from "~~/domain/hashinfo";

export default function checkHash(hash: string, prototypes: any[]): HashInfo[] {
  let returnData: HashInfo[] = [];
  prototypes.forEach(hashType => {
    let regex = new RegExp(hashType.regex.source, hashType.regex.options);
    let match = regex.test(hash);
    if (match) {
      returnData.push(...hashType.modes.map((m: any) => new HashInfo(m.john, m.hashcat, m.extended, m.name)))
    } else {
    }

  });
  return returnData;
}

