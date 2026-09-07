import { RunContext } from "../features/reconciliation/run-controller";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { renderToStaticMarkup } from "react-dom/server";

import Home from "../app/page";
import { AppShell } from "../components/app-shell";
import { RupeeFlow } from "../components/rupee-flow";

const markup = () => renderToStaticMarkup(<RunContext.Provider value={{run:null,phase:"idle",error:null,health:"ready",busy:false,startDemo:async()=>{},refresh:async()=>true,decide:async()=>{},acceptRun:()=>{},openSavedSnapshot:()=>{},savedOnly:false,href:path=>path}}><AppShell><Home /></AppShell></RunContext.Provider>);

test("entry identifies Reconra and its money-trail purpose", () => {
  const html = markup();
  assert.match(html, /Reconra/);
  assert.match(html, /<h1[^>]*>Every rupee should have a trail\.<\/h1>/);
});

test("entry routes Import Data and Test Mode sync to their working workflows", () => {
  const html = markup();
  assert.match(html, /aria-label="Import Data"[^>]*href="\/import"/);
  assert.match(html, /aria-label="Sync Razorpay Test Mode"[^>]*href="\/razorpay"/);
});

test("shell has a main landmark, primary navigation, active home and skip link", () => {
  const html = markup();
  assert.match(html, /<main[^>]*id="main-content"/);
  assert.match(html, /<nav[^>]*aria-label="Primary"/);
  assert.match(html, /href="\/workspace"/);
  assert.match(html, /href="#main-content"/);
  for (const label of ["Workspace", "Ledger", "Exceptions", "Audit", "Import", "Razorpay"]) {
    assert.ok(html.includes(label));
  }
});

test("Rupee Flow combines decorative local currency artwork with original inline SVG", () => {
  const html = renderToStaticMarkup(<RupeeFlow />);
  assert.match(html, /<svg[^>]*aria-hidden="true"/);
  assert.doesNotMatch(html, /<(?:img|image)\b|(?:src|href)=|https?:\/\//);
  assert.match(html, /Illustrative money trail/);
  assert.match(html, /class="currency-architecture" aria-hidden="true"/);
  const css = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");
  assert.match(css, /url\('\/assets\/rupee-500-reference\.webp'\)/);
  assert.ok(readFileSync(new URL("../public/assets/rupee-500-reference.webp", import.meta.url)).byteLength < 1_100_000);
});

test("CSS includes a static reduced-motion treatment", () => {
  const css = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");
  assert.match(css, /@media\s*\(prefers-reduced-motion:\s*reduce\)/);
  assert.match(css, /animation:\s*none/);
  assert.match(css, /transition:\s*none/);
});
