import { readFile } from "node:fs/promises";
import path from "node:path";

export type SalesAgentOption = {
  name: string;
  manager: string;
  regionalOffice: string;
};

const SALES_TEAM_FILE_PATH = path.join(
  process.cwd(),
  "public",
  "docs",
  "sales_teams.csv",
);

function parseCsvLine(line: string): string[] {
  const values: string[] = [];
  let currentValue = "";
  let isInsideQuotes = false;

  for (let index = 0; index < line.length; index += 1) {
    const character = line[index];

    if (character === '"') {
      const nextCharacter = line[index + 1];

      if (isInsideQuotes && nextCharacter === '"') {
        currentValue += '"';
        index += 1;
        continue;
      }

      isInsideQuotes = !isInsideQuotes;
      continue;
    }

    if (character === "," && !isInsideQuotes) {
      values.push(currentValue.trim());
      currentValue = "";
      continue;
    }

    currentValue += character;
  }

  values.push(currentValue.trim());
  return values;
}

function parseSalesTeamCsv(fileContents: string): SalesAgentOption[] {
  const [headerLine, ...rows] = fileContents
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (!headerLine) {
    throw new Error("sales_teams.csv is empty.");
  }

  const headers = parseCsvLine(headerLine);
  const expectedHeaders = ["sales_agent", "manager", "regional_office"];

  if (expectedHeaders.some((header, index) => headers[index] !== header)) {
    throw new Error("sales_teams.csv headers do not match the expected schema.");
  }

  return rows.map((row, rowIndex) => {
    const values = parseCsvLine(row);
    const [name, manager, regionalOffice] = values;

    if (!name || !manager || !regionalOffice) {
      throw new Error(
        `sales_teams.csv row ${rowIndex + 2} is missing required values.`,
      );
    }

    return {
      name,
      manager,
      regionalOffice,
    };
  });
}

export async function getSalesAgentOptions(): Promise<SalesAgentOption[]> {
  const fileContents = await readFile(SALES_TEAM_FILE_PATH, "utf8");

  return parseSalesTeamCsv(fileContents).sort((leftAgent, rightAgent) =>
    leftAgent.name.localeCompare(rightAgent.name),
  );
}
