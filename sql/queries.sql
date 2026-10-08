-- Question: What does the long-term May extent series look like?
SELECT *
FROM ice_extent_long_term
ORDER BY year;

-- Question: How has extent changed decade over decade?
SELECT
    (year / 10) * 10 AS decade,
    ROUND(AVG(extent_million_km2), 3) AS avg_extent,
    COUNT(*) AS n_years
FROM ice_extent_long_term
GROUP BY decade
ORDER BY decade;

-- Question: What is the year-over-year change in extent (moving trend)?
SELECT
    year,
    extent_million_km2,
    extent_million_km2 - LAG(extent_million_km2) OVER (ORDER BY year) AS change_from_prior_year
FROM ice_extent_long_term
ORDER BY year;

-- Question: In the 2015-2020 window, how do extent and traffic rank together?
SELECT
    year,
    extent_million_km2,
    total_traffic,
    RANK() OVER (ORDER BY extent_million_km2 ASC) AS extent_rank_lowest_first,
    RANK() OVER (ORDER BY total_traffic DESC) AS traffic_rank_highest_first
FROM ice_extent_vs_traffic
ORDER BY year;

-- Question: Which vessel type grew the most between 2015 and 2020?
SELECT
    'Cargo' AS vessel_type,
    MAX(CASE WHEN year = 2020 THEN Cargo END) - MAX(CASE WHEN year = 2015 THEN Cargo END) AS change_2015_2020
FROM ice_extent_vs_traffic
UNION ALL
SELECT
    'Fishing',
    MAX(CASE WHEN year = 2020 THEN Fishing END) - MAX(CASE WHEN year = 2015 THEN Fishing END)
FROM ice_extent_vs_traffic
UNION ALL
SELECT
    'Tanker',
    MAX(CASE WHEN year = 2020 THEN Tanker END) - MAX(CASE WHEN year = 2015 THEN Tanker END)
FROM ice_extent_vs_traffic
UNION ALL
SELECT
    'Other',
    MAX(CASE WHEN year = 2020 THEN Other END) - MAX(CASE WHEN year = 2015 THEN Other END)
FROM ice_extent_vs_traffic;

-- Question: What does the recent (2020-2026) regional ice age composition look like?
SELECT
    year,
    ROUND(mean_siage, 4) AS mean_siage,
    ROUND(conc_1yi, 4) AS conc_1yi,
    ROUND(conc_6yi, 4) AS conc_6yi
FROM ice_age_recent
ORDER BY year;

-- Question: Has the youngest ice category (1-year) grown or shrunk since 2020, regionally?
SELECT
    year,
    conc_1yi,
    conc_1yi - LAG(conc_1yi) OVER (ORDER BY year) AS change_from_prior_year
FROM ice_age_recent
ORDER BY year;