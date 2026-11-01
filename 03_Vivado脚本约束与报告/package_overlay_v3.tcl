set project_file [file normalize {vivado/radar_system_v3/radar_system_v3.xpr}]
set impl_dir [file normalize {vivado/radar_system_v3/radar_system_v3.runs/impl_1}]
set routed_dcp [file join $impl_dir radar_system_v3_wrapper_routed.dcp]
set bit_file [file join $impl_dir radar_system_v3_wrapper.bit]
set hwh_file [file normalize {vivado/radar_system_v3/radar_system_v3.gen/sources_1/bd/radar_system_v3/hw_handoff/radar_system_v3.hwh}]

foreach required_file [list $project_file $routed_dcp $bit_file $hwh_file] {
  if {![file exists $required_file]} {
    error [format {Required V3 build output was not found: %s} $required_file]
  }
}

open_project $project_file
open_checkpoint $routed_dcp

set utilization_report [file normalize {vivado/radar_system_v3_utilization.rpt}]
set timing_report [file normalize {vivado/radar_system_v3_timing.rpt}]
set drc_report [file normalize {vivado/radar_system_v3_drc.rpt}]
report_utilization -file $utilization_report
report_timing_summary -file $timing_report
report_drc -file $drc_report

set overlay_dir [file normalize {overlay/radar_filter_v3}]
file mkdir $overlay_dir
file copy -force $bit_file [file join $overlay_dir radar_filter_v3.bit]
file copy -force $hwh_file [file join $overlay_dir radar_filter_v3.hwh]
write_hw_platform -fixed -include_bit -force \
  -file [file join $overlay_dir radar_filter_v3.xsa]

set manifest [open [file join $overlay_dir BUILD_INFO.txt] w]
puts $manifest {PYNQ-Z2 LD6004 Radar Filter V3}
puts $manifest [format {Vivado project: %s} $project_file]
puts $manifest {Build mode: direct Vivado run scripts}
puts $manifest {Clock: 100 MHz}
puts $manifest {radar_filter_0 base: 0x40000000}
puts $manifest {axi_gpio_alarm base: 0x41200000}
puts $manifest {Alarm outputs: PYNQ-Z2 LED0..LED3 via 4-bit AXI GPIO}
puts $manifest {Functions: V2 filtering/feature IP plus software-controlled hardware alarm output}
close $manifest

puts {============================================================}
puts { V3 overlay packaged successfully.}
puts [format { Overlay directory: %s} $overlay_dir]
puts [format { Utilization report: %s} $utilization_report]
puts [format { Timing report:      %s} $timing_report]
puts [format { DRC report:         %s} $drc_report]
puts {============================================================}
close_project
exit

