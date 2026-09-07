import { requestJson } from "../../lib/api/client";
import { parseRun, type RunResult } from "../reconciliation/types";

export const razorpayApi = { sync: async (): Promise<RunResult> => parseRun(await requestJson("/razorpay/sync")) };
