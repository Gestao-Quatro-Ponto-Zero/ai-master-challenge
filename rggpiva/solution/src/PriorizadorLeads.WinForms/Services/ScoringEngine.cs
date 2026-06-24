using PriorizadorLeads.WinForms.Models;

namespace PriorizadorLeads.WinForms.Services;

public sealed class ScoringResult
{
    public List<ScoredOpportunity> Opportunities { get; init; } = new();
    public ScoringReferences References { get; init; } = new();
}

internal sealed class GroupRate
{
    public double Rate { get; init; }
    public int ClosedN { get; init; }
}

public sealed class ScoringEngine
{
    private static readonly HashSet<string> OpenStages = new(StringComparer.OrdinalIgnoreCase) { "Prospecção", "Em negociação" };
    private static readonly HashSet<string> ClosedStages = new(StringComparer.OrdinalIgnoreCase) { "Ganha", "Perdida" };

    public ScoringResult Score(CrmDataSet data)
    {
        var joined = PrepareBaseRows(data);
        var closed = joined.Where(x => x.IsClosed).ToList();
        if (closed.Count == 0)
            throw new InvalidOperationException("O dataset precisa conter oportunidades ganhas e perdidas para calibrar o scoring.");

        var globalWinRate = closed.Average(x => x.IsWon ? 1d : 0d);
        var wonCycles = closed.Where(x => x.IsWon && x.CycleDays.HasValue).Select(x => (double)x.CycleDays!.Value).ToList();
        var medianWonCycleDays = Median(wonCycles, 45d);
        var referenceDate = joined.Count > 0
            ? joined.SelectMany(x => new[] { x.CloseDate, x.EngageDate }).Where(x => x.HasValue).Select(x => x!.Value).DefaultIfEmpty(DateTime.Today).Max().Date.AddDays(1)
            : DateTime.Today;

        foreach (var row in joined)
        {
            row.DealAgeDays = row.EngageDate.HasValue ? Math.Max(0, (referenceDate - row.EngageDate.Value.Date).Days) : null;
        }

        ApplyBuckets(joined);
        ApplyEstimatedValues(joined, closed);
        ApplyGroupRates(joined, closed, globalWinRate);
        ApplyScores(joined, closed, globalWinRate, medianWonCycleDays);

        var refs = new ScoringReferences
        {
            GlobalWinRate = globalWinRate,
            ReferenceDate = referenceDate,
            MedianWonCycleDays = medianWonCycleDays,
            OpenCount = joined.Count(x => x.IsOpen),
            ClosedCount = joined.Count(x => x.IsClosed),
            DataQualityNotes = new List<string>
            {
                "A aplicação está configurada para ler os CSVs em português: contas, produtos, equipes de vendas e funil de vendas.",
                "O parser aceita separador ponto e vírgula, codificação UTF-8 com BOM e decimal com vírgula.",
                "Oportunidades sem conta, setor, preço ou data recebem penalidade leve de qualidade de dados.",
                "A data de referência usa o maior timestamp do próprio dataset, não a data atual."
            }
        };

        foreach (var row in joined)
        {
            var explanation = BuildExplanation(row, refs);
            row.WhyHighOrLow = explanation.Reasons;
            row.MainRisks = explanation.Risks;
            row.NextBestAction = NextBestAction(row);
        }

        return new ScoringResult
        {
            Opportunities = joined
                .OrderByDescending(x => x.Score)
                .ThenByDescending(x => x.ExpectedValue)
                .ToList(),
            References = refs
        };
    }

    public static List<ComponentBreakdown> GetBreakdown(ScoredOpportunity row)
    {
        return new List<ComponentBreakdown>
        {
            new() { Component = "Etapa", Score0To1 = row.StageScore, Interpretation = "Peso 20% — avanço no funil comercial" },
            new() { Component = "Vendedor / gerente / regional", Score0To1 = row.SellerScore, Interpretation = "Peso 18% — histórico comercial" },
            new() { Component = "Conta / porte", Score0To1 = row.AccountScore, Interpretation = "Peso 18% — histórico e perfil da conta" },
            new() { Component = "Produto / série", Score0To1 = row.ProductScore, Interpretation = "Peso 16% — conversão por produto" },
            new() { Component = "Setor", Score0To1 = row.SectorScore, Interpretation = "Peso 12% — aderência setorial" },
            new() { Component = "Velocidade / idade", Score0To1 = row.VelocityScore, Interpretation = "Peso 10% — risco de esfriar" },
            new() { Component = "Valor", Score0To1 = row.ValueScore, Interpretation = "Peso 6% — potencial financeiro com limite" },
            new() { Component = "Qualidade dos dados", Score0To1 = row.DataQualityScore, Interpretation = "Multiplicador — penaliza dados incompletos" },
            new() { Component = "Probabilidade ML", Score0To1 = row.MlWinProbability, Interpretation = "Modelo supervisionado ML.NET treinado em oportunidades Ganha/Perdida" },
            new() { Component = "Score híbrido", Score0To1 = row.HybridScore / 100d, Interpretation = "Combina 55% score explicável + 45% probabilidade ML" }
        };
    }

    private static List<ScoredOpportunity> PrepareBaseRows(CrmDataSet data)
    {
        var accounts = data.Accounts
            .GroupBy(x => x.Account, StringComparer.OrdinalIgnoreCase)
            .ToDictionary(x => x.Key, x => x.First(), StringComparer.OrdinalIgnoreCase);

        var products = data.Products
            .GroupBy(x => x.Product, StringComparer.OrdinalIgnoreCase)
            .ToDictionary(x => x.Key, x => x.First(), StringComparer.OrdinalIgnoreCase);

        var teams = data.SalesTeams
            .GroupBy(x => x.SalesAgent, StringComparer.OrdinalIgnoreCase)
            .ToDictionary(x => x.Key, x => x.First(), StringComparer.OrdinalIgnoreCase);

        var rows = new List<ScoredOpportunity>(data.Pipeline.Count);
        foreach (var p in data.Pipeline)
        {
            accounts.TryGetValue(p.Account, out var account);
            products.TryGetValue(p.Product, out var product);
            teams.TryGetValue(p.SalesAgent, out var team);

            var cycleDays = p.CloseDate.HasValue && p.EngageDate.HasValue
                ? (int?)(p.CloseDate.Value.Date - p.EngageDate.Value.Date).Days
                : null;
            if (cycleDays < 0)
                cycleDays = null;

            var dealStage = SafeText(p.DealStage, "Não informado");
            rows.Add(new ScoredOpportunity
            {
                OpportunityId = SafeText(p.OpportunityId, "Não informado"),
                SalesAgent = SafeText(p.SalesAgent, "Não informado"),
                Product = SafeText(p.Product, "Não informado"),
                Account = string.IsNullOrWhiteSpace(p.Account) ? "Conta não informada" : p.Account,
                DealStage = dealStage,
                EngageDate = p.EngageDate,
                CloseDate = p.CloseDate,
                CloseValue = p.CloseValue,
                IsOpen = OpenStages.Contains(dealStage),
                IsClosed = ClosedStages.Contains(dealStage),
                IsWon = dealStage.Equals("Ganha", StringComparison.OrdinalIgnoreCase),
                CycleDays = cycleDays,
                Sector = SafeText(account?.Sector, "Não informado"),
                OfficeLocation = SafeText(account?.OfficeLocation, "Não informado"),
                SubsidiaryOf = SafeText(account?.SubsidiaryOf, "Independente / não informado"),
                Revenue = account?.Revenue,
                Employees = account?.Employees,
                Series = SafeText(product?.Series, "Não informado"),
                SalesPrice = product?.SalesPrice,
                Manager = SafeText(team?.Manager, "Não informado"),
                RegionalOffice = SafeText(team?.RegionalOffice, "Não informado"),
                RevenueBucket = "Não informado",
                EmployeesBucket = "Não informado"
            });
        }

        return rows;
    }

    private static void ApplyBuckets(List<ScoredOpportunity> rows)
    {
        var revenueValues = rows.Where(x => x.Revenue.HasValue).Select(x => x.Revenue!.Value).OrderBy(x => x).ToList();
        var employeeValues = rows.Where(x => x.Employees.HasValue).Select(x => (double)x.Employees!.Value).OrderBy(x => x).ToList();

        var revenueQ1 = Quantile(revenueValues, 0.25);
        var revenueQ2 = Quantile(revenueValues, 0.50);
        var revenueQ3 = Quantile(revenueValues, 0.75);
        var empQ1 = Quantile(employeeValues, 0.25);
        var empQ2 = Quantile(employeeValues, 0.50);
        var empQ3 = Quantile(employeeValues, 0.75);

        foreach (var row in rows)
        {
            row.RevenueBucket = row.Revenue.HasValue
                ? Bucket(row.Revenue.Value, revenueQ1, revenueQ2, revenueQ3, "Receita baixa", "Receita média", "Receita alta", "Receita enterprise")
                : "Não informado";

            row.EmployeesBucket = row.Employees.HasValue
                ? Bucket(row.Employees.Value, empQ1, empQ2, empQ3, "Equipe pequena", "Equipe média", "Equipe grande", "Equipe enterprise")
                : "Não informado";
        }
    }

    private static void ApplyEstimatedValues(List<ScoredOpportunity> rows, List<ScoredOpportunity> closed)
    {
        var won = closed.Where(x => x.IsWon).ToList();
        var globalMedianClose = Median(won.Select(x => x.CloseValue).Where(x => x > 0).ToList(), 0d);
        var productMedian = won
            .Where(x => x.CloseValue > 0)
            .GroupBy(x => x.Product, StringComparer.OrdinalIgnoreCase)
            .ToDictionary(x => x.Key, x => Median(x.Select(v => v.CloseValue).ToList(), globalMedianClose), StringComparer.OrdinalIgnoreCase);

        foreach (var row in rows)
        {
            if (row.SalesPrice.HasValue)
                row.EstimatedDealValue = row.SalesPrice.Value;
            else if (productMedian.TryGetValue(row.Product, out var medianByProduct))
                row.EstimatedDealValue = medianByProduct;
            else
                row.EstimatedDealValue = globalMedianClose;
        }
    }

    private static void ApplyGroupRates(List<ScoredOpportunity> rows, List<ScoredOpportunity> closed, double globalWinRate)
    {
        var byAgent = SmoothedWinRate(closed, x => x.SalesAgent, globalWinRate);
        var byManager = SmoothedWinRate(closed, x => x.Manager, globalWinRate);
        var byRegional = SmoothedWinRate(closed, x => x.RegionalOffice, globalWinRate);
        var byProduct = SmoothedWinRate(closed, x => x.Product, globalWinRate);
        var bySeries = SmoothedWinRate(closed, x => x.Series, globalWinRate);
        var byAccount = SmoothedWinRate(closed, x => x.Account, globalWinRate);
        var bySector = SmoothedWinRate(closed, x => x.Sector, globalWinRate);
        var byRevenueBucket = SmoothedWinRate(closed, x => x.RevenueBucket, globalWinRate);
        var byEmployeesBucket = SmoothedWinRate(closed, x => x.EmployeesBucket, globalWinRate);

        foreach (var row in rows)
        {
            var agent = GetRate(byAgent, row.SalesAgent, globalWinRate);
            var manager = GetRate(byManager, row.Manager, globalWinRate);
            var regional = GetRate(byRegional, row.RegionalOffice, globalWinRate);
            var product = GetRate(byProduct, row.Product, globalWinRate);
            var series = GetRate(bySeries, row.Series, globalWinRate);
            var account = GetRate(byAccount, row.Account, globalWinRate);
            var sector = GetRate(bySector, row.Sector, globalWinRate);
            var revenueBucket = GetRate(byRevenueBucket, row.RevenueBucket, globalWinRate);
            var employeesBucket = GetRate(byEmployeesBucket, row.EmployeesBucket, globalWinRate);

            row.SalesAgentWinRate = agent.Rate;
            row.ManagerWinRate = manager.Rate;
            row.RegionalOfficeWinRate = regional.Rate;
            row.ProductWinRate = product.Rate;
            row.SeriesWinRate = series.Rate;
            row.AccountWinRate = account.Rate;
            row.SectorWinRate = sector.Rate;
            row.RevenueBucketWinRate = revenueBucket.Rate;
            row.EmployeesBucketWinRate = employeesBucket.Rate;

            row.SalesAgentClosedN = agent.ClosedN;
            row.ProductClosedN = product.ClosedN;
            row.AccountClosedN = account.ClosedN;
            row.SectorClosedN = sector.ClosedN;
        }
    }

    private static void ApplyScores(List<ScoredOpportunity> rows, List<ScoredOpportunity> closed, double globalWinRate, double medianWonCycleDays)
    {
        var wonCyclesByProduct = closed
            .Where(x => x.IsWon && x.CycleDays.HasValue)
            .GroupBy(x => x.Product, StringComparer.OrdinalIgnoreCase)
            .ToDictionary(x => x.Key, x => Median(x.Select(v => (double)v.CycleDays!.Value).ToList(), medianWonCycleDays), StringComparer.OrdinalIgnoreCase);

        var valueRanks = PercentileRanks(rows.Select(x => x.EstimatedDealValue).ToList());

        for (var i = 0; i < rows.Count; i++)
        {
            var row = rows[i];
            row.StageScore = row.DealStage switch
            {
                "Prospecção" => Math.Max(globalWinRate - 0.18, 0.25),
                "Em negociação" => Math.Min(globalWinRate + 0.14, 0.90),
                "Ganha" => 1.0,
                "Perdida" => 0.0,
                _ => globalWinRate
            };

            row.SellerScore = 0.60 * row.SalesAgentWinRate + 0.25 * row.ManagerWinRate + 0.15 * row.RegionalOfficeWinRate;
            row.ProductScore = 0.75 * row.ProductWinRate + 0.25 * row.SeriesWinRate;
            row.AccountScore = 0.55 * row.AccountWinRate + 0.25 * row.RevenueBucketWinRate + 0.20 * row.EmployeesBucketWinRate;
            row.SectorScore = row.SectorWinRate;
            row.VelocityScore = VelocityScore(row, medianWonCycleDays, wonCyclesByProduct);
            row.ValueScore = 0.45 + 0.50 * valueRanks[i];

            var quality = DataQuality(row);
            row.DataQualityScore = quality.Score;
            row.QualityNotes = quality.Notes;

            var raw =
                row.StageScore * 0.20 +
                row.SellerScore * 0.18 +
                row.AccountScore * 0.18 +
                row.ProductScore * 0.16 +
                row.SectorScore * 0.12 +
                row.VelocityScore * 0.10 +
                row.ValueScore * 0.06;

            row.Score = Math.Round(Math.Clamp(100d * raw * row.DataQualityScore, 1d, 99d), 1);
            if (row.DealStage.Equals("Ganha", StringComparison.OrdinalIgnoreCase))
                row.Score = 100d;
            if (row.DealStage.Equals("Perdida", StringComparison.OrdinalIgnoreCase))
                row.Score = 0d;

            row.PriorityBand = PriorityBand(row.Score);
            row.ExpectedValue = Math.Round(row.EstimatedDealValue * row.Score / 100d, 2);

            row.StageScore = Math.Round(row.StageScore, 3);
            row.SellerScore = Math.Round(row.SellerScore, 3);
            row.ProductScore = Math.Round(row.ProductScore, 3);
            row.AccountScore = Math.Round(row.AccountScore, 3);
            row.SectorScore = Math.Round(row.SectorScore, 3);
            row.VelocityScore = Math.Round(row.VelocityScore, 3);
            row.ValueScore = Math.Round(row.ValueScore, 3);
            row.DataQualityScore = Math.Round(row.DataQualityScore, 3);
        }
    }

    private static Dictionary<string, GroupRate> SmoothedWinRate(List<ScoredOpportunity> closed, Func<ScoredOpportunity, string> selector, double globalWinRate, double priorStrength = 15d)
    {
        return closed
            .GroupBy(selector, StringComparer.OrdinalIgnoreCase)
            .ToDictionary(
                g => SafeText(g.Key, "Não informado"),
                g =>
                {
                    var n = g.Count();
                    var wins = g.Count(x => x.IsWon);
                    return new GroupRate
                    {
                        ClosedN = n,
                        Rate = (wins + priorStrength * globalWinRate) / (n + priorStrength)
                    };
                },
                StringComparer.OrdinalIgnoreCase);
    }

    private static GroupRate GetRate(Dictionary<string, GroupRate> rates, string key, double globalWinRate)
    {
        return rates.TryGetValue(SafeText(key, "Não informado"), out var found)
            ? found
            : new GroupRate { Rate = globalWinRate, ClosedN = 0 };
    }

    private static double VelocityScore(ScoredOpportunity row, double medianWonCycleDays, Dictionary<string, double> productCycleMap)
    {
        if (row.DealStage.Equals("Prospecção", StringComparison.OrdinalIgnoreCase) && !row.EngageDate.HasValue)
            return 0.46;
        if (!row.DealAgeDays.HasValue)
            return 0.50;

        var typicalCycle = productCycleMap.TryGetValue(row.Product, out var byProduct) ? byProduct : medianWonCycleDays;
        if (typicalCycle <= 0)
            typicalCycle = medianWonCycleDays > 0 ? medianWonCycleDays : 45d;

        var age = row.DealAgeDays.Value;
        if (age <= typicalCycle * 0.55) return 0.92;
        if (age <= typicalCycle) return 0.78;
        if (age <= typicalCycle * 1.45) return 0.58;
        if (age <= typicalCycle * 2.0) return 0.38;
        return 0.22;
    }

    private static (double Score, List<string> Notes) DataQuality(ScoredOpportunity row)
    {
        var score = 1.0;
        var notes = new List<string>();

        if (row.Account.Equals("Conta não informada", StringComparison.OrdinalIgnoreCase))
        {
            score -= 0.12;
            notes.Add("conta não informada");
        }
        if (row.Sector.Equals("Não informado", StringComparison.OrdinalIgnoreCase))
        {
            score -= 0.06;
            notes.Add("setor não informado");
        }
        if (!row.SalesPrice.HasValue)
        {
            score -= 0.08;
            notes.Add("preço de produto estimado");
        }
        if (row.DealStage.Equals("Prospecção", StringComparison.OrdinalIgnoreCase) && !row.EngageDate.HasValue)
        {
            score -= 0.04;
            notes.Add("ainda sem data de engajamento");
        }

        return (Math.Max(score, 0.70), notes);
    }

    private static (string Reasons, string Risks) BuildExplanation(ScoredOpportunity row, ScoringReferences refs)
    {
        var reasons = new List<string>();
        var risks = new List<string>();
        var global = refs.GlobalWinRate;

        if (row.DealStage.Equals("Em negociação", StringComparison.OrdinalIgnoreCase))
            reasons.Add("já está em negociação, portanto está mais avançada no funil");
        else if (row.DealStage.Equals("Prospecção", StringComparison.OrdinalIgnoreCase))
            risks.Add("ainda está em prospecção, então precisa validar necessidade e timing");

        CheckRate(row.SalesAgentWinRate, "histórico do vendedor acima da média", "vendedor abaixo da média", global, reasons, risks);
        CheckRate(row.ProductWinRate, "produto com conversão histórica acima da média", "produto abaixo da média", global, reasons, risks);
        CheckRate(row.AccountWinRate, "conta com histórico favorável no CRM", "conta abaixo da média", global, reasons, risks);
        CheckRate(row.SectorWinRate, "setor com bom histórico de fechamento", "setor abaixo da média", global, reasons, risks);
        CheckRate(row.RevenueBucketWinRate, "porte de conta com boa conversão histórica", "porte abaixo da média", global, reasons, risks);

        if (row.VelocityScore >= 0.80)
            reasons.Add("idade da oportunidade ainda compatível com ciclos ganhos");
        else if (row.VelocityScore <= 0.40)
            risks.Add("oportunidade parece fria pelo tempo no pipeline");

        if (row.ValueScore >= 0.80)
            reasons.Add("valor potencial relevante sem dominar sozinho o score");

        foreach (var note in row.QualityNotes)
            risks.Add($"dado incompleto: {note}");

        if (reasons.Count == 0)
            reasons.Add("score sustentado principalmente pela média histórica do funil");
        if (risks.Count == 0)
            risks.Add("sem risco crítico identificado nos campos disponíveis");

        return (string.Join("; ", reasons.Take(4)), string.Join("; ", risks.Take(3)));
    }

    private static void CheckRate(double value, string positiveText, string negativeText, double global, List<string> reasons, List<string> risks)
    {
        if (value >= global + 0.06)
            reasons.Add($"{positiveText} ({value:P0} vs média {global:P0})");
        else if (value <= global - 0.08)
            risks.Add($"{negativeText} ({value:P0} vs {global:P0})");
    }

    private static string NextBestAction(ScoredOpportunity row)
    {
        if (row.Account.Equals("Conta não informada", StringComparison.OrdinalIgnoreCase))
            return "Completar conta e contexto antes de investir tempo comercial relevante.";
        if (row.Score >= 68 && row.DealStage.Equals("Em negociação", StringComparison.OrdinalIgnoreCase))
            return "Priorizar hoje: confirmar decisor, objeções, proposta e próxima data de fechamento.";
        if (row.Score >= 68 && row.DealStage.Equals("Prospecção", StringComparison.OrdinalIgnoreCase))
            return "Fazer primeiro contato personalizado e avançar rapidamente para negociação.";
        if (row.VelocityScore <= 0.38)
            return "Reaquecer: validar se ainda existe dor, orçamento e janela de decisão.";
        if (row.Score >= 58)
            return "Trabalhar nesta semana: agendar follow-up objetivo com próximo passo registrado.";
        if (row.Score >= 50)
            return "Nutrir com cadência leve e buscar novo sinal de intenção antes de aumentar o esforço comercial.";
        return "Baixa prioridade: automatizar nutrição ou revisar qualificação antes de dedicar tempo do vendedor.";
    }

    private static string PriorityBand(double score)
    {
        if (score >= 68) return "A - Focar hoje";
        if (score >= 58) return "B - Trabalhar nesta semana";
        if (score >= 50) return "C - Nutrir / validar";
        return "D - Baixa prioridade";
    }

    private static List<double> PercentileRanks(List<double> values)
    {
        if (values.Count == 0)
            return new List<double>();

        var ordered = values
            .Select((value, index) => new { value, index })
            .OrderBy(x => x.value)
            .ToList();

        var ranks = new double[values.Count];
        for (var i = 0; i < ordered.Count; i++)
            ranks[ordered[i].index] = (i + 1d) / ordered.Count;

        return ranks.ToList();
    }

    private static string Bucket(double value, double q1, double q2, double q3, string low, string medium, string high, string enterprise)
    {
        if (value <= q1) return low;
        if (value <= q2) return medium;
        if (value <= q3) return high;
        return enterprise;
    }

    private static double Quantile(List<double> sortedValues, double probability)
    {
        if (sortedValues.Count == 0)
            return 0d;
        if (sortedValues.Count == 1)
            return sortedValues[0];

        var position = (sortedValues.Count - 1) * probability;
        var lower = (int)Math.Floor(position);
        var upper = (int)Math.Ceiling(position);
        if (lower == upper)
            return sortedValues[lower];
        var weight = position - lower;
        return sortedValues[lower] * (1d - weight) + sortedValues[upper] * weight;
    }

    private static double Median(List<double> values, double fallback)
    {
        var clean = values.Where(x => !double.IsNaN(x) && !double.IsInfinity(x)).OrderBy(x => x).ToList();
        if (clean.Count == 0)
            return fallback;
        var mid = clean.Count / 2;
        return clean.Count % 2 == 0 ? (clean[mid - 1] + clean[mid]) / 2d : clean[mid];
    }

    private static string SafeText(string? value, string fallback)
    {
        return string.IsNullOrWhiteSpace(value) ? fallback : value.Trim();
    }
}
