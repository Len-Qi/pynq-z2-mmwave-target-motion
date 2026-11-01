# PYNQ-Z2 user LEDs. Pinout verified against the Xilinx PYNQ board sources.
# The V3 AXI GPIO external interface is named alarm_led, therefore the
# generated top-level output bus is alarm_led_tri_o[3:0].

set_property -dict { PACKAGE_PIN R14 IOSTANDARD LVCMOS33 } [get_ports { alarm_led_tri_o[0] }]
set_property -dict { PACKAGE_PIN P14 IOSTANDARD LVCMOS33 } [get_ports { alarm_led_tri_o[1] }]
set_property -dict { PACKAGE_PIN N16 IOSTANDARD LVCMOS33 } [get_ports { alarm_led_tri_o[2] }]
set_property -dict { PACKAGE_PIN M14 IOSTANDARD LVCMOS33 } [get_ports { alarm_led_tri_o[3] }]

