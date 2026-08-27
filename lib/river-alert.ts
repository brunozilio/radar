export type RiverAlertDecision = "ignore" | "reset" | "trigger";

export function riverAlertDecision(
  level: number,
  alertLevel: number | null,
  isActive: boolean,
): RiverAlertDecision {
  if (
    alertLevel === null ||
    !Number.isFinite(alertLevel) ||
    !Number.isFinite(level)
  ) {
    return "ignore";
  }
  if (level < alertLevel) return isActive ? "reset" : "ignore";
  return isActive ? "ignore" : "trigger";
}
