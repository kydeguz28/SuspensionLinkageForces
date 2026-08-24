import { chromium } from "playwright";
import path from "node:path";
import { pathToFileURL } from "node:url";

const viewer = path.resolve("../outputs/suspension_linkages_3d_current.html");
const browser = await chromium.launch({
  headless: true,
  executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
});
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(viewer).href);
await page.getByRole("tab", { name: "Member Sizing" }).click();
await page.waitForSelector("#sizingTableBody tr");
const desktop = {
  title: await page.getByRole("heading", { name: "Governing member loads" }).isVisible(),
  rows: await page.locator("#sizingTableBody tr").count(),
  fails: await page.locator("#sizingFailCount").textContent(),
  cautions: await page.locator("#sizingCautionCount").textContent(),
  unrated: await page.locator("#sizingUnratedCount").textContent(),
  bodyWidth: await page.evaluate(() => document.body.scrollWidth),
  viewportWidth: await page.evaluate(() => window.innerWidth),
};
await page.getByRole("button", { name: "Peak axial" }).click();
desktop.peakSort = {
  direction: await page.getByRole("button", { name: "Peak axial" }).locator("xpath=..").getAttribute("aria-sort"),
  first: await page.locator("#sizingTableBody tr").first().locator("td").nth(1).textContent(),
};
await page.screenshot({ path: "member_sizing_desktop.png", fullPage: true });
await page.locator("#sizingTableBody .inspect-link").first().click();
desktop.inspectReturnedToGeometry = await page.getByRole("tab", { name: "3D Geometry" }).getAttribute("aria-selected");
desktop.selectedAssembly = await page.locator("#assembly option:checked").textContent();
desktop.selectedCase = await page.locator("#loadCase option:checked").textContent();

await page.setViewportSize({ width: 390, height: 844 });
await page.getByRole("tab", { name: "Member Sizing" }).click();
await page.screenshot({ path: "member_sizing_mobile.png", fullPage: true });
const mobile = {
  title: await page.getByRole("heading", { name: "Governing member loads" }).isVisible(),
  horizontalTableScroll: await page.locator("#sizingView .sizing-table-wrap").evaluate(el => el.scrollWidth > el.clientWidth),
  governingMarginVisible: await page.locator("#sizingTableBody tr").first().locator('[data-label="Governing MS"]').isVisible(),
  inspectVisible: await page.locator("#sizingTableBody tr").first().getByRole("button", { name: "Inspect" }).isVisible(),
  pageWidth: await page.evaluate(() => document.documentElement.scrollWidth),
  viewportWidth: await page.evaluate(() => window.innerWidth),
};
await page.setViewportSize({ width: 1600, height: 1000 });
await page.getByRole("tab", { name: "Chassis Loads" }).click();
await page.waitForSelector("#chassisCanvasHost #sharedViewport");
const chassis = {
  title: await page.getByRole("heading", { name: "Loads into the chassis" }).isVisible(),
  interfaces: await page.locator("#chassisInterfaceCount").textContent(),
  corners: await page.locator("#chassisCornerCount").textContent(),
  selection: await page.locator("#chassisCase option:checked").textContent(),
  viewportOnPage: await page.locator("#chassisCanvasHost #sharedViewport").isVisible(),
  oppositeSideControls: await page.getByText("Mirror opposite side").count(),
  envelopeTag: await page.locator("#chassisVectorTag").textContent(),
  envelopeTagVisible: await page.locator("#chassisVectorTag").isVisible(),
  canvasSize: await page.locator("#scene").evaluate(el => [el.clientWidth,el.clientHeight]),
};
await page.screenshot({ path: "chassis_resultants_3d.png", fullPage: true });
await page.getByRole("tab", { name: "3D Geometry" }).click();
chassis.viewportReturned = await page.locator("#geometryView #sharedViewport").count();
console.log(JSON.stringify({ desktop, mobile, chassis }, null, 2));
await browser.close();
