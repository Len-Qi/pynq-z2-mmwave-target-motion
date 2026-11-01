#include "radar_filter.h"

namespace {

const unsigned int MEDIAN_SIZE = 5;
const unsigned int FEATURE_SIZE = 10;

int median5(const int input[MEDIAN_SIZE]) {
#pragma HLS INLINE
    int sorted[MEDIAN_SIZE];
#pragma HLS ARRAY_PARTITION variable=sorted complete

    for (unsigned int i = 0; i < MEDIAN_SIZE; i++) {
#pragma HLS UNROLL
        sorted[i] = input[i];
    }

    for (unsigned int i = 0; i < MEDIAN_SIZE - 1; i++) {
#pragma HLS UNROLL
        for (unsigned int j = i + 1; j < MEDIAN_SIZE; j++) {
#pragma HLS UNROLL
            if (sorted[j] < sorted[i]) {
                int temp = sorted[i];
                sorted[i] = sorted[j];
                sorted[j] = temp;
            }
        }
    }
    return sorted[MEDIAN_SIZE / 2];
}

unsigned int absolute_value(int value) {
#pragma HLS INLINE
    return value < 0 ? (unsigned int)(-value) : (unsigned int)value;
}

unsigned int window_range(
    const int input[FEATURE_SIZE],
    unsigned int count
) {
#pragma HLS INLINE
    int minimum = input[0];
    int maximum = input[0];

    for (unsigned int i = 1; i < FEATURE_SIZE; i++) {
#pragma HLS UNROLL
        if (i < count) {
            if (input[i] < minimum) {
                minimum = input[i];
            }
            if (input[i] > maximum) {
                maximum = input[i];
            }
        }
    }
    return (unsigned int)(maximum - minimum);
}

}  // namespace

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
) {
#pragma HLS INTERFACE mode=s_axilite port=x_mm bundle=CTRL
#pragma HLS INTERFACE mode=s_axilite port=y_mm bundle=CTRL
#pragma HLS INTERFACE mode=s_axilite port=z_mm bundle=CTRL
#pragma HLS INTERFACE mode=s_axilite port=distance_mm bundle=CTRL
#pragma HLS INTERFACE mode=s_axilite port=dt_ms bundle=CTRL
#pragma HLS INTERFACE mode=s_axilite port=reset_state bundle=CTRL
#pragma HLS INTERFACE mode=s_axilite port=filtered_x_mm bundle=CTRL
#pragma HLS INTERFACE mode=s_axilite port=filtered_y_mm bundle=CTRL
#pragma HLS INTERFACE mode=s_axilite port=filtered_z_mm bundle=CTRL
#pragma HLS INTERFACE mode=s_axilite port=filtered_distance_mm bundle=CTRL
#pragma HLS INTERFACE mode=s_axilite port=velocity_x_mm_s bundle=CTRL
#pragma HLS INTERFACE mode=s_axilite port=velocity_y_mm_s bundle=CTRL
#pragma HLS INTERFACE mode=s_axilite port=velocity_z_mm_s bundle=CTRL
#pragma HLS INTERFACE mode=s_axilite port=velocity_distance_mm_s bundle=CTRL
#pragma HLS INTERFACE mode=s_axilite port=range_x_mm bundle=CTRL
#pragma HLS INTERFACE mode=s_axilite port=range_y_mm bundle=CTRL
#pragma HLS INTERFACE mode=s_axilite port=range_z_mm bundle=CTRL
#pragma HLS INTERFACE mode=s_axilite port=range_distance_mm bundle=CTRL
#pragma HLS INTERFACE mode=s_axilite port=motion_score bundle=CTRL
#pragma HLS INTERFACE mode=s_axilite port=valid bundle=CTRL
#pragma HLS INTERFACE mode=s_axilite port=return bundle=CTRL

    static int median_x[MEDIAN_SIZE];
    static int median_y[MEDIAN_SIZE];
    static int median_z[MEDIAN_SIZE];
    static int median_distance[MEDIAN_SIZE];
    static unsigned int median_index = 0;
    static unsigned int median_count = 0;

    static int feature_x[FEATURE_SIZE];
    static int feature_y[FEATURE_SIZE];
    static int feature_z[FEATURE_SIZE];
    static int feature_distance[FEATURE_SIZE];
    static unsigned int feature_index = 0;
    static unsigned int feature_count = 0;

    static int previous_x = 0;
    static int previous_y = 0;
    static int previous_z = 0;
    static int previous_distance = 0;
    static unsigned int previous_valid = 0;

#pragma HLS ARRAY_PARTITION variable=median_x complete
#pragma HLS ARRAY_PARTITION variable=median_y complete
#pragma HLS ARRAY_PARTITION variable=median_z complete
#pragma HLS ARRAY_PARTITION variable=median_distance complete
#pragma HLS ARRAY_PARTITION variable=feature_x complete
#pragma HLS ARRAY_PARTITION variable=feature_y complete
#pragma HLS ARRAY_PARTITION variable=feature_z complete
#pragma HLS ARRAY_PARTITION variable=feature_distance complete

    if (reset_state != 0) {
        for (unsigned int i = 0; i < MEDIAN_SIZE; i++) {
#pragma HLS UNROLL
            median_x[i] = 0;
            median_y[i] = 0;
            median_z[i] = 0;
            median_distance[i] = 0;
        }
        for (unsigned int i = 0; i < FEATURE_SIZE; i++) {
#pragma HLS UNROLL
            feature_x[i] = 0;
            feature_y[i] = 0;
            feature_z[i] = 0;
            feature_distance[i] = 0;
        }

        median_index = 0;
        median_count = 0;
        feature_index = 0;
        feature_count = 0;
        previous_x = 0;
        previous_y = 0;
        previous_z = 0;
        previous_distance = 0;
        previous_valid = 0;

        filtered_x_mm = 0;
        filtered_y_mm = 0;
        filtered_z_mm = 0;
        filtered_distance_mm = 0;
        velocity_x_mm_s = 0;
        velocity_y_mm_s = 0;
        velocity_z_mm_s = 0;
        velocity_distance_mm_s = 0;
        range_x_mm = 0;
        range_y_mm = 0;
        range_z_mm = 0;
        range_distance_mm = 0;
        motion_score = 0;
        valid = 0;
        return;
    }

    median_x[median_index] = x_mm;
    median_y[median_index] = y_mm;
    median_z[median_index] = z_mm;
    median_distance[median_index] = distance_mm;
    median_index++;
    if (median_index == MEDIAN_SIZE) {
        median_index = 0;
    }
    if (median_count < MEDIAN_SIZE) {
        median_count++;
    }

    if (median_count < MEDIAN_SIZE) {
        filtered_x_mm = x_mm;
        filtered_y_mm = y_mm;
        filtered_z_mm = z_mm;
        filtered_distance_mm = distance_mm;
        velocity_x_mm_s = 0;
        velocity_y_mm_s = 0;
        velocity_z_mm_s = 0;
        velocity_distance_mm_s = 0;
        range_x_mm = 0;
        range_y_mm = 0;
        range_z_mm = 0;
        range_distance_mm = 0;
        motion_score = 0;
        valid = 0;
        return;
    }

    filtered_x_mm = median5(median_x);
    filtered_y_mm = median5(median_y);
    filtered_z_mm = median5(median_z);
    filtered_distance_mm = median5(median_distance);

    if ((previous_valid != 0) && (dt_ms != 0)) {
        velocity_x_mm_s =
            (filtered_x_mm - previous_x) * 1000 / (int)dt_ms;
        velocity_y_mm_s =
            (filtered_y_mm - previous_y) * 1000 / (int)dt_ms;
        velocity_z_mm_s =
            (filtered_z_mm - previous_z) * 1000 / (int)dt_ms;
        velocity_distance_mm_s =
            (filtered_distance_mm - previous_distance) * 1000 / (int)dt_ms;
    } else {
        velocity_x_mm_s = 0;
        velocity_y_mm_s = 0;
        velocity_z_mm_s = 0;
        velocity_distance_mm_s = 0;
    }

    previous_x = filtered_x_mm;
    previous_y = filtered_y_mm;
    previous_z = filtered_z_mm;
    previous_distance = filtered_distance_mm;
    previous_valid = 1;

    feature_x[feature_index] = filtered_x_mm;
    feature_y[feature_index] = filtered_y_mm;
    feature_z[feature_index] = filtered_z_mm;
    feature_distance[feature_index] = filtered_distance_mm;
    feature_index++;
    if (feature_index == FEATURE_SIZE) {
        feature_index = 0;
    }
    if (feature_count < FEATURE_SIZE) {
        feature_count++;
    }

    range_x_mm = window_range(feature_x, feature_count);
    range_y_mm = window_range(feature_y, feature_count);
    range_z_mm = window_range(feature_z, feature_count);
    range_distance_mm = window_range(feature_distance, feature_count);

    motion_score =
        absolute_value(velocity_x_mm_s) +
        absolute_value(velocity_y_mm_s) +
        absolute_value(velocity_z_mm_s) +
        absolute_value(velocity_distance_mm_s) +
        range_x_mm + range_y_mm + range_z_mm + range_distance_mm;

    valid = feature_count == FEATURE_SIZE ? 1 : 0;
}
