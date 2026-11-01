# PYNQ-Z2 毫米波雷达人体目标存在与运动感知系统

基于 AMD Zynq FPGA、PYNQ-Z2 与 HLK-LD6004 毫米波雷达的无视觉、多目标人体感知作品。系统读取雷达输出的目标信息，在 ARM 端完成串口协议解析与多目标状态管理，并通过 FPGA 可编程逻辑完成中值滤波、速度特征和滑动窗口特征计算。

本仓库对应比赛最终提交版本，功能范围如下：

| 板载 LED | 含义 |
| --- | --- |
| LED3 | 检测到至少一个有效目标 |
| LED2 | 检测到至少一个持续运动目标 |
| LED1 | 保持关闭，最终版本未使用 |
| LED0 | 保持关闭，最终版本未使用 |

> 说明：最终版本不包含跌倒识别或人体姿态识别，不应将本项目用于安全关键报警。

## 系统组成

- PYNQ-Z2（Zynq-7000）开发板
- HLK-LD6004 毫米波雷达
- 串口数据链路
- ARM/PS：串口接收、协议解析、多目标管理与状态机
- FPGA/PL：滤波及运动特征加速
- PYNQ Overlay：BIT + HWH

## 快速运行

将 `01_PYNQ运行程序` 上传到 PYNQ-Z2 后，在板端执行：

```bash
cd /home/xilinx/jupyter_notebooks/target_motion_demo
pip3 install -r requirements.txt
sudo bash run_demo.sh
```

请先根据实际连接确认串口设备、波特率以及雷达供电。运行程序会把最终状态映射到板载 LED，输出值只使用高两位：

```python
((present << 3) | (moving << 2)) & 0xC
```

## 目录结构

- `01_PYNQ运行程序`：板端完整运行程序、启动脚本及 Overlay
- `02_FPGA_HLS源码`：HLS 算法源代码与 C++ 测试平台
- `03_Vivado脚本约束与报告`：工程脚本、引脚约束、地址表和实现报告
- `04_Overlay`：BIT、HWH、XSA 硬件交付文件
- `05_测试`：最终软件逻辑测试
- `docs/technical_document_zh.pdf`：中文技术文档

## FPGA 实现结果

- PL 时钟：100 MHz
- Filter IP 地址：`0x40000000`
- AXI GPIO 地址：`0x41200000`
- Slice LUT：8444 / 53200（15.87%）
- Slice Register：7235 / 106400（6.80%）
- BRAM：0
- DSP：0
- WNS：0.228 ns
- TNS：0 ns

实现报告中的 `RTSTAT-10 No routable loads` 为警告，已在技术文档中如实记录；最终实现时序约束满足。

## 验证范围

- Python 源码语法检查
- 串口目标数据解析
- 无目标、目标静止、目标运动状态逻辑
- LED 输出位约束：LED1 与 LED0 不会被软件置位
- Vivado 实现后的时序与资源报告

## License

本项目采用 [MIT License](LICENSE)。第三方硬件、工具与依赖仍遵循各自许可。
