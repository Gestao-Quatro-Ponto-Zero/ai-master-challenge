# Data QA Report

- Dataset: `/Users/lenon/Downloads/social_media_dataset.csv`
- Valid rows: **52214**
- Parse errors: **0**
- Date range: **2023-05-29 00:15:00** to **2025-05-28 11:08:00**

## Coverage

- Platforms: {'RedNote': 10402, 'Bilibili': 10598, 'YouTube': 10495, 'TikTok': 10296, 'Instagram': 10423}
- Content types: {'video': 31500, 'image': 10303, 'mixed': 5213, 'text': 5198}
- Categories: {'beauty': 21023, 'lifestyle': 20761, 'tech': 10430}
- Sponsored split: {'FALSE': 29900, 'TRUE': 22314}

## Critical constraints found

- `engagement_rate` is not present in source file and was derived as `(likes + shares + comments_count) / views`.
- No absolute zero values were found in `views`, `likes`, `shares`, `comments_count`.
- This pattern indicates low natural variance and potential synthetic behavior; interpretation must avoid overclaim.

## Zero checks

- {'views_zero': 0, 'likes_zero': 0, 'shares_zero': 0, 'comments_zero': 0, 'interactions_zero': 0}

## Near-zero proxy (distribution tail)

- p10 ERR: 0.19283529 (5222 posts, 10.00%)
- p25 ERR: 0.19575824 (13054 posts, 25.00%)
- p10 share_rate: 0.02749511 (5222 posts, 10.00%)
- p25 share_rate: 0.02852050 (13054 posts, 25.00%)

## Platform baseline means

- Bilibili: mean ERR=0.19908496, mean share_rate=0.02971551, mean views=10099.93, mean reach/follower=0.07140895
- Instagram: mean ERR=0.19899251, mean share_rate=0.02972207, mean views=10100.35, mean reach/follower=0.06703264
- RedNote: mean ERR=0.19909762, mean share_rate=0.02968549, mean views=10100.78, mean reach/follower=0.06899092
- TikTok: mean ERR=0.19906017, mean share_rate=0.02969084, mean views=10100.59, mean reach/follower=0.07428006
- YouTube: mean ERR=0.19903720, mean share_rate=0.02972063, mean views=10099.78, mean reach/follower=0.06504909
