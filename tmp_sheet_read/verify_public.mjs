import { chromium } from "playwright";

const url = "https://kydeguz28.github.io/SuspensionLinkageForces/";
const browser = await chromium.launch({
  headless: true,
  executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
});
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errors = [];
page.on("pageerror", error => errors.push(error.message));
page.on("console", message => { if (message.type() === "error") errors.push(message.text()); });
const response = await page.goto(url, { waitUntil: "networkidle" });
const result = {
  status: response?.status(),
  title: await page.title(),
  geometryTab: await page.getByRole("tab", { name: "3D Geometry" }).isVisible(),
  sizingTab: await page.getByRole("tab", { name: "Member Sizing" }).isVisible(),
  chassisTab: await page.getByRole("tab", { name: "Chassis Loads" }).isVisible(),
  canvas: await page.locator("#scene").isVisible(),
  errors,
};
await page.getByRole("tab", { name: "Chassis Loads" }).click();
result.chassisRows = await page.locator("#chassisTableBody tr").count();
result.chassisCanvas = await page.locator("#chassisCanvasHost #scene").isVisible();
await page.screenshot({ path: "public_pages_viewer.png", fullPage: false });
console.log(JSON.stringify(result, null, 2));
await browser.close();
