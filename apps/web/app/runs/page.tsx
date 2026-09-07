"use client";
import { RunHistory } from "../../features/runs/run-history";
export default function RunsPage() { return <section className="operational"><header className="screen-heading"><div><p className="screen-eyebrow">LOCAL RUN HISTORY</p><h1>Saved runs</h1><p>Recent public reconciliation snapshots from this browser.</p></div></header><RunHistory /></section>; }
