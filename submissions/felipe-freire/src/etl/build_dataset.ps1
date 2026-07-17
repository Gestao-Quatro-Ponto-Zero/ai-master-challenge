param(
    [string]$InputPath = "data/raw/social_media_dataset.csv",
    [string]$OutputPath = "data/processed/posts_analytical.csv"
)

$ErrorActionPreference = "Stop"
$required = @(
    "id", "platform", "content_id", "creator_id", "content_type",
    "content_category", "post_date", "language", "content_length",
    "hashtags", "views", "likes", "shares", "comments_count",
    "follower_count", "is_sponsored", "disclosure_type", "sponsor_category",
    "disclosure_location", "audience_age_distribution",
    "audience_gender_distribution", "audience_location"
)

if (-not (Test-Path -LiteralPath $InputPath)) {
    throw "Input not found: $InputPath"
}

$rows = Import-Csv -LiteralPath $InputPath
if ($rows.Count -eq 0) { throw "Input is empty" }
$headers = @($rows[0].PSObject.Properties.Name)
$missingColumns = @($required | Where-Object { $_ -notin $headers })
if ($missingColumns.Count -gt 0) {
    throw "Missing required columns: $($missingColumns -join ', ')"
}

$ids = [Collections.Generic.HashSet[string]]::new()
$contentIds = [Collections.Generic.HashSet[string]]::new()
$output = [Collections.Generic.List[object]]::new()

foreach ($row in $rows) {
    if (-not $ids.Add($row.id)) { throw "Duplicate id: $($row.id)" }
    if (-not $contentIds.Add($row.content_id)) { throw "Duplicate content_id: $($row.content_id)" }

    $views = [long]$row.views
    $likes = [long]$row.likes
    $shares = [long]$row.shares
    $comments = [long]$row.comments_count
    $followers = [long]$row.follower_count
    $contentLength = [int]$row.content_length
    if ($views -le 0 -or $likes -lt 0 -or $shares -lt 0 -or $comments -lt 0 -or $followers -le 0) {
        throw "Invalid metric range at id=$($row.id)"
    }
    if ($likes -gt $views -or $shares -gt $views -or $comments -gt $views) {
        throw "Interaction exceeds views at id=$($row.id)"
    }

    $postDate = [datetime]::MinValue
    if (-not [datetime]::TryParse(
        $row.post_date,
        [Globalization.CultureInfo]::InvariantCulture,
        [Globalization.DateTimeStyles]::None,
        [ref]$postDate
    )) { throw "Invalid post_date at id=$($row.id)" }

    $sponsored = $row.is_sponsored -eq "TRUE"
    if ($sponsored -and ($row.sponsor_category -eq "Not sponsors" -or $row.disclosure_type -eq "none")) {
        throw "Sponsored metadata inconsistency at id=$($row.id)"
    }
    if (-not $sponsored -and ($row.sponsor_category -ne "Not sponsors" -or $row.disclosure_type -ne "none")) {
        throw "Organic metadata inconsistency at id=$($row.id)"
    }

    $engagementTotal = $likes + $shares + $comments
    $creatorSize = if ($followers -lt 10000) { "nano_lt_10k" }
        elseif ($followers -lt 50000) { "micro_10k_50k" }
        elseif ($followers -lt 100000) { "mid_50k_100k" }
        elseif ($followers -lt 500000) { "macro_100k_500k" }
        else { "mega_500k_plus" }
    $hashtagCount = if ([string]::IsNullOrWhiteSpace($row.hashtags)) { 0 }
        else { @($row.hashtags.Split(",") | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }).Count }

    $output.Add([pscustomobject][ordered]@{
        id                           = [long]$row.id
        content_id                   = $row.content_id
        creator_id                   = $row.creator_id
        platform                     = $row.platform
        content_type                 = $row.content_type
        content_category             = $row.content_category
        post_datetime                = $postDate.ToString("yyyy-MM-ddTHH:mm:ss")
        post_year                    = $postDate.Year
        post_month                   = $postDate.ToString("yyyy-MM")
        post_day_of_week             = $postDate.DayOfWeek.ToString().ToLowerInvariant()
        post_hour                    = $postDate.Hour
        language                     = $row.language
        content_length               = $contentLength
        hashtags                     = $row.hashtags
        hashtag_count                = $hashtagCount
        views                        = $views
        likes                        = $likes
        shares                       = $shares
        comments_count               = $comments
        follower_count               = $followers
        creator_size                 = $creatorSize
        is_sponsored                 = [int]$sponsored
        disclosure_type              = $row.disclosure_type
        sponsor_category             = $row.sponsor_category
        disclosure_location          = $row.disclosure_location
        audience_age_distribution    = $row.audience_age_distribution
        audience_gender_distribution = $row.audience_gender_distribution
        audience_location            = $row.audience_location
        engagement_total             = $engagementTotal
        engagement_rate_views        = ([math]::Round($engagementTotal / $views, 8)).ToString("0.00000000", [Globalization.CultureInfo]::InvariantCulture)
        like_rate_views              = ([math]::Round($likes / $views, 8)).ToString("0.00000000", [Globalization.CultureInfo]::InvariantCulture)
        share_rate_views             = ([math]::Round($shares / $views, 8)).ToString("0.00000000", [Globalization.CultureInfo]::InvariantCulture)
        comment_rate_views           = ([math]::Round($comments / $views, 8)).ToString("0.00000000", [Globalization.CultureInfo]::InvariantCulture)
        views_per_follower           = ([math]::Round($views / $followers, 8)).ToString("0.00000000", [Globalization.CultureInfo]::InvariantCulture)
    })
}

$outputDirectory = Split-Path -Parent $OutputPath
if ($outputDirectory) { New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null }
$output | Export-Csv -LiteralPath $OutputPath -NoTypeInformation -Encoding utf8

Write-Output "rows=$($output.Count)"
Write-Output "columns=$(@($output[0].PSObject.Properties.Name).Count)"
Write-Output "output=$OutputPath"
