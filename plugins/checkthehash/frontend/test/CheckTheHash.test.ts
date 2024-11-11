import {
  test,
  describe,
  expect
} from 'vitest';
import prototypes from '../data/converted-prototypes.json'
import checkHash from '~~/utils/CheckTheHash';

describe("checkHash function - Sample Detection Summary", () => {
  prototypes.forEach((hashType) => {
    hashType.modes.forEach((mode) => {
      if (mode.samples) {
        mode.samples.forEach((sample) => {
          test(`should detect hash type ${mode.name}`, () => {
            const result = checkHash(sample, prototypes);

            expect(result).toContain(mode.name);
          });
        });
      }
    });
  });
});