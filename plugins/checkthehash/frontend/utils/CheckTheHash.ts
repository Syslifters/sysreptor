import type { Ref, UnwrapRef } from "vue";

export default function checkHash(hash: string, prototypes: any[]): string[] {
  let returnData: string[] = [];
  prototypes.forEach(hashType => {
    let regex = new RegExp(hashType.regex.source, hashType.regex.options);
    let match = regex.test(hash);
    if (match) {
      hashType.modes.map((m: any) => m.name).forEach((possibleHash: string) => {
        returnData.push(possibleHash)
      });
    } else {
    }

  });
  return  returnData;
}

