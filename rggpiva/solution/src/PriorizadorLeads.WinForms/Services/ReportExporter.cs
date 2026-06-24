using System.Globalization;
using System.Text;
using PriorizadorLeads.WinForms.Models;

namespace PriorizadorLeads.WinForms.Services;

public static class ReportExporter
{
    private static readonly CultureInfo PtBr = new("pt-BR");

    public static void ExportPrioritiesCsv(IEnumerable<ScoredOpportunity> opportunities, string path)
    {
        var lines = new List<string>
        {
            string.Join(';', new[]
            {
                "prioridade", "score_hibrido", "probabilidade_ml", "score_heuristico", "valor_ponderado_hibrido",
                "valor_ponderado_heuristico", "valor_potencial", "id_oportunidade", "etapa", "vendedor", "gerente",
                "regional", "conta", "setor", "produto", "idade_dias", "explicacao_ml", "justificativa_regras",
                "riscos_principais", "proxima_acao"
            })
        };

        foreach (var row in opportunities)
        {
            lines.Add(string.Join(';', new[]
            {
                Csv(row.PriorityBand),
                Csv(row.HybridScore.ToString("0.0", PtBr)),
                Csv(row.MlWinProbability.ToString("P1", PtBr)),
                Csv(row.Score.ToString("0.0", PtBr)),
                Csv(row.HybridExpectedValue.ToString("0.00", PtBr)),
                Csv(row.ExpectedValue.ToString("0.00", PtBr)),
                Csv(row.EstimatedDealValue.ToString("0.00", PtBr)),
                Csv(row.OpportunityId),
                Csv(row.EtapaPtBr),
                Csv(row.SalesAgent),
                Csv(row.Manager),
                Csv(row.RegionalOffice),
                Csv(row.Account),
                Csv(row.Sector),
                Csv(row.Product),
                Csv(row.DealAgeDays?.ToString(PtBr) ?? string.Empty),
                Csv(row.MlExplanation),
                Csv(row.WhyHighOrLow),
                Csv(row.MainRisks),
                Csv(row.NextBestAction)
            }));
        }

        File.WriteAllLines(path, lines, new UTF8Encoding(encoderShouldEmitUTF8Identifier: true));
    }

    private static string Csv(string? value)
    {
        value ??= string.Empty;
        var mustQuote = value.Contains(';') || value.Contains('"') || value.Contains('\n') || value.Contains('\r');
        value = value.Replace("\"", "\"\"");
        return mustQuote ? $"\"{value}\"" : value;
    }
}
