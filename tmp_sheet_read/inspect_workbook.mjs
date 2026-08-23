import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";
import fs from "node:fs/promises";

const source = "C:/Users/kyled/Downloads/Mk11 Susp Linkage Forces .xlsx";
const input = await FileBlob.load(source);
const workbook = await SpreadsheetFile.importXlsx(input);
await fs.writeFile("import_ok.txt", "ok", "utf8");

const sheets = await workbook.inspect({
  kind: "sheet",
  include: "id,name",
  maxChars: 12000,
});
console.log("SHEETS");
console.log(sheets.ndjson);
await fs.writeFile("sheets.ndjson", String(sheets.ndjson ?? ""), "utf8");

const summary = await workbook.inspect({
  kind: "workbook,sheet,table",
  maxChars: 18000,
  tableMaxRows: 8,
  tableMaxCols: 12,
  tableMaxCellChars: 80,
});
console.log("SUMMARY");
console.log(summary.ndjson);
await fs.writeFile("summary.ndjson", String(summary.ndjson ?? ""), "utf8");
