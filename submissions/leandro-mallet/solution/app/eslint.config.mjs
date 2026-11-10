import next from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

// FE-03: nenhuma cor nem tamanho de fonte solto fora do tema (src/tema/).
const SOLTO = String.raw`(#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(|text-\[\d|bg-\[#|text-\[#|border-\[#)`;

const config = [
  { ignores: [".next/**", "node_modules/**", "scripts/**", "data/**", "next-env.d.ts"] },
  ...next,
  ...nextTs,
  {
    files: ["src/**/*.{ts,tsx}"],
    ignores: ["src/tema/**"],
    rules: {
      "no-restricted-syntax": [
        "error",
        { selector: `Literal[value=/${SOLTO}/]`, message: "Use um token do tema (src/tema/tema.css), não valor solto." },
        { selector: `TemplateElement[value.raw=/${SOLTO}/]`, message: "Use um token do tema (src/tema/tema.css), não valor solto." },
      ],
    },
  },
];

export default config;
