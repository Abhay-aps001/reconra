import assert from "node:assert/strict";
import { test } from "node:test";

import { formatINRFromPaise } from "../lib/format/currency";

for (const [paise, expected] of [
  [528419000, "₹52,84,190.00"],
  [0, "₹0.00"],
  [-0, "₹0.00"],
  [1, "₹0.01"],
  [99, "₹0.99"],
  [100, "₹1.00"],
  [100001, "₹1,000.01"],
  [10000000, "₹1,00,000.00"],
  [-528419099, "-₹52,84,190.99"],
  [-1, "-₹0.01"],
  [Number.MAX_SAFE_INTEGER, "₹9,00,71,99,25,47,409.91"],
  [Number.MIN_SAFE_INTEGER, "-₹9,00,71,99,25,47,409.91"],
] as const) {
  test(`formats integer paise ${paise} as ${expected}`, () => {
    assert.equal(formatINRFromPaise(paise), expected);
  });
}

for (const value of [0.5, -1.5, NaN, Infinity, -Infinity, Number.MAX_SAFE_INTEGER + 1]) {
  test(`rejects invalid or imprecise paise: ${value}`, () => {
    assert.throws(() => formatINRFromPaise(value), RangeError);
  });
}
