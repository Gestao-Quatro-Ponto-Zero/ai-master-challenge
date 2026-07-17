param([string]$DatasetPath = "data/processed/posts_analytical.csv")

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $DatasetPath)) { throw "Processed dataset not found" }
$rows = Import-Csv -LiteralPath $DatasetPath
if ($rows.Count -ne 52214) { throw "Expected 52214 rows, got $($rows.Count)" }

$required = @(
    "id", "content_id", "creator_id", "platform", "post_datetime",
    "creator_size", "engagement_total", "engagement_rate_views",
    "share_rate_views", "views_per_follower"
)
$headers = @($rows[0].PSObject.Properties.Name)
foreach ($column in $required) {
    if ($column -notin $headers) { throw "Missing output column: $column" }
}

$ids = [Collections.Generic.HashSet[string]]::new()
$contentIds = [Collections.Generic.HashSet[string]]::new()
foreach ($row in $rows) {
    if (-not $ids.Add($row.id)) { throw "Duplicate id: $($row.id)" }
    if (-not $contentIds.Add($row.content_id)) { throw "Duplicate content_id: $($row.content_id)" }
    $rate = [double]::Parse($row.engagement_rate_views, [Globalization.CultureInfo]::InvariantCulture)
    if ($rate -le 0 -or $rate -gt 1) { throw "Engagement rate out of bounds at id=$($row.id)" }
    if ($row.is_sponsored -notin @("0", "1")) { throw "Invalid sponsor flag at id=$($row.id)" }
    if ([string]::IsNullOrWhiteSpace($row.post_datetime)) { throw "Missing post datetime at id=$($row.id)" }
}

$sample = $rows[0]
$expected = ([long]$sample.likes + [long]$sample.shares + [long]$sample.comments_count)
if ([long]$sample.engagement_total -ne $expected) { throw "Engagement total reconciliation failed" }

Write-Output "PASS rows=$($rows.Count) columns=$($headers.Count)"
