from typing import Any, Dict, List, Optional

SQL_QUERIES_CATALOGUE: Dict[str, Dict[str, Any]] = {
    "query_01_total_reports": {
        "id": "query_01_total_reports",
        "title": "Total Found-Item Reports",
        "category": "Basic Aggregation",
        "concept": "COUNT(*)",
        "description": "Calculates the total count of found-item reports submitted to the campus database.",
        "sql_text": "SELECT COUNT(*) AS total_reports FROM found_items;",
        "default_params": {},
    },
    "query_02_available_items": {
        "id": "query_02_available_items",
        "title": "Currently Available Unclaimed Items",
        "category": "Filtering & Selection",
        "concept": "WHERE Clause",
        "description": "Filters items that are still active and available for claiming by campus members.",
        "sql_text": "SELECT COUNT(*) AS available_items FROM found_items WHERE status = 'available';",
        "default_params": {},
    },
    "query_03_category_distribution": {
        "id": "query_03_category_distribution",
        "title": "Found-Item Count Grouped by Category",
        "category": "Grouping & Aggregation",
        "concept": "LEFT JOIN & GROUP BY",
        "description": "Aggregates found-item report counts per category.",
        "sql_text": """SELECT 
    c.id AS category_id,
    c.name AS category_name,
    COUNT(f.id) AS total_items,
    SUM(CASE WHEN f.status = 'available' THEN 1 ELSE 0 END) AS available_items,
    SUM(CASE WHEN f.status = 'returned' THEN 1 ELSE 0 END) AS returned_items
FROM categories c
LEFT JOIN found_items f ON c.id = f.category_id
GROUP BY c.id, c.name
ORDER BY total_items DESC;""",
        "default_params": {},
    },
    "query_04_location_distribution": {
        "id": "query_04_location_distribution",
        "title": "Found-Item Count Grouped by Campus Location",
        "category": "Grouping & Aggregation",
        "concept": "LEFT JOIN, GROUP BY & ORDER BY",
        "description": "Identifies campus hotspot zones where found items are most frequently reported.",
        "sql_text": """SELECT 
    l.id AS location_id,
    l.name AS location_name,
    l.building_or_area,
    COUNT(f.id) AS item_count
FROM campus_locations l
LEFT JOIN found_items f ON l.id = f.location_id
GROUP BY l.id, l.name, l.building_or_area
ORDER BY item_count DESC;""",
        "default_params": {},
    },
    "query_05_recent_reports": {
        "id": "query_05_recent_reports",
        "title": "Most Recently Reported Items",
        "category": "Sorting & Limiting",
        "concept": "ORDER BY & LIMIT",
        "description": "Retrieves the newest found-item records with location and category information.",
        "sql_text": """SELECT 
    f.reference_code,
    f.title,
    c.name AS category_name,
    l.name AS location_name,
    f.status,
    f.found_at
FROM found_items f
JOIN categories c ON f.category_id = c.id
JOIN campus_locations l ON f.location_id = l.id
ORDER BY f.found_at DESC
LIMIT :limit;""",
        "default_params": {"limit": 15},
    },
    "query_06_listings_with_reporters": {
        "id": "query_06_listings_with_reporters",
        "title": "Listings with Reporter Display Info",
        "category": "Relational JOINs",
        "concept": "INNER JOIN users to found_items",
        "description": "Demonstrates relational navigation between user accounts and their found-item reports.",
        "sql_text": """SELECT 
    f.reference_code,
    f.title,
    u.full_name AS reporter_name,
    u.department AS reporter_department,
    f.found_at,
    f.status
FROM found_items f
INNER JOIN users u ON f.reporter_id = u.id
ORDER BY f.created_at DESC
LIMIT :limit;""",
        "default_params": {"limit": 15},
    },
    "query_07_full_item_taxonomy": {
        "id": "query_07_full_item_taxonomy",
        "title": "Listings with Category, Subcategory & Location",
        "category": "Multi-Table JOINs",
        "concept": "Multiple INNER & LEFT JOINs",
        "description": "Combines four related tables into a unified taxonomy view of item reports.",
        "sql_text": """SELECT 
    f.reference_code,
    f.title,
    c.name AS category,
    COALESCE(s.name, 'N/A') AS subcategory,
    l.name AS location,
    l.building_or_area,
    f.condition,
    f.status
FROM found_items f
JOIN categories c ON f.category_id = c.id
LEFT JOIN subcategories s ON f.subcategory_id = s.id
JOIN campus_locations l ON f.location_id = l.id
ORDER BY f.id DESC
LIMIT :limit;""",
        "default_params": {"limit": 20},
    },
    "query_08_enquiry_count_per_listing": {
        "id": "query_08_enquiry_count_per_listing",
        "title": "Contact Requests per Item",
        "category": "Aggregation with JOINs",
        "concept": "LEFT JOIN, COUNT & HAVING",
        "description": "Finds listings that have generated interest through in-app contact enquiries.",
        "sql_text": """SELECT 
    f.reference_code,
    f.title,
    f.status,
    c.name AS category_name,
    COUNT(cr.id) AS total_enquiries
FROM found_items f
JOIN categories c ON f.category_id = c.id
LEFT JOIN contact_requests cr ON f.id = cr.item_id
GROUP BY f.id, f.reference_code, f.title, f.status, c.name
HAVING total_enquiries > 0
ORDER BY total_enquiries DESC
LIMIT :limit;""",
        "default_params": {"limit": 15},
    },
    "query_09_categories_threshold": {
        "id": "query_09_categories_threshold",
        "title": "High-Volume Categories (HAVING Filter)",
        "category": "Filtered Aggregates",
        "concept": "HAVING Clause",
        "description": "Applies a post-aggregation filter to identify categories with at least N reports.",
        "sql_text": """SELECT 
    c.name AS category_name,
    COUNT(f.id) AS item_count
FROM categories c
JOIN found_items f ON c.id = f.category_id
GROUP BY c.id, c.name
HAVING item_count >= :min_count
ORDER BY item_count DESC;""",
        "default_params": {"min_count": 15},
    },
    "query_10_above_average_reporters": {
        "id": "query_10_above_average_reporters",
        "title": "Users Reporting Above-Average Items",
        "category": "Subqueries & Advanced Analytics",
        "concept": "Scalar Subquery in HAVING",
        "description": "Demonstrates nested SQL: filters users whose found-item report count exceeds the campus average.",
        "sql_text": """SELECT 
    u.id AS user_id,
    u.full_name,
    u.department,
    COUNT(f.id) AS report_count
FROM users u
JOIN found_items f ON u.id = f.reporter_id
GROUP BY u.id, u.full_name, u.department
HAVING COUNT(f.id) > (
    SELECT AVG(user_totals.cnt)
    FROM (
        SELECT COUNT(id) AS cnt
        FROM found_items
        GROUP BY reporter_id
    ) AS user_totals
)
ORDER BY report_count DESC;""",
        "default_params": {},
    },
    "query_11_monthly_trends": {
        "id": "query_11_monthly_trends",
        "title": "Monthly Found-Item Reporting Trend",
        "category": "Date & Time Functions",
        "concept": "DATE_FORMAT & GROUP BY",
        "description": "Summarizes found-item report volume by calendar month to observe seasonal patterns.",
        "sql_text": """SELECT 
    DATE_FORMAT(found_at, '%Y-%m') AS report_month,
    COUNT(id) AS total_reports,
    SUM(CASE WHEN status = 'returned' THEN 1 ELSE 0 END) AS returned_count
FROM found_items
GROUP BY report_month
ORDER BY report_month ASC;""",
        "default_params": {},
    },
    "query_12_status_breakdown": {
        "id": "query_12_status_breakdown",
        "title": "Listing Resolution Rate & Breakdown",
        "category": "Percentages & Distribution",
        "concept": "Subquery Expression & Math",
        "description": "Shows the breakdown between available, returned, and removed items with live percentages.",
        "sql_text": """SELECT 
    status,
    COUNT(*) AS total_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM found_items), 2) AS percentage_of_total
FROM found_items
GROUP BY status
ORDER BY total_count DESC;""",
        "default_params": {},
    },
    "query_13_subcategory_counts": {
        "id": "query_13_subcategory_counts",
        "title": "Subcategory-Level Granular Breakdown",
        "category": "Hierarchical Aggregation",
        "concept": "JOIN 3 Tables with GROUP BY",
        "description": "Provides granular item counts across subcategories alongside their parent category.",
        "sql_text": """SELECT 
    c.name AS category_name,
    s.name AS subcategory_name,
    COUNT(f.id) AS item_count
FROM subcategories s
JOIN categories c ON s.category_id = c.id
LEFT JOIN found_items f ON s.id = f.subcategory_id
GROUP BY c.name, s.name
ORDER BY item_count DESC
LIMIT :limit;""",
        "default_params": {"limit": 20},
    },
    "query_14_uncontacted_available_items": {
        "id": "query_14_uncontacted_available_items",
        "title": "Available Items Without Enquiries",
        "category": "Outer JOIN Filtering",
        "concept": "LEFT JOIN & IS NULL",
        "description": "Finds available listings that have received 0 contact enquiries so far.",
        "sql_text": """SELECT 
    f.reference_code,
    f.title,
    c.name AS category_name,
    l.name AS location_name,
    f.found_at
FROM found_items f
JOIN categories c ON f.category_id = c.id
JOIN campus_locations l ON f.location_id = l.id
LEFT JOIN contact_requests cr ON f.id = cr.item_id
WHERE cr.id IS NULL AND f.status = 'available'
ORDER BY f.found_at DESC
LIMIT :limit;""",
        "default_params": {"limit": 20},
    },
    "query_15_top_contributors": {
        "id": "query_15_top_contributors",
        "title": "Top Campus Good Samaritans",
        "category": "Ranking & Analytics",
        "concept": "JOIN, GROUP BY & ORDER BY",
        "description": "Ranks campus community members who have submitted the highest number of found-item reports.",
        "sql_text": """SELECT 
    u.id AS user_id,
    u.full_name,
    u.department,
    COUNT(f.id) AS items_reported,
    SUM(CASE WHEN f.status = 'returned' THEN 1 ELSE 0 END) AS items_successfully_returned
FROM users u
JOIN found_items f ON u.id = f.reporter_id
GROUP BY u.id, u.full_name, u.department
ORDER BY items_reported DESC
LIMIT 10;""",
        "default_params": {},
    },
    "query_16_multiple_images": {
        "id": "query_16_multiple_images",
        "title": "Found Items with Multiple Photographs",
        "category": "Relational Aggregates",
        "concept": "JOIN with HAVING > 1",
        "description": "Finds listings where the reporter provided multiple photographic angles.",
        "sql_text": """SELECT 
    f.reference_code,
    f.title,
    c.name AS category_name,
    COUNT(img.id) AS photograph_count
FROM found_items f
JOIN categories c ON f.category_id = c.id
JOIN item_images img ON f.id = img.item_id
GROUP BY f.id, f.reference_code, f.title, c.name
HAVING photograph_count > 1
ORDER BY photograph_count DESC, f.id DESC;""",
        "default_params": {},
    },
    "query_17_contact_status_summary": {
        "id": "query_17_contact_status_summary",
        "title": "Enquiry Request Status Funnel",
        "category": "Workflow Metrics",
        "concept": "GROUP BY on Status",
        "description": "Categorizes contact enquiries across 'new', 'read', and 'closed' states.",
        "sql_text": """SELECT 
    status AS enquiry_status,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM contact_requests), 2) AS percentage
FROM contact_requests
GROUP BY status
ORDER BY count DESC;""",
        "default_params": {},
    },
    "query_18_old_unclaimed_items": {
        "id": "query_18_old_unclaimed_items",
        "title": "Long-Term Unclaimed Available Items",
        "category": "Date Arithmetic",
        "concept": "DATEDIFF(NOW(), date)",
        "description": "Identifies available found items that have remained unclaimed for more than N days.",
        "sql_text": """SELECT 
    f.reference_code,
    f.title,
    c.name AS category_name,
    l.name AS location_name,
    f.found_at,
    DATEDIFF(NOW(), f.found_at) AS days_unclaimed
FROM found_items f
JOIN categories c ON f.category_id = c.id
JOIN campus_locations l ON f.location_id = l.id
WHERE f.status = 'available'
  AND DATEDIFF(NOW(), f.found_at) >= :min_days
ORDER BY days_unclaimed DESC
LIMIT :limit;""",
        "default_params": {"min_days": 14, "limit": 20},
    },
    "query_19_active_items_view": {
        "id": "query_19_active_items_view",
        "title": "Demonstration: View 'v_active_found_items'",
        "category": "MySQL Views",
        "concept": "Querying Database Views",
        "description": "Reads directly from the pre-compiled MySQL View joining categories, locations, and reporters.",
        "sql_text": """SELECT 
    reference_code,
    title,
    category_name,
    subcategory_name,
    location_name,
    reporter_name,
    found_at
FROM v_active_found_items
ORDER BY found_at DESC
LIMIT :limit;""",
        "default_params": {"limit": 15},
    },
    "query_20_category_summary_view": {
        "id": "query_20_category_summary_view",
        "title": "Demonstration: View 'v_category_listing_summary'",
        "category": "MySQL Views",
        "concept": "Summary View Aggregation",
        "description": "Queries the database view summarizing item resolution rates per category.",
        "sql_text": """SELECT 
    category_name,
    total_items,
    available_items,
    returned_items,
    removed_items
FROM v_category_listing_summary
ORDER BY total_items DESC;""",
        "default_params": {},
    },
}
