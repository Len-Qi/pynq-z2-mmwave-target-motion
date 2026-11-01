#include <iostream>
#include "radar_filter.h"

struct Outputs {
    int filtered_x, filtered_y, filtered_z, filtered_distance;
    int velocity_x, velocity_y, velocity_z, velocity_distance;
    unsigned int range_x, range_y, range_z, range_distance;
    unsigned int motion_score, valid;
};

void invoke(int x, int y, int z, int distance,
            unsigned int dt_ms, unsigned int reset, Outputs &out) {
    radar_filter(
        x, y, z, distance, dt_ms, reset,
        out.filtered_x, out.filtered_y, out.filtered_z,
        out.filtered_distance,
        out.velocity_x, out.velocity_y, out.velocity_z,
        out.velocity_distance,
        out.range_x, out.range_y, out.range_z, out.range_distance,
        out.motion_score, out.valid
    );
}

bool expect_equal(const char *name, int actual, int expected) {
    if (actual == expected) return true;
    std::cerr << name << actual << expected << std::endl;
    return false;
}

int main() {
    Outputs out = {};
    bool passed = true;
    invoke(0, 0, 0, 0, 100, 1, out);

    std::cout << "frame,fx,fy,fz,fd,vx,vy,vz,vd,rx,ry,rz,rd,score,valid"
              << std::endl;

    // The window becomes valid after ten filtered samples.
    for (int i = 0; i < 14; i++) {
        invoke(i * 100, i * 200, -i * 50, 2000 - i * 20,
               100, 0, out);
        std::cout
            << i << "," << out.filtered_x << "," << out.filtered_y
            << "," << out.filtered_z << "," << out.filtered_distance
            << "," << out.velocity_x << "," << out.velocity_y
            << "," << out.velocity_z << "," << out.velocity_distance
            << "," << out.range_x << "," << out.range_y
            << "," << out.range_z << "," << out.range_distance
            << "," << out.motion_score << "," << out.valid << std::endl;
        if (i < 13 && out.valid != 0) {
            passed = false;
        }
    }

    passed &= expect_equal("filtered_x", out.filtered_x, 1100);
    passed &= expect_equal("filtered_y", out.filtered_y, 2200);
    passed &= expect_equal("filtered_z", out.filtered_z, -550);
    passed &= expect_equal("filtered_distance", out.filtered_distance, 1780);
    passed &= expect_equal("velocity_x", out.velocity_x, 1000);
    passed &= expect_equal("velocity_y", out.velocity_y, 2000);
    passed &= expect_equal("velocity_z", out.velocity_z, -500);
    passed &= expect_equal("velocity_distance", out.velocity_distance, -200);
    passed &= expect_equal("range_x", (int)out.range_x, 900);
    passed &= expect_equal("range_y", (int)out.range_y, 1800);
    passed &= expect_equal("range_z", (int)out.range_z, 450);
    passed &= expect_equal("range_distance", (int)out.range_distance, 180);
    passed &= expect_equal("motion_score", (int)out.motion_score, 7030);
    passed &= expect_equal("valid", (int)out.valid, 1);

    // One extreme point must be rejected by the median filter.
    invoke(0, 0, 0, 0, 100, 1, out);
    int outlier_data[5] = {100, 101, 9999, 102, 103};
    for (int i = 0; i < 5; i++) {
        invoke(outlier_data[i], 0, 0, 1000, 100, 0, out);
    }
    passed &= expect_equal("outlier_filtered_x", out.filtered_x, 102);

    if (!passed) return 1;
    std::cout << "TEST_PASSED" << std::endl;
    return 0;
}
