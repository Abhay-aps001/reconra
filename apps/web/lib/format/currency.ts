const indianInteger = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });

/** Display integer paise without rounding or converting money to floating-point rupees. */
export function formatINRFromPaise(value: number): string {
  if (!Number.isSafeInteger(value)) {
    throw new RangeError("Currency display requires safe integer paise.");
  }

  const paise = BigInt(value);
  const magnitude = paise < BigInt(0) ? -paise : paise;
  const rupees = magnitude / BigInt(100);
  const fraction = (magnitude % BigInt(100)).toString().padStart(2, "0");
  return `${paise < BigInt(0) ? "-" : ""}₹${indianInteger.format(rupees)}.${fraction}`;
}
