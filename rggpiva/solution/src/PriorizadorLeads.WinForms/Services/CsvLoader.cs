using System.Globalization;
using System.Text;
using PriorizadorLeads.WinForms.Models;

namespace PriorizadorLeads.WinForms.Services;

public static class CsvLoader
{
    public static CrmDataSet Load(string dataDirectory)
    {
        if (!Directory.Exists(dataDirectory))
            throw new DirectoryNotFoundException($"Pasta de dados não encontrada: {dataDirectory}");

        var data = new CrmDataSet();

        data.Accounts.AddRange(ReadCsv(ResolveCsv(dataDirectory, "contas.csv", "accounts.csv")).Select(row => new AccountRecord
        {
            Account = Normalize(Get(row, "conta", "account")),
            Sector = NormalizeSector(Get(row, "setor", "sector")),
            YearEstablished = ParseInt(Get(row, "ano_fundacao", "year_established")),
            Revenue = ParseDouble(Get(row, "receita_anual_milhoes_usd", "revenue")),
            Employees = ParseInt(Get(row, "funcionarios", "employees")),
            OfficeLocation = Normalize(Get(row, "localizacao_matriz", "office_location")),
            SubsidiaryOf = Normalize(Get(row, "subsidiaria_de", "subsidiary_of"))
        }));

        data.Products.AddRange(ReadCsv(ResolveCsv(dataDirectory, "produtos.csv", "products.csv")).Select(row => new ProductRecord
        {
            Product = NormalizeProduct(Get(row, "produto", "product")),
            Series = Normalize(Get(row, "serie", "series")),
            SalesPrice = ParseDouble(Get(row, "preco_venda_sugerido", "sales_price"))
        }));

        data.SalesTeams.AddRange(ReadCsv(ResolveCsv(dataDirectory, "equipes_vendas.csv", "sales_teams.csv")).Select(row => new SalesTeamRecord
        {
            SalesAgent = Normalize(Get(row, "vendedor", "sales_agent")),
            Manager = Normalize(Get(row, "gerente", "manager")),
            RegionalOffice = Normalize(Get(row, "escritorio_regional", "regional_office"))
        }));

        data.Pipeline.AddRange(ReadCsv(ResolveCsv(dataDirectory, "funil_vendas.csv", "sales_pipeline.csv")).Select(row => new PipelineRecord
        {
            OpportunityId = Normalize(Get(row, "id_oportunidade", "opportunity_id")),
            SalesAgent = Normalize(Get(row, "vendedor", "sales_agent")),
            Product = NormalizeProduct(Get(row, "produto", "product")),
            Account = Normalize(Get(row, "conta", "account")),
            DealStage = NormalizeStage(Get(row, "etapa_negocio", "deal_stage")),
            EngageDate = ParseDate(Get(row, "data_engajamento", "engage_date")),
            CloseDate = ParseDate(Get(row, "data_fechamento", "close_date")),
            CloseValue = ParseDouble(Get(row, "valor_fechamento", "close_value")) ?? 0d
        }));

        return data;
    }

    private static string ResolveCsv(string dataDirectory, string preferredPtBrName, string legacyEnglishName)
    {
        var preferred = Path.Combine(dataDirectory, preferredPtBrName);
        if (File.Exists(preferred))
            return preferred;

        var legacy = Path.Combine(dataDirectory, legacyEnglishName);
        if (File.Exists(legacy))
            return legacy;

        throw new FileNotFoundException($"Nenhum CSV encontrado para {preferredPtBrName} ou {legacyEnglishName} na pasta {dataDirectory}.");
    }

    private static string Get(Dictionary<string, string> row, params string[] possibleHeaders)
    {
        foreach (var header in possibleHeaders)
        {
            if (row.TryGetValue(header, out var value))
                return value;
        }

        return string.Empty;
    }

    private static List<Dictionary<string, string>> ReadCsv(string path)
    {
        if (!File.Exists(path))
            throw new FileNotFoundException($"Arquivo CSV não encontrado: {path}", path);

        var lines = File.ReadAllLines(path, Encoding.UTF8);
        if (lines.Length == 0)
            return new List<Dictionary<string, string>>();

        var delimiter = DetectDelimiter(lines[0]);
        var headers = SplitCsvLine(lines[0], delimiter)
            .Select(h => h.Trim().TrimStart('\uFEFF'))
            .ToArray();

        var result = new List<Dictionary<string, string>>(Math.Max(0, lines.Length - 1));

        for (var i = 1; i < lines.Length; i++)
        {
            if (string.IsNullOrWhiteSpace(lines[i]))
                continue;

            var fields = SplitCsvLine(lines[i], delimiter);
            var row = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            for (var col = 0; col < headers.Length; col++)
            {
                row[headers[col]] = col < fields.Count ? fields[col] : string.Empty;
            }
            result.Add(row);
        }

        return result;
    }

    private static char DetectDelimiter(string headerLine)
    {
        var semicolons = headerLine.Count(ch => ch == ';');
        var commas = headerLine.Count(ch => ch == ',');
        return semicolons >= commas ? ';' : ',';
    }

    private static List<string> SplitCsvLine(string line, char delimiter)
    {
        var fields = new List<string>();
        var current = new StringBuilder();
        var inQuotes = false;

        for (var i = 0; i < line.Length; i++)
        {
            var ch = line[i];
            if (ch == '"')
            {
                if (inQuotes && i + 1 < line.Length && line[i + 1] == '"')
                {
                    current.Append('"');
                    i++;
                }
                else
                {
                    inQuotes = !inQuotes;
                }
            }
            else if (ch == delimiter && !inQuotes)
            {
                fields.Add(current.ToString().Trim());
                current.Clear();
            }
            else
            {
                current.Append(ch);
            }
        }

        fields.Add(current.ToString().Trim());
        return fields;
    }

    public static string Normalize(string? value)
    {
        return (value ?? string.Empty).Trim();
    }

    public static string NormalizeProduct(string? value)
    {
        var normalized = Normalize(value);
        return normalized.Equals("GTXPro", StringComparison.OrdinalIgnoreCase) ? "GTX Pro" : normalized;
    }

    public static string NormalizeSector(string? value)
    {
        var normalized = Normalize(value);
        return normalized.Equals("technolgy", StringComparison.OrdinalIgnoreCase) ? "technology" : normalized;
    }

    public static string NormalizeStage(string? value)
    {
        var normalized = Normalize(value);
        return normalized switch
        {
            "Prospecting" => "Prospecção",
            "Engaging" => "Em negociação",
            "Won" => "Ganha",
            "Lost" => "Perdida",
            _ => normalized
        };
    }

    private static double? ParseDouble(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
            return null;

        var text = value.Trim();

        if (text.Contains(',') && !text.Contains('.'))
            text = text.Replace(',', '.');

        if (double.TryParse(text, NumberStyles.Any, CultureInfo.InvariantCulture, out var parsed))
            return parsed;

        if (double.TryParse(value.Trim(), NumberStyles.Any, new CultureInfo("pt-BR"), out parsed))
            return parsed;

        if (double.TryParse(value.Trim(), NumberStyles.Any, CultureInfo.CurrentCulture, out parsed))
            return parsed;

        return null;
    }

    private static int? ParseInt(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
            return null;

        return int.TryParse(value.Trim(), NumberStyles.Any, CultureInfo.InvariantCulture, out var parsed)
            ? parsed
            : null;
    }

    private static DateTime? ParseDate(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
            return null;

        if (DateTime.TryParseExact(value.Trim(), "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var parsed))
            return parsed.Date;

        if (DateTime.TryParse(value.Trim(), CultureInfo.InvariantCulture, DateTimeStyles.None, out parsed))
            return parsed.Date;

        return null;
    }
}
