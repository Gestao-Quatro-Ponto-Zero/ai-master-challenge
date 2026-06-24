namespace PriorizadorLeads.WinForms.Models;

public sealed class AccountRecord
{
    public string Account { get; set; } = string.Empty;
    public string Sector { get; set; } = string.Empty;
    public int? YearEstablished { get; set; }
    public double? Revenue { get; set; }
    public int? Employees { get; set; }
    public string OfficeLocation { get; set; } = string.Empty;
    public string SubsidiaryOf { get; set; } = string.Empty;
}

public sealed class ProductRecord
{
    public string Product { get; set; } = string.Empty;
    public string Series { get; set; } = string.Empty;
    public double? SalesPrice { get; set; }
}

public sealed class SalesTeamRecord
{
    public string SalesAgent { get; set; } = string.Empty;
    public string Manager { get; set; } = string.Empty;
    public string RegionalOffice { get; set; } = string.Empty;
}

public sealed class PipelineRecord
{
    public string OpportunityId { get; set; } = string.Empty;
    public string SalesAgent { get; set; } = string.Empty;
    public string Product { get; set; } = string.Empty;
    public string Account { get; set; } = string.Empty;
    public string DealStage { get; set; } = string.Empty;
    public DateTime? EngageDate { get; set; }
    public DateTime? CloseDate { get; set; }
    public double CloseValue { get; set; }
}

public sealed class CrmDataSet
{
    public List<AccountRecord> Accounts { get; } = new();
    public List<ProductRecord> Products { get; } = new();
    public List<SalesTeamRecord> SalesTeams { get; } = new();
    public List<PipelineRecord> Pipeline { get; } = new();
}

public sealed class ScoringReferences
{
    public double GlobalWinRate { get; set; }
    public DateTime ReferenceDate { get; set; }
    public double MedianWonCycleDays { get; set; }
    public int OpenCount { get; set; }
    public int ClosedCount { get; set; }
    public List<string> DataQualityNotes { get; set; } = new();
}

public sealed class MlTrainingSummary
{
    public bool IsAvailable { get; set; }
    public string StatusMessage { get; set; } = string.Empty;
    public int ClosedRows { get; set; }
    public int TrainRows { get; set; }
    public int TestRows { get; set; }
    public double Accuracy { get; set; }
    public double AreaUnderRocCurve { get; set; }
    public double AreaUnderPrecisionRecallCurve { get; set; }
    public double F1Score { get; set; }
    public double LogLoss { get; set; }
    public DateTime TrainedAt { get; set; }
    public List<string> FeaturesUsed { get; set; } = new();
    public List<string> Notes { get; set; } = new();
}

public sealed class ComponentBreakdown
{
    public string Component { get; set; } = string.Empty;
    public double Score0To1 { get; set; }
    public string Interpretation { get; set; } = string.Empty;
}

public sealed class ScoredOpportunity
{
    public string PriorityBand { get; set; } = string.Empty;
    public double Score { get; set; }
    public double ExpectedValue { get; set; }
    public double EstimatedDealValue { get; set; }
    public string OpportunityId { get; set; } = string.Empty;
    public string DealStage { get; set; } = string.Empty;
    public string EtapaPtBr => DealStage switch
    {
        "Prospecting" => "Prospecção",
        "Engaging" => "Em negociação",
        "Won" => "Ganha",
        "Lost" => "Perdida",
        "Prospecção" => "Prospecção",
        "Em negociação" => "Em negociação",
        "Ganha" => "Ganha",
        "Perdida" => "Perdida",
        _ => string.IsNullOrWhiteSpace(DealStage) ? "Não informada" : DealStage
    };
    public string SalesAgent { get; set; } = string.Empty;
    public string Manager { get; set; } = string.Empty;
    public string RegionalOffice { get; set; } = string.Empty;
    public string Account { get; set; } = string.Empty;
    public string Sector { get; set; } = string.Empty;
    public string OfficeLocation { get; set; } = string.Empty;
    public string SubsidiaryOf { get; set; } = string.Empty;
    public double? Revenue { get; set; }
    public int? Employees { get; set; }
    public string Product { get; set; } = string.Empty;
    public string Series { get; set; } = string.Empty;
    public double? SalesPrice { get; set; }
    public DateTime? EngageDate { get; set; }
    public DateTime? CloseDate { get; set; }
    public double CloseValue { get; set; }
    public int? DealAgeDays { get; set; }
    public int? CycleDays { get; set; }
    public bool IsOpen { get; set; }
    public bool IsClosed { get; set; }
    public bool IsWon { get; set; }
    public string RevenueBucket { get; set; } = string.Empty;
    public string EmployeesBucket { get; set; } = string.Empty;

    public double StageScore { get; set; }
    public double SellerScore { get; set; }
    public double ProductScore { get; set; }
    public double AccountScore { get; set; }
    public double SectorScore { get; set; }
    public double VelocityScore { get; set; }
    public double ValueScore { get; set; }
    public double DataQualityScore { get; set; }

    public double SalesAgentWinRate { get; set; }
    public double ManagerWinRate { get; set; }
    public double RegionalOfficeWinRate { get; set; }
    public double ProductWinRate { get; set; }
    public double SeriesWinRate { get; set; }
    public double AccountWinRate { get; set; }
    public double SectorWinRate { get; set; }
    public double RevenueBucketWinRate { get; set; }
    public double EmployeesBucketWinRate { get; set; }

    public int SalesAgentClosedN { get; set; }
    public int ProductClosedN { get; set; }
    public int AccountClosedN { get; set; }
    public int SectorClosedN { get; set; }

    public double MlWinProbability { get; set; }
    public double MlScore => MlWinProbability * 100d;
    public double HybridScore { get; set; }
    public double HybridExpectedValue { get; set; }
    public string MlBand { get; set; } = "ML não calculado";
    public string MlExplanation { get; set; } = string.Empty;

    public List<string> QualityNotes { get; set; } = new();
    public string WhyHighOrLow { get; set; } = string.Empty;
    public string MainRisks { get; set; } = string.Empty;
    public string NextBestAction { get; set; } = string.Empty;
}
