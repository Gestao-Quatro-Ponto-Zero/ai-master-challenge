using Microsoft.ML;
using Microsoft.ML.Data;
using PriorizadorLeads.WinForms.Models;

namespace PriorizadorLeads.WinForms.Services;

/// <summary>
/// Treina um modelo supervisionado de classificação binária usando apenas oportunidades fechadas.
/// O alvo é: Ganha = true, Perdida = false.
/// A etapa do negócio não entra como feature para evitar vazamento de informação.
/// </summary>
public sealed class MachineLearningLeadScorer
{
    private const int Seed = 42;
    private readonly MLContext _ml = new(seed: Seed);

    public MlTrainingSummary TrainAndApply(List<ScoredOpportunity> opportunities)
    {
        var closed = opportunities
            .Where(x => x.IsClosed)
            .Select(ToInput)
            .Where(x => !string.IsNullOrWhiteSpace(x.SalesAgent))
            .ToList();

        if (closed.Count < 100)
            return Fail($"Base insuficiente para treinar ML. Oportunidades fechadas encontradas: {closed.Count}.");

        var random = new Random(Seed);
        var shuffled = closed
            .OrderBy(_ => random.Next())
            .ToList();

        var testCount = Math.Max(1, (int)Math.Round(shuffled.Count * 0.20));
        var testRows = shuffled.Take(testCount).ToList();
        var trainRows = shuffled.Skip(testCount).ToList();

        var trainData = _ml.Data.LoadFromEnumerable(trainRows);
        var testData = _ml.Data.LoadFromEnumerable(testRows);

        var pipeline = BuildPipeline();
        var model = pipeline.Fit(trainData);
        var scoredTest = model.Transform(testData);
        var metrics = _ml.BinaryClassification.Evaluate(scoredTest, labelColumnName: nameof(MlOpportunityInput.Label));

        var predictor = _ml.Model.CreatePredictionEngine<MlOpportunityInput, MlOpportunityPrediction>(model);
        foreach (var opportunity in opportunities)
        {
            var prediction = predictor.Predict(ToInput(opportunity));
            var probability = Math.Clamp(prediction.Probability, 0f, 1f);

            opportunity.MlWinProbability = Math.Round(probability, 4);
            opportunity.HybridScore = Math.Round(0.55 * opportunity.Score + 0.45 * opportunity.MlScore, 1);
            opportunity.HybridExpectedValue = Math.Round(opportunity.EstimatedDealValue * opportunity.HybridScore / 100d, 2);
            opportunity.MlBand = BuildMlBand(opportunity.MlWinProbability);
            opportunity.PriorityBand = BuildHybridPriorityBand(opportunity.HybridScore);
            opportunity.MlExplanation = BuildMlExplanation(opportunity);

            if (opportunity.IsWon)
            {
                opportunity.HybridScore = 100d;
                opportunity.HybridExpectedValue = opportunity.EstimatedDealValue;
                opportunity.PriorityBand = "Ganha";
            }
            else if (opportunity.DealStage.Equals("Perdida", StringComparison.OrdinalIgnoreCase))
            {
                opportunity.HybridScore = 0d;
                opportunity.HybridExpectedValue = 0d;
                opportunity.PriorityBand = "Perdida";
            }
        }

        return new MlTrainingSummary
        {
            IsAvailable = true,
            StatusMessage = "Modelo ML.NET treinado e aplicado com sucesso.",
            ClosedRows = closed.Count,
            TrainRows = trainRows.Count,
            TestRows = testRows.Count,
            Accuracy = metrics.Accuracy,
            AreaUnderRocCurve = metrics.AreaUnderRocCurve,
            AreaUnderPrecisionRecallCurve = metrics.AreaUnderPrecisionRecallCurve,
            F1Score = metrics.F1Score,
            LogLoss = metrics.LogLoss,
            TrainedAt = DateTime.Now,
            FeaturesUsed = FeatureList(),
            Notes = new List<string>
            {
                "Alvo supervisionado: oportunidades fechadas como Ganha ou Perdida.",
                "A etapa do negócio foi excluída das features para evitar vazamento de informação, pois Ganha/Perdida já é o próprio resultado final.",
                "A probabilidade ML foi combinada ao score explicável, gerando um score híbrido mais defensável para uso comercial.",
                "O modelo deve ser revalidado em produção com dados reais de leads, atividades, origem, cadência, propostas e motivos de perda."
            }
        };
    }

    private IEstimator<ITransformer> BuildPipeline()
    {
        return _ml.Transforms.Categorical.OneHotEncoding("SalesAgentEncoded", nameof(MlOpportunityInput.SalesAgent))
            .Append(_ml.Transforms.Categorical.OneHotEncoding("ManagerEncoded", nameof(MlOpportunityInput.Manager)))
            .Append(_ml.Transforms.Categorical.OneHotEncoding("RegionalOfficeEncoded", nameof(MlOpportunityInput.RegionalOffice)))
            .Append(_ml.Transforms.Categorical.OneHotEncoding("AccountEncoded", nameof(MlOpportunityInput.Account)))
            .Append(_ml.Transforms.Categorical.OneHotEncoding("SectorEncoded", nameof(MlOpportunityInput.Sector)))
            .Append(_ml.Transforms.Categorical.OneHotEncoding("ProductEncoded", nameof(MlOpportunityInput.Product)))
            .Append(_ml.Transforms.Categorical.OneHotEncoding("SeriesEncoded", nameof(MlOpportunityInput.Series)))
            .Append(_ml.Transforms.Categorical.OneHotEncoding("RevenueBucketEncoded", nameof(MlOpportunityInput.RevenueBucket)))
            .Append(_ml.Transforms.Categorical.OneHotEncoding("EmployeesBucketEncoded", nameof(MlOpportunityInput.EmployeesBucket)))
            .Append(_ml.Transforms.Concatenate("Features",
                "SalesAgentEncoded",
                "ManagerEncoded",
                "RegionalOfficeEncoded",
                "AccountEncoded",
                "SectorEncoded",
                "ProductEncoded",
                "SeriesEncoded",
                "RevenueBucketEncoded",
                "EmployeesBucketEncoded",
                nameof(MlOpportunityInput.Revenue),
                nameof(MlOpportunityInput.Employees),
                nameof(MlOpportunityInput.SalesPrice),
                nameof(MlOpportunityInput.DealAgeDays)))
            .Append(_ml.BinaryClassification.Trainers.FastTree(
                labelColumnName: nameof(MlOpportunityInput.Label),
                featureColumnName: "Features",
                numberOfLeaves: 24,
                numberOfTrees: 160,
                minimumExampleCountPerLeaf: 15,
                learningRate: 0.08));
    }

    private static MlOpportunityInput ToInput(ScoredOpportunity opportunity)
    {
        return new MlOpportunityInput
        {
            Label = opportunity.IsWon,
            SalesAgent = Clean(opportunity.SalesAgent),
            Manager = Clean(opportunity.Manager),
            RegionalOffice = Clean(opportunity.RegionalOffice),
            Account = Clean(opportunity.Account),
            Sector = Clean(opportunity.Sector),
            Product = Clean(opportunity.Product),
            Series = Clean(opportunity.Series),
            RevenueBucket = Clean(opportunity.RevenueBucket),
            EmployeesBucket = Clean(opportunity.EmployeesBucket),
            Revenue = ToFloat(opportunity.Revenue),
            Employees = opportunity.Employees ?? 0,
            SalesPrice = ToFloat(opportunity.SalesPrice),
            DealAgeDays = opportunity.CycleDays ?? opportunity.DealAgeDays ?? 0
        };
    }

    private static float ToFloat(double? value)
    {
        if (!value.HasValue || double.IsNaN(value.Value) || double.IsInfinity(value.Value))
            return 0f;
        return (float)value.Value;
    }

    private static string Clean(string? value)
    {
        return string.IsNullOrWhiteSpace(value) ? "Não informado" : value.Trim();
    }

    private static string BuildMlBand(double probability)
    {
        if (probability >= 0.75) return "Alta probabilidade ML";
        if (probability >= 0.60) return "Boa probabilidade ML";
        if (probability >= 0.45) return "Probabilidade intermediária ML";
        return "Baixa probabilidade ML";
    }

    private static string BuildHybridPriorityBand(double hybridScore)
    {
        if (hybridScore >= 72) return "A - Focar hoje";
        if (hybridScore >= 60) return "B - Trabalhar nesta semana";
        if (hybridScore >= 48) return "C - Nutrir / validar";
        return "D - Baixa prioridade";
    }

    private static string BuildMlExplanation(ScoredOpportunity row)
    {
        var parts = new List<string>
        {
            $"probabilidade ML de ganho: {row.MlWinProbability:P1}",
            $"score heurístico: {row.Score:0.0}",
            $"score híbrido: {row.HybridScore:0.0}"
        };

        if (row.MlWinProbability >= 0.70 && row.Score >= 60)
            parts.Add("modelo e regras concordam em priorizar a oportunidade");
        else if (row.MlWinProbability >= 0.70 && row.Score < 60)
            parts.Add("o modelo encontrou padrão histórico favorável que não estava tão forte nas regras");
        else if (row.MlWinProbability < 0.45 && row.Score >= 60)
            parts.Add("as regras indicam prioridade, mas o padrão histórico do modelo recomenda cautela");
        else if (row.MlWinProbability < 0.45)
            parts.Add("padrão histórico semelhante a oportunidades que tenderam a perda");
        else
            parts.Add("resultado intermediário, recomenda validação comercial antes de alto esforço");

        return string.Join("; ", parts);
    }

    private static List<string> FeatureList()
    {
        return new List<string>
        {
            "vendedor",
            "gerente",
            "escritório regional",
            "conta",
            "setor",
            "produto",
            "série do produto",
            "faixa de receita",
            "faixa de funcionários",
            "receita anual",
            "número de funcionários",
            "preço sugerido do produto",
            "idade/ciclo da oportunidade"
        };
    }

    private static MlTrainingSummary Fail(string message)
    {
        return new MlTrainingSummary
        {
            IsAvailable = false,
            StatusMessage = message,
            TrainedAt = DateTime.Now,
            Notes = new List<string> { message }
        };
    }

    private sealed class MlOpportunityInput
    {
        public bool Label { get; set; }
        public string SalesAgent { get; set; } = string.Empty;
        public string Manager { get; set; } = string.Empty;
        public string RegionalOffice { get; set; } = string.Empty;
        public string Account { get; set; } = string.Empty;
        public string Sector { get; set; } = string.Empty;
        public string Product { get; set; } = string.Empty;
        public string Series { get; set; } = string.Empty;
        public string RevenueBucket { get; set; } = string.Empty;
        public string EmployeesBucket { get; set; } = string.Empty;
        public float Revenue { get; set; }
        public float Employees { get; set; }
        public float SalesPrice { get; set; }
        public float DealAgeDays { get; set; }
    }

    private sealed class MlOpportunityPrediction
    {
        [ColumnName("PredictedLabel")]
        public bool PredictedLabel { get; set; }
        public float Probability { get; set; }
        public float Score { get; set; }
    }
}
