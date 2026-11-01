#ifndef RADAR_FILTER_H
#define RADAR_FILTER_H

void radar_filter(
    int x_mm,
    int y_mm,
    int z_mm,
    int distance_mm,
    unsigned int dt_ms,
    unsigned int reset_state,
    int &filtered_x_mm,
    int &filtered_y_mm,
    int &filtered_z_mm,
    int &filtered_distance_mm,
    int &velocity_x_mm_s,
    int &velocity_y_mm_s,
    int &velocity_z_mm_s,
    int &velocity_distance_mm_s,
    unsigned int &range_x_mm,
    unsigned int &range_y_mm,
    unsigned int &range_z_mm,
    unsigned int &range_distance_mm,
    unsigned int &motion_score,
    unsigned int &valid
);

#endif
