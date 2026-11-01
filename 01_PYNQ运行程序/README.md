# PYNQ-Z2 板端运行说明

本目录是最终演示程序，只完成两个可验证功能：

- LED3：检测到至少一个有效人体目标时点亮。
- LED2：至少一个目标被判定为持续运动时点亮。
- LED1、LED0：程序强制保持熄灭。

## 文件说明

- `live_target_motion_demo.py`：最终运行入口。
- `fpga_radar_core.py`：LD6004 数据解析与 FPGA MMIO 调用。
- `motion_core.py`：独立目标轨迹的运动状态判定。
- `target_windows.py`：按 cluster_id 分开保存各目标窗口。
- `led_status.py`：LED 状态输出，低两位永久清零。
- `radar_filter_v3.bit/.hwh`：PYNQ Overlay。

## 上传与运行

把整个目录上传到 PYNQ，例如：

`/home/xilinx/jupyter_notebooks/target_motion_demo`

打开 MobaXterm 或 Jupyter Terminal，执行：

```bash
cd /home/xilinx/jupyter_notebooks/target_motion_demo
pip3 install pyserial
sudo bash run_demo.sh
```

如果雷达串口不是 `/dev/ttyUSB0`，直接执行：

```bash
sudo python3 live_target_motion_demo.py --device /dev/ttyUSB1
```

停止程序按 `Ctrl+C`，退出时程序自动关闭四颗 LED。

## 演示顺序

1. 雷达前无人：LED3、LED2 均灭。
2. 人进入并静止约 3 秒：LED3 亮、LED2 灭。
3. 人连续走动约 3 秒：LED3、LED2均亮。
4. 人离开雷达区域：约 1.5 秒后两灯熄灭。

本版本不包含姿态分类或跌倒识别，请勿在演示和文档中作此声明。
