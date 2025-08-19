# Delhivery Trip Data Analysis Report
## Problem Statement
Delhivery aims to optimize package delivery by comparing actual delivery metrics with system-generated estimates. This
analysis helps uncover inefficiencies, delay patterns, and routing inaccuracies.
## Exploratory Data Analysis (EDA)
- Total rows: 144,867
- Categorical features: route_type, source_name, destination_name
- Missing values found in source_name and destination_name; filled using mode.
- Data types optimized for analysis.
## Feature Engineering
- Extracted city/state from source/destination names
- Derived trip_month, trip_day, trip_year from timestamps
- Calculated trip_duration_hours and od_duration
- Aggregated trip-level stats by trip_uuid.
## Statistical Tests and Visual Analysis
- Wilcoxon tests show significant difference in:
- actual_time vs osrm_time
- actual_time vs segment_actual_time
- osrm_time vs segment_osrm_time
- osrm_distance vs segment_osrm_distance
- KDE and box plots reveal right-skewed distributions and bias.
## Outlier Detection and Treatment
- Outliers found in actual_time, osrm_time, segment_actual_time, osrm_distance
- IQR method applied to remove extreme values
- Distributions smoothed post-treatment.
## Encoding and Scaling
- One-hot encoded route_type and state columns
- StandardScaler applied to numerical fields for modeling.
## Business Insights
- Gurgaon_Bilaspur_HB is the top destination center
- Average delay from actual vs OSRM time is 203 mins
- Segment-level logging underestimates true performance
- OD duration is more reliable than scan-to-scan.
## Recommendations
- Improve OSRM route calibration
- Rely on full OD duration, not scan durations
## Delhivery Trip Data Analysis Report
- Audit segment-level time logging
- Focus on high-delay corridors for performance improvements
- Use dashboards for real-time monitoring.
