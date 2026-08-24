import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";
import fs from "node:fs/promises";

const source = "C:/Users/kyled/Downloads/Mk11 Susp Linkage Forces .xlsx";
const input = await FileBlob.load(source);
const workbook = await SpreadsheetFile.importXlsx(input);
await fs.writeFile("import_ok.txt", "ok", "utf8");

const targets = {
  "Manufacturing Summary": "A1:T27",
  "Summary Front": "A1:R59",
  "Summary Rear": "A1:M58",
  "Rod end and plugs": "A1:AB29",
};
const extracted = {};
for (const [sheetName, address] of Object.entries(targets)) {
  const sheet = workbook.worksheets.getItem(sheetName);
  const range = sheet.getRange(address);
  extracted[sheetName] = {
    address,
    values: range.values,
    formulas: range.formulas,
  };
}
await fs.writeFile("sizing_ranges.json", JSON.stringify(extracted, null, 2), "utf8");
