#bit compress spix4 speed up
set_property BITSTREAM.GENERAL.COMPRESS true [current_design]
set_property CONFIG_MODE SPIx4 [current_design]
set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 4 [current_design]
set_property BITSTREAM.CONFIG.CONFIGRATE 50 [current_design]
set_property PACKAGE_PIN G25 [get_ports uart_txd]
set_property PACKAGE_PIN L27 [get_ports uart_rxd]
set_property IOSTANDARD LVCMOS18 [get_ports uart_txd]
set_property IOSTANDARD LVCMOS18 [get_ports uart_rxd]

set_property PACKAGE_PIN AD26 [get_ports rst]
set_property PACKAGE_PIN AC24 [get_ports sys_mmcm_sel_cmd_raw]
set_property IOSTANDARD LVCMOS18 [get_ports rst]
set_property IOSTANDARD LVCMOS18 [get_ports sys_mmcm_sel_cmd_raw]

create_clock -period 4.000 [get_ports gty127_clk_p]
set_property PACKAGE_PIN R29 [get_ports gty127_clk_p]
set_property PACKAGE_PIN G27 [get_ports {user_led[5]}]
set_property PACKAGE_PIN G26 [get_ports {user_led[4]}]
set_property PACKAGE_PIN H27 [get_ports {user_led[3]}]
set_property PACKAGE_PIN H26 [get_ports {user_led[2]}]
set_property PACKAGE_PIN J26 [get_ports {user_led[1]}]
set_property PACKAGE_PIN AC26 [get_ports {user_led[0]}]
set_property IOSTANDARD LVCMOS18 [get_ports {user_led[5]}]
set_property IOSTANDARD LVCMOS18 [get_ports {user_led[4]}]
set_property IOSTANDARD LVCMOS18 [get_ports {user_led[3]}]
set_property IOSTANDARD LVCMOS18 [get_ports {user_led[2]}]
set_property IOSTANDARD LVCMOS18 [get_ports {user_led[1]}]
set_property IOSTANDARD LVCMOS18 [get_ports {user_led[0]}]

# Front-panel LEDs 1..10 (active-low through NVT2010PW)
set_property PACKAGE_PIN C23 [get_ports {panel_led[0]}]
set_property PACKAGE_PIN A23 [get_ports {panel_led[1]}]
set_property PACKAGE_PIN C22 [get_ports {panel_led[2]}]
set_property PACKAGE_PIN D21 [get_ports {panel_led[3]}]
set_property PACKAGE_PIN B20 [get_ports {panel_led[4]}]
set_property PACKAGE_PIN E23 [get_ports {panel_led[5]}]
set_property PACKAGE_PIN D23 [get_ports {panel_led[6]}]
set_property PACKAGE_PIN D24 [get_ports {panel_led[7]}]
set_property PACKAGE_PIN C24 [get_ports {panel_led[8]}]
set_property PACKAGE_PIN C26 [get_ports {panel_led[9]}]
set_property IOSTANDARD LVCMOS18 [get_ports {panel_led[*]}]

# Front-panel buttons 1..2 (active-low through NVT2010PW)
set_property PACKAGE_PIN D25 [get_ports {panel_btn_n[0]}]
set_property PACKAGE_PIN E25 [get_ports {panel_btn_n[1]}]
set_property IOSTANDARD LVCMOS18 [get_ports {panel_btn_n[*]}]

set_property PACKAGE_PIN A12 [get_ports {rf_out_en[3]}]
set_property PACKAGE_PIN A13 [get_ports {rf_out_en[2]}]
set_property PACKAGE_PIN C13 [get_ports {rf_out_en[1]}]
set_property PACKAGE_PIN D13 [get_ports {rf_out_en[0]}]
set_property IOSTANDARD LVCMOS18 [get_ports {rf_out_en[3]}]
set_property IOSTANDARD LVCMOS18 [get_ports {rf_out_en[2]}]
set_property IOSTANDARD LVCMOS18 [get_ports {rf_out_en[1]}]
set_property IOSTANDARD LVCMOS18 [get_ports {rf_out_en[0]}]

set_property IOSTANDARD LVCMOS18 [get_ports ad9144_irq]
set_property IOSTANDARD LVCMOS18 [get_ports ad9144_tx_en0]
set_property IOSTANDARD LVCMOS18 [get_ports ad9144_tx_en1]
set_property PACKAGE_PIN B9 [get_ports ad9144_irq]
set_property PACKAGE_PIN E8 [get_ports ad9144_tx_en0]
set_property PACKAGE_PIN F8 [get_ports ad9144_tx_en1]
create_clock -period 4.000 [get_ports gty224_clk_p]
create_clock -period 4.000 [get_ports gty225_clk_p]
create_clock -period 4.000 [get_ports gty226_clk_p]
create_clock -period 4.000 [get_ports gty227_clk_p]
create_clock -period 5.000 [get_ports sysclk_p]
create_clock -period 4.000 -waveform {0.000 2.000} [get_ports coreclk_p]
set_property PACKAGE_PIN AF6 [get_ports gty224_clk_p]
set_property PACKAGE_PIN AB6 [get_ports gty225_clk_p]
set_property PACKAGE_PIN V6 [get_ports gty226_clk_p]
set_property PACKAGE_PIN P6 [get_ports gty227_clk_p]
#set_property PACKAGE_PIN F18 [get_ports sysclk_p]
set_property PACKAGE_PIN AJ23 [get_ports sysclk_p]
set_property IOSTANDARD LVDS [get_ports sysclk_p]
set_property IOSTANDARD LVDS [get_ports sysclk_n]
set_property PACKAGE_PIN AG12 [get_ports coreclk_p]
set_property IOSTANDARD DIFF_SSTL18_I [get_ports coreclk_n]
set_property IOSTANDARD DIFF_SSTL18_I [get_ports coreclk_p]

#set_property IOSTANDARD LVDS [get_ports coreclk_n]
#set_property IOSTANDARD LVDS [get_ports coreclk_p]

set_property PACKAGE_PIN C17 [get_ports lmk048_ld1]
set_property PACKAGE_PIN B17 [get_ports lmk048_ld2]
set_property PACKAGE_PIN W24 [get_ports ads54j60_reset]
set_property PACKAGE_PIN G20 [get_ports ads54j69_reset]
set_property PACKAGE_PIN D14 [get_ports lmk048_sync]
set_property IOSTANDARD LVCMOS18 [get_ports lmk048_ld1]
set_property IOSTANDARD LVCMOS18 [get_ports lmk048_ld2]
set_property IOSTANDARD LVCMOS18 [get_ports ads54j60_reset]
set_property IOSTANDARD LVCMOS18 [get_ports ads54j69_reset]
set_property IOSTANDARD LVCMOS18 [get_ports lmk048_sync]
set_property PACKAGE_PIN AG11 [get_ports sysrefclk_p]
set_property IOSTANDARD DIFF_SSTL18_I [get_ports sysrefclk_p]
set_property IOSTANDARD DIFF_SSTL18_I [get_ports sysrefclk_n]
set_property LOC GTHE3_CHANNEL_X1Y3 [get_cells {u_adda_top/adda_top_i/ads54j60_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_2_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_2_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[3].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[3].GTHE3_CHANNEL_PRIM_INST}]
set_property PACKAGE_PIN AJ4 [get_ports {ads54j60_A_p[3]}]
set_property LOC GTHE3_CHANNEL_X1Y2 [get_cells {u_adda_top/adda_top_i/ads54j60_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_2_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_2_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[3].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[2].GTHE3_CHANNEL_PRIM_INST}]
set_property PACKAGE_PIN AK2 [get_ports {ads54j60_A_p[2]}]
set_property PACKAGE_PIN AM2 [get_ports {ads54j60_A_p[1]}]
set_property PACKAGE_PIN AP2 [get_ports {ads54j60_A_p[0]}]
set_property PACKAGE_PIN AB2 [get_ports {ads54j60_B_p[3]}]
set_property PACKAGE_PIN AD2 [get_ports {ads54j60_B_p[2]}]
set_property PACKAGE_PIN AF2 [get_ports {ads54j60_B_p[1]}]
set_property PACKAGE_PIN AH2 [get_ports {ads54j60_B_p[0]}]
set_property LOC GTHE3_CHANNEL_X1Y9 [get_cells {u_adda_top/adda_top_i/ads54j69_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_0_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_0_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[3].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[1].GTHE3_CHANNEL_PRIM_INST}]
set_property PACKAGE_PIN V2 [get_ports {ads54j69_A_p[1]}]
set_property LOC GTHE3_CHANNEL_X1Y8 [get_cells {u_adda_top/adda_top_i/ads54j69_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_0_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_0_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[3].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[0].GTHE3_CHANNEL_PRIM_INST}]
set_property PACKAGE_PIN Y2 [get_ports {ads54j69_A_p[0]}]
set_property PACKAGE_PIN K2 [get_ports {ads54j69_B_p[1]}]
set_property PACKAGE_PIN M2 [get_ports {ads54j69_B_p[0]}]
set_property LOC GTHE3_CHANNEL_X0Y19 [get_cells {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[4].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[3].GTHE3_CHANNEL_PRIM_INST}]
set_property PACKAGE_PIN B31 [get_ports {ad9144_da_p[7]}]
set_property LOC GTHE3_CHANNEL_X0Y18 [get_cells {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[4].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[2].GTHE3_CHANNEL_PRIM_INST}]
set_property PACKAGE_PIN D31 [get_ports {ad9144_da_p[6]}]
set_property LOC GTHE3_CHANNEL_X0Y17 [get_cells {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[4].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[1].GTHE3_CHANNEL_PRIM_INST}]
set_property PACKAGE_PIN G29 [get_ports {ad9144_da_p[5]}]
set_property LOC GTHE3_CHANNEL_X0Y16 [get_cells {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[4].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[0].GTHE3_CHANNEL_PRIM_INST}]
set_property PACKAGE_PIN H31 [get_ports {ad9144_da_p[4]}]
set_property PACKAGE_PIN K31 [get_ports {ad9144_da_p[3]}]
set_property PACKAGE_PIN M31 [get_ports {ad9144_da_p[2]}]
set_property PACKAGE_PIN P31 [get_ports {ad9144_da_p[1]}]
set_property PACKAGE_PIN T31 [get_ports {ad9144_da_p[0]}]
set_property PACKAGE_PIN A9 [get_ports ad9144_cs]
set_property PACKAGE_PIN A10 [get_ports ad9144_miso]
set_property PACKAGE_PIN D8 [get_ports ad9144_mosi]
set_property PACKAGE_PIN C8 [get_ports ad9144_sclk]
set_property PACKAGE_PIN AA25 [get_ports ads54j60_cs]
set_property PACKAGE_PIN Y25 [get_ports ads54j60_sclk]
set_property PACKAGE_PIN W23 [get_ports ads54j60_sdin]
set_property PACKAGE_PIN Y21 [get_ports ads54j60_sdio]
set_property PACKAGE_PIN AA24 [get_ports ads54j60_syncse]
set_property PACKAGE_PIN H22 [get_ports ads54j69_cs]
set_property PACKAGE_PIN F22 [get_ports ads54j69_sclk]
set_property PACKAGE_PIN U29 [get_ports ads54j69_sdin]
set_property PACKAGE_PIN G22 [get_ports ads54j69_sdio]
set_property PACKAGE_PIN J23 [get_ports ads54j69_syncse]
set_property PACKAGE_PIN G10 [get_ports da_sync_out0_p]
set_property PACKAGE_PIN G9 [get_ports da_sync_out1_p]
set_property PACKAGE_PIN C14 [get_ports lmk048_clk]
set_property PACKAGE_PIN F15 [get_ports lmk048_cs]
set_property PACKAGE_PIN C18 [get_ports lmk048_mosi]


set_property IOSTANDARD LVCMOS18 [get_ports ad9144_cs]
set_property IOSTANDARD LVCMOS18 [get_ports ad9144_miso]
set_property IOSTANDARD LVCMOS18 [get_ports ad9144_mosi]
set_property IOSTANDARD LVCMOS18 [get_ports ad9144_sclk]
set_property IOSTANDARD LVCMOS18 [get_ports ads54j60_cs]
set_property IOSTANDARD LVCMOS18 [get_ports ads54j60_sclk]
set_property IOSTANDARD LVCMOS18 [get_ports ads54j60_sdin]
set_property IOSTANDARD LVCMOS18 [get_ports ads54j60_sdio]
set_property IOSTANDARD LVCMOS18 [get_ports ads54j60_syncse]
set_property IOSTANDARD LVCMOS18 [get_ports ads54j69_cs]
set_property IOSTANDARD LVCMOS18 [get_ports ads54j69_sclk]
set_property IOSTANDARD LVCMOS18 [get_ports ads54j69_sdin]
set_property IOSTANDARD LVCMOS18 [get_ports ads54j69_sdio]
set_property IOSTANDARD LVCMOS18 [get_ports ads54j69_syncse]
set_property IOSTANDARD LVCMOS18 [get_ports lmk048_clk]
set_property IOSTANDARD LVCMOS18 [get_ports lmk048_cs]
set_property IOSTANDARD LVCMOS18 [get_ports lmk048_mosi]
set_property IOSTANDARD DIFF_SSTL18_I [get_ports da_sync_out0_p]
set_property IOSTANDARD DIFF_SSTL18_I [get_ports da_sync_out1_p]

set_property MARK_DEBUG true [get_nets sys_mmcm_sel_cmd_buf]
set_property MARK_DEBUG true [get_nets sys_mmcm_sel_cmd]
set_property MARK_DEBUG true [get_nets sys_mmcm_sel]
set_property MARK_DEBUG true [get_nets sys_mmcm_rst]

set_property DIFF_TERM_ADV TERM_NONE [get_ports sysclk_p]


set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch0[9]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch3[2]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch0[14]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch3[7]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch1[1]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch1[5]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch1[14]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch0[6]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch1[4]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch3[5]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch0[0]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch0[2]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch2[0]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch1[6]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch0[13]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch0[15]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch0[1]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch0[2]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch3[0]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch0[7]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch2[12]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch2[15]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch1[2]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch1[0]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch1[13]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch3[6]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch3[14]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch1[14]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch3[13]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch1[10]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch0[0]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch0[1]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch1[9]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch2[8]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch0[6]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch2[4]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch1[5]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch1[12]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch0[3]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch0[8]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch0[7]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch0[13]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch1[0]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch0[5]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch3[11]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch1[13]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch0[2]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch0[8]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch1[10]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch1[11]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch0[11]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch1[1]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch1[6]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch1[4]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch1[3]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch0[5]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch3[12]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch0[8]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch1[5]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch3[10]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch1[4]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch1[14]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch1[10]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch0[10]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch3[1]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch0[9]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch1[6]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch1[7]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch1[0]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch1[2]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch1[15]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch0[14]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch2[9]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch0[4]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch2[2]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch2[3]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch0[6]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch0[7]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch0[12]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch0[4]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch1[3]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch2[11]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch2[13]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch0[12]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch1[2]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch1[1]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch1[8]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch0[11]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch0[10]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch0[12]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch1[15]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch1[8]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch2[10]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch1[7]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch0[4]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch0[3]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch3[15]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch0[3]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch0[15]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch2[7]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch1[11]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch0[5]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch0[11]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch2[5]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch0[10]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch0[14]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch3[9]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch1[3]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch0[9]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch3[3]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch3[8]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch0[1]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch1[12]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch2[6]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch1[8]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch1[12]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch1[9]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch0[0]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch1[13]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch2[14]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch3[4]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch0[13]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch0[15]}]
set_property MARK_DEBUG true [get_nets {ad9144_tx_data_ch2[1]}]
set_property MARK_DEBUG true [get_nets {ads54j60_adc_data_ch1[9]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch1[7]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch1[11]}]
set_property MARK_DEBUG true [get_nets {ads54j69_adc_data_ch1[15]}]
# Removed stale pre-creation connections; active u_ila_0 probes are defined below.

create_debug_core u_ila_0 ila
set_property ALL_PROBE_SAME_MU true [get_debug_cores u_ila_0]
set_property ALL_PROBE_SAME_MU_CNT 1 [get_debug_cores u_ila_0]
set_property C_ADV_TRIGGER false [get_debug_cores u_ila_0]
set_property C_DATA_DEPTH 16384 [get_debug_cores u_ila_0]
set_property C_EN_STRG_QUAL false [get_debug_cores u_ila_0]
set_property C_INPUT_PIPE_STAGES 4 [get_debug_cores u_ila_0]
set_property C_TRIGIN_EN false [get_debug_cores u_ila_0]
set_property C_TRIGOUT_EN false [get_debug_cores u_ila_0]
set_property port_width 1 [get_debug_ports u_ila_0/clk]
connect_debug_port u_ila_0/clk [get_nets [list sys_clk]]
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_0/probe0]
set_property port_width 16 [get_debug_ports u_ila_0/probe0]
connect_debug_port u_ila_0/probe0 [get_nets [list {ad9144_tx_data_ch2[0]} {ad9144_tx_data_ch2[1]} {ad9144_tx_data_ch2[2]} {ad9144_tx_data_ch2[3]} {ad9144_tx_data_ch2[4]} {ad9144_tx_data_ch2[5]} {ad9144_tx_data_ch2[6]} {ad9144_tx_data_ch2[7]} {ad9144_tx_data_ch2[8]} {ad9144_tx_data_ch2[9]} {ad9144_tx_data_ch2[10]} {ad9144_tx_data_ch2[11]} {ad9144_tx_data_ch2[12]} {ad9144_tx_data_ch2[13]} {ad9144_tx_data_ch2[14]} {ad9144_tx_data_ch2[15]}]]
create_debug_port u_ila_0 probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_0/probe1]
set_property port_width 16 [get_debug_ports u_ila_0/probe1]
connect_debug_port u_ila_0/probe1 [get_nets [list {ad9144_tx_data_ch3[0]} {ad9144_tx_data_ch3[1]} {ad9144_tx_data_ch3[2]} {ad9144_tx_data_ch3[3]} {ad9144_tx_data_ch3[4]} {ad9144_tx_data_ch3[5]} {ad9144_tx_data_ch3[6]} {ad9144_tx_data_ch3[7]} {ad9144_tx_data_ch3[8]} {ad9144_tx_data_ch3[9]} {ad9144_tx_data_ch3[10]} {ad9144_tx_data_ch3[11]} {ad9144_tx_data_ch3[12]} {ad9144_tx_data_ch3[13]} {ad9144_tx_data_ch3[14]} {ad9144_tx_data_ch3[15]}]]
create_debug_port u_ila_0 probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_0/probe2]
set_property port_width 32 [get_debug_ports u_ila_0/probe2]
connect_debug_port u_ila_0/probe2 [get_nets [list {adc_in[16]} {adc_in[17]} {adc_in[18]} {adc_in[19]} {adc_in[20]} {adc_in[21]} {adc_in[22]} {adc_in[23]} {adc_in[24]} {adc_in[25]} {adc_in[26]} {adc_in[27]} {adc_in[28]} {adc_in[29]} {adc_in[30]} {adc_in[31]} {adc_in[48]} {adc_in[49]} {adc_in[50]} {adc_in[51]} {adc_in[52]} {adc_in[53]} {adc_in[54]} {adc_in[55]} {adc_in[56]} {adc_in[57]} {adc_in[58]} {adc_in[59]} {adc_in[60]} {adc_in[61]} {adc_in[62]} {adc_in[63]}]]
create_debug_port u_ila_0 probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_0/probe3]
set_property port_width 16 [get_debug_ports u_ila_0/probe3]
connect_debug_port u_ila_0/probe3 [get_nets [list {ad9144_tx_data_ch0[0]} {ad9144_tx_data_ch0[1]} {ad9144_tx_data_ch0[2]} {ad9144_tx_data_ch0[3]} {ad9144_tx_data_ch0[4]} {ad9144_tx_data_ch0[5]} {ad9144_tx_data_ch0[6]} {ad9144_tx_data_ch0[7]} {ad9144_tx_data_ch0[8]} {ad9144_tx_data_ch0[9]} {ad9144_tx_data_ch0[10]} {ad9144_tx_data_ch0[11]} {ad9144_tx_data_ch0[12]} {ad9144_tx_data_ch0[13]} {ad9144_tx_data_ch0[14]} {ad9144_tx_data_ch0[15]}]]
create_debug_port u_ila_0 probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_0/probe4]
set_property port_width 16 [get_debug_ports u_ila_0/probe4]
connect_debug_port u_ila_0/probe4 [get_nets [list {ad9144_tx_data_ch1[0]} {ad9144_tx_data_ch1[1]} {ad9144_tx_data_ch1[2]} {ad9144_tx_data_ch1[3]} {ad9144_tx_data_ch1[4]} {ad9144_tx_data_ch1[5]} {ad9144_tx_data_ch1[6]} {ad9144_tx_data_ch1[7]} {ad9144_tx_data_ch1[8]} {ad9144_tx_data_ch1[9]} {ad9144_tx_data_ch1[10]} {ad9144_tx_data_ch1[11]} {ad9144_tx_data_ch1[12]} {ad9144_tx_data_ch1[13]} {ad9144_tx_data_ch1[14]} {ad9144_tx_data_ch1[15]}]]
create_debug_core u_ila_1 ila
set_property ALL_PROBE_SAME_MU true [get_debug_cores u_ila_1]
set_property ALL_PROBE_SAME_MU_CNT 1 [get_debug_cores u_ila_1]
set_property C_ADV_TRIGGER false [get_debug_cores u_ila_1]
set_property C_DATA_DEPTH 16384 [get_debug_cores u_ila_1]
set_property C_EN_STRG_QUAL false [get_debug_cores u_ila_1]
set_property C_INPUT_PIPE_STAGES 4 [get_debug_cores u_ila_1]
set_property C_TRIGIN_EN false [get_debug_cores u_ila_1]
set_property C_TRIGOUT_EN false [get_debug_cores u_ila_1]
set_property port_width 1 [get_debug_ports u_ila_1/clk]
connect_debug_port u_ila_1/clk [get_nets [list sys_clk_in]]
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_1/probe0]
set_property port_width 1 [get_debug_ports u_ila_1/probe0]
connect_debug_port u_ila_1/probe0 [get_nets [list sys_mmcm_rst]]
create_debug_port u_ila_1 probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_1/probe1]
set_property port_width 1 [get_debug_ports u_ila_1/probe1]
connect_debug_port u_ila_1/probe1 [get_nets [list sys_mmcm_sel]]
create_debug_port u_ila_1 probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_1/probe2]
set_property port_width 1 [get_debug_ports u_ila_1/probe2]
connect_debug_port u_ila_1/probe2 [get_nets [list sys_mmcm_sel_cmd]]
create_debug_port u_ila_1 probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_1/probe3]
set_property port_width 1 [get_debug_ports u_ila_1/probe3]
connect_debug_port u_ila_1/probe3 [get_nets [list sys_mmcm_sel_cmd_buf]]
set_property C_CLK_INPUT_FREQ_HZ 300000000 [get_debug_cores dbg_hub]
set_property C_ENABLE_CLK_DIVIDER false [get_debug_cores dbg_hub]
set_property C_USER_SCAN_CHAIN 1 [get_debug_cores dbg_hub]
connect_debug_port dbg_hub/clk [get_nets sys_clk]

# AD9144 output-path diagnostics (62.5 MHz).
# Keep the original sys_clk-domain ILAs above. All data probes below are
# sampled AFTER the 16-to-64-bit DAC FIFOs, before JESD byte rearrangement.
# Probe map:
# 0..3: tx_tdata_RF, tx_tdata_RF1, tx_tdata_RF2, tx_tdata_RF3 (64 bits each)
# 4: FIFO0 empty; 5: actual FIFO reset (active high)
# 6: AD9144 JESD core reset (active high)
# 7[0]: TXEN0, 7[1]: TXEN1 (currently driven by the same GPIO bit)
# 8: JESD0 tready; 9: SYNC0; 10: PHY tx_reset_done
# SYNC1 is unused by this design and absent from the synthesized netlist.
# The core-reset input resolves to constant zero in the current netlist.
# 11[2*lane +: 2]: GT TXBUFSTATUS[1:0], lane order listed below.
# TXBUFSTATUS bit 1 = sticky overflow/underflow; bit 0 = half-full status.
# SYNC/reset/TXEN are level diagnostics, not CDC edge-timing measurements.
# BEGIN AD9144_OUTPUT_ILA
create_debug_core u_ila_dac_out ila
set_property ALL_PROBE_SAME_MU true [get_debug_cores u_ila_dac_out]
set_property ALL_PROBE_SAME_MU_CNT 1 [get_debug_cores u_ila_dac_out]
set_property C_ADV_TRIGGER false [get_debug_cores u_ila_dac_out]
set_property C_DATA_DEPTH 4096 [get_debug_cores u_ila_dac_out]
set_property C_EN_STRG_QUAL false [get_debug_cores u_ila_dac_out]
set_property C_INPUT_PIPE_STAGES 2 [get_debug_cores u_ila_dac_out]
set_property C_TRIGIN_EN false [get_debug_cores u_ila_dac_out]
set_property C_TRIGOUT_EN false [get_debug_cores u_ila_dac_out]
set_property port_width 1 [get_debug_ports u_ila_dac_out/clk]
connect_debug_port u_ila_dac_out/clk [get_nets {u_adda_top/ad9144_core_clk_o}]

# probe0
set_property MARK_DEBUG true [get_nets [list {u_adda_top/tx_tdata_RF[0]} {u_adda_top/tx_tdata_RF[1]} {u_adda_top/tx_tdata_RF[2]} {u_adda_top/tx_tdata_RF[3]} {u_adda_top/tx_tdata_RF[4]} {u_adda_top/tx_tdata_RF[5]} {u_adda_top/tx_tdata_RF[6]} {u_adda_top/tx_tdata_RF[7]} {u_adda_top/tx_tdata_RF[8]} {u_adda_top/tx_tdata_RF[9]} {u_adda_top/tx_tdata_RF[10]} {u_adda_top/tx_tdata_RF[11]} {u_adda_top/tx_tdata_RF[12]} {u_adda_top/tx_tdata_RF[13]} {u_adda_top/tx_tdata_RF[14]} {u_adda_top/tx_tdata_RF[15]} {u_adda_top/tx_tdata_RF[16]} {u_adda_top/tx_tdata_RF[17]} {u_adda_top/tx_tdata_RF[18]} {u_adda_top/tx_tdata_RF[19]} {u_adda_top/tx_tdata_RF[20]} {u_adda_top/tx_tdata_RF[21]} {u_adda_top/tx_tdata_RF[22]} {u_adda_top/tx_tdata_RF[23]} {u_adda_top/tx_tdata_RF[24]} {u_adda_top/tx_tdata_RF[25]} {u_adda_top/tx_tdata_RF[26]} {u_adda_top/tx_tdata_RF[27]} {u_adda_top/tx_tdata_RF[28]} {u_adda_top/tx_tdata_RF[29]} {u_adda_top/tx_tdata_RF[30]} {u_adda_top/tx_tdata_RF[31]} {u_adda_top/tx_tdata_RF[32]} {u_adda_top/tx_tdata_RF[33]} {u_adda_top/tx_tdata_RF[34]} {u_adda_top/tx_tdata_RF[35]} {u_adda_top/tx_tdata_RF[36]} {u_adda_top/tx_tdata_RF[37]} {u_adda_top/tx_tdata_RF[38]} {u_adda_top/tx_tdata_RF[39]} {u_adda_top/tx_tdata_RF[40]} {u_adda_top/tx_tdata_RF[41]} {u_adda_top/tx_tdata_RF[42]} {u_adda_top/tx_tdata_RF[43]} {u_adda_top/tx_tdata_RF[44]} {u_adda_top/tx_tdata_RF[45]} {u_adda_top/tx_tdata_RF[46]} {u_adda_top/tx_tdata_RF[47]} {u_adda_top/tx_tdata_RF[48]} {u_adda_top/tx_tdata_RF[49]} {u_adda_top/tx_tdata_RF[50]} {u_adda_top/tx_tdata_RF[51]} {u_adda_top/tx_tdata_RF[52]} {u_adda_top/tx_tdata_RF[53]} {u_adda_top/tx_tdata_RF[54]} {u_adda_top/tx_tdata_RF[55]} {u_adda_top/tx_tdata_RF[56]} {u_adda_top/tx_tdata_RF[57]} {u_adda_top/tx_tdata_RF[58]} {u_adda_top/tx_tdata_RF[59]} {u_adda_top/tx_tdata_RF[60]} {u_adda_top/tx_tdata_RF[61]} {u_adda_top/tx_tdata_RF[62]} {u_adda_top/tx_tdata_RF[63]}]]
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_dac_out/probe0]
set_property port_width 64 [get_debug_ports u_ila_dac_out/probe0]
connect_debug_port u_ila_dac_out/probe0 [get_nets [list {u_adda_top/tx_tdata_RF[0]} {u_adda_top/tx_tdata_RF[1]} {u_adda_top/tx_tdata_RF[2]} {u_adda_top/tx_tdata_RF[3]} {u_adda_top/tx_tdata_RF[4]} {u_adda_top/tx_tdata_RF[5]} {u_adda_top/tx_tdata_RF[6]} {u_adda_top/tx_tdata_RF[7]} {u_adda_top/tx_tdata_RF[8]} {u_adda_top/tx_tdata_RF[9]} {u_adda_top/tx_tdata_RF[10]} {u_adda_top/tx_tdata_RF[11]} {u_adda_top/tx_tdata_RF[12]} {u_adda_top/tx_tdata_RF[13]} {u_adda_top/tx_tdata_RF[14]} {u_adda_top/tx_tdata_RF[15]} {u_adda_top/tx_tdata_RF[16]} {u_adda_top/tx_tdata_RF[17]} {u_adda_top/tx_tdata_RF[18]} {u_adda_top/tx_tdata_RF[19]} {u_adda_top/tx_tdata_RF[20]} {u_adda_top/tx_tdata_RF[21]} {u_adda_top/tx_tdata_RF[22]} {u_adda_top/tx_tdata_RF[23]} {u_adda_top/tx_tdata_RF[24]} {u_adda_top/tx_tdata_RF[25]} {u_adda_top/tx_tdata_RF[26]} {u_adda_top/tx_tdata_RF[27]} {u_adda_top/tx_tdata_RF[28]} {u_adda_top/tx_tdata_RF[29]} {u_adda_top/tx_tdata_RF[30]} {u_adda_top/tx_tdata_RF[31]} {u_adda_top/tx_tdata_RF[32]} {u_adda_top/tx_tdata_RF[33]} {u_adda_top/tx_tdata_RF[34]} {u_adda_top/tx_tdata_RF[35]} {u_adda_top/tx_tdata_RF[36]} {u_adda_top/tx_tdata_RF[37]} {u_adda_top/tx_tdata_RF[38]} {u_adda_top/tx_tdata_RF[39]} {u_adda_top/tx_tdata_RF[40]} {u_adda_top/tx_tdata_RF[41]} {u_adda_top/tx_tdata_RF[42]} {u_adda_top/tx_tdata_RF[43]} {u_adda_top/tx_tdata_RF[44]} {u_adda_top/tx_tdata_RF[45]} {u_adda_top/tx_tdata_RF[46]} {u_adda_top/tx_tdata_RF[47]} {u_adda_top/tx_tdata_RF[48]} {u_adda_top/tx_tdata_RF[49]} {u_adda_top/tx_tdata_RF[50]} {u_adda_top/tx_tdata_RF[51]} {u_adda_top/tx_tdata_RF[52]} {u_adda_top/tx_tdata_RF[53]} {u_adda_top/tx_tdata_RF[54]} {u_adda_top/tx_tdata_RF[55]} {u_adda_top/tx_tdata_RF[56]} {u_adda_top/tx_tdata_RF[57]} {u_adda_top/tx_tdata_RF[58]} {u_adda_top/tx_tdata_RF[59]} {u_adda_top/tx_tdata_RF[60]} {u_adda_top/tx_tdata_RF[61]} {u_adda_top/tx_tdata_RF[62]} {u_adda_top/tx_tdata_RF[63]}]]

# probe1
set_property MARK_DEBUG true [get_nets [list {u_adda_top/tx_tdata_RF1[0]} {u_adda_top/tx_tdata_RF1[1]} {u_adda_top/tx_tdata_RF1[2]} {u_adda_top/tx_tdata_RF1[3]} {u_adda_top/tx_tdata_RF1[4]} {u_adda_top/tx_tdata_RF1[5]} {u_adda_top/tx_tdata_RF1[6]} {u_adda_top/tx_tdata_RF1[7]} {u_adda_top/tx_tdata_RF1[8]} {u_adda_top/tx_tdata_RF1[9]} {u_adda_top/tx_tdata_RF1[10]} {u_adda_top/tx_tdata_RF1[11]} {u_adda_top/tx_tdata_RF1[12]} {u_adda_top/tx_tdata_RF1[13]} {u_adda_top/tx_tdata_RF1[14]} {u_adda_top/tx_tdata_RF1[15]} {u_adda_top/tx_tdata_RF1[16]} {u_adda_top/tx_tdata_RF1[17]} {u_adda_top/tx_tdata_RF1[18]} {u_adda_top/tx_tdata_RF1[19]} {u_adda_top/tx_tdata_RF1[20]} {u_adda_top/tx_tdata_RF1[21]} {u_adda_top/tx_tdata_RF1[22]} {u_adda_top/tx_tdata_RF1[23]} {u_adda_top/tx_tdata_RF1[24]} {u_adda_top/tx_tdata_RF1[25]} {u_adda_top/tx_tdata_RF1[26]} {u_adda_top/tx_tdata_RF1[27]} {u_adda_top/tx_tdata_RF1[28]} {u_adda_top/tx_tdata_RF1[29]} {u_adda_top/tx_tdata_RF1[30]} {u_adda_top/tx_tdata_RF1[31]} {u_adda_top/tx_tdata_RF1[32]} {u_adda_top/tx_tdata_RF1[33]} {u_adda_top/tx_tdata_RF1[34]} {u_adda_top/tx_tdata_RF1[35]} {u_adda_top/tx_tdata_RF1[36]} {u_adda_top/tx_tdata_RF1[37]} {u_adda_top/tx_tdata_RF1[38]} {u_adda_top/tx_tdata_RF1[39]} {u_adda_top/tx_tdata_RF1[40]} {u_adda_top/tx_tdata_RF1[41]} {u_adda_top/tx_tdata_RF1[42]} {u_adda_top/tx_tdata_RF1[43]} {u_adda_top/tx_tdata_RF1[44]} {u_adda_top/tx_tdata_RF1[45]} {u_adda_top/tx_tdata_RF1[46]} {u_adda_top/tx_tdata_RF1[47]} {u_adda_top/tx_tdata_RF1[48]} {u_adda_top/tx_tdata_RF1[49]} {u_adda_top/tx_tdata_RF1[50]} {u_adda_top/tx_tdata_RF1[51]} {u_adda_top/tx_tdata_RF1[52]} {u_adda_top/tx_tdata_RF1[53]} {u_adda_top/tx_tdata_RF1[54]} {u_adda_top/tx_tdata_RF1[55]} {u_adda_top/tx_tdata_RF1[56]} {u_adda_top/tx_tdata_RF1[57]} {u_adda_top/tx_tdata_RF1[58]} {u_adda_top/tx_tdata_RF1[59]} {u_adda_top/tx_tdata_RF1[60]} {u_adda_top/tx_tdata_RF1[61]} {u_adda_top/tx_tdata_RF1[62]} {u_adda_top/tx_tdata_RF1[63]}]]
create_debug_port u_ila_dac_out probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_dac_out/probe1]
set_property port_width 64 [get_debug_ports u_ila_dac_out/probe1]
connect_debug_port u_ila_dac_out/probe1 [get_nets [list {u_adda_top/tx_tdata_RF1[0]} {u_adda_top/tx_tdata_RF1[1]} {u_adda_top/tx_tdata_RF1[2]} {u_adda_top/tx_tdata_RF1[3]} {u_adda_top/tx_tdata_RF1[4]} {u_adda_top/tx_tdata_RF1[5]} {u_adda_top/tx_tdata_RF1[6]} {u_adda_top/tx_tdata_RF1[7]} {u_adda_top/tx_tdata_RF1[8]} {u_adda_top/tx_tdata_RF1[9]} {u_adda_top/tx_tdata_RF1[10]} {u_adda_top/tx_tdata_RF1[11]} {u_adda_top/tx_tdata_RF1[12]} {u_adda_top/tx_tdata_RF1[13]} {u_adda_top/tx_tdata_RF1[14]} {u_adda_top/tx_tdata_RF1[15]} {u_adda_top/tx_tdata_RF1[16]} {u_adda_top/tx_tdata_RF1[17]} {u_adda_top/tx_tdata_RF1[18]} {u_adda_top/tx_tdata_RF1[19]} {u_adda_top/tx_tdata_RF1[20]} {u_adda_top/tx_tdata_RF1[21]} {u_adda_top/tx_tdata_RF1[22]} {u_adda_top/tx_tdata_RF1[23]} {u_adda_top/tx_tdata_RF1[24]} {u_adda_top/tx_tdata_RF1[25]} {u_adda_top/tx_tdata_RF1[26]} {u_adda_top/tx_tdata_RF1[27]} {u_adda_top/tx_tdata_RF1[28]} {u_adda_top/tx_tdata_RF1[29]} {u_adda_top/tx_tdata_RF1[30]} {u_adda_top/tx_tdata_RF1[31]} {u_adda_top/tx_tdata_RF1[32]} {u_adda_top/tx_tdata_RF1[33]} {u_adda_top/tx_tdata_RF1[34]} {u_adda_top/tx_tdata_RF1[35]} {u_adda_top/tx_tdata_RF1[36]} {u_adda_top/tx_tdata_RF1[37]} {u_adda_top/tx_tdata_RF1[38]} {u_adda_top/tx_tdata_RF1[39]} {u_adda_top/tx_tdata_RF1[40]} {u_adda_top/tx_tdata_RF1[41]} {u_adda_top/tx_tdata_RF1[42]} {u_adda_top/tx_tdata_RF1[43]} {u_adda_top/tx_tdata_RF1[44]} {u_adda_top/tx_tdata_RF1[45]} {u_adda_top/tx_tdata_RF1[46]} {u_adda_top/tx_tdata_RF1[47]} {u_adda_top/tx_tdata_RF1[48]} {u_adda_top/tx_tdata_RF1[49]} {u_adda_top/tx_tdata_RF1[50]} {u_adda_top/tx_tdata_RF1[51]} {u_adda_top/tx_tdata_RF1[52]} {u_adda_top/tx_tdata_RF1[53]} {u_adda_top/tx_tdata_RF1[54]} {u_adda_top/tx_tdata_RF1[55]} {u_adda_top/tx_tdata_RF1[56]} {u_adda_top/tx_tdata_RF1[57]} {u_adda_top/tx_tdata_RF1[58]} {u_adda_top/tx_tdata_RF1[59]} {u_adda_top/tx_tdata_RF1[60]} {u_adda_top/tx_tdata_RF1[61]} {u_adda_top/tx_tdata_RF1[62]} {u_adda_top/tx_tdata_RF1[63]}]]

# probe2
set_property MARK_DEBUG true [get_nets [list {u_adda_top/tx_tdata_RF2[0]} {u_adda_top/tx_tdata_RF2[1]} {u_adda_top/tx_tdata_RF2[2]} {u_adda_top/tx_tdata_RF2[3]} {u_adda_top/tx_tdata_RF2[4]} {u_adda_top/tx_tdata_RF2[5]} {u_adda_top/tx_tdata_RF2[6]} {u_adda_top/tx_tdata_RF2[7]} {u_adda_top/tx_tdata_RF2[8]} {u_adda_top/tx_tdata_RF2[9]} {u_adda_top/tx_tdata_RF2[10]} {u_adda_top/tx_tdata_RF2[11]} {u_adda_top/tx_tdata_RF2[12]} {u_adda_top/tx_tdata_RF2[13]} {u_adda_top/tx_tdata_RF2[14]} {u_adda_top/tx_tdata_RF2[15]} {u_adda_top/tx_tdata_RF2[16]} {u_adda_top/tx_tdata_RF2[17]} {u_adda_top/tx_tdata_RF2[18]} {u_adda_top/tx_tdata_RF2[19]} {u_adda_top/tx_tdata_RF2[20]} {u_adda_top/tx_tdata_RF2[21]} {u_adda_top/tx_tdata_RF2[22]} {u_adda_top/tx_tdata_RF2[23]} {u_adda_top/tx_tdata_RF2[24]} {u_adda_top/tx_tdata_RF2[25]} {u_adda_top/tx_tdata_RF2[26]} {u_adda_top/tx_tdata_RF2[27]} {u_adda_top/tx_tdata_RF2[28]} {u_adda_top/tx_tdata_RF2[29]} {u_adda_top/tx_tdata_RF2[30]} {u_adda_top/tx_tdata_RF2[31]} {u_adda_top/tx_tdata_RF2[32]} {u_adda_top/tx_tdata_RF2[33]} {u_adda_top/tx_tdata_RF2[34]} {u_adda_top/tx_tdata_RF2[35]} {u_adda_top/tx_tdata_RF2[36]} {u_adda_top/tx_tdata_RF2[37]} {u_adda_top/tx_tdata_RF2[38]} {u_adda_top/tx_tdata_RF2[39]} {u_adda_top/tx_tdata_RF2[40]} {u_adda_top/tx_tdata_RF2[41]} {u_adda_top/tx_tdata_RF2[42]} {u_adda_top/tx_tdata_RF2[43]} {u_adda_top/tx_tdata_RF2[44]} {u_adda_top/tx_tdata_RF2[45]} {u_adda_top/tx_tdata_RF2[46]} {u_adda_top/tx_tdata_RF2[47]} {u_adda_top/tx_tdata_RF2[48]} {u_adda_top/tx_tdata_RF2[49]} {u_adda_top/tx_tdata_RF2[50]} {u_adda_top/tx_tdata_RF2[51]} {u_adda_top/tx_tdata_RF2[52]} {u_adda_top/tx_tdata_RF2[53]} {u_adda_top/tx_tdata_RF2[54]} {u_adda_top/tx_tdata_RF2[55]} {u_adda_top/tx_tdata_RF2[56]} {u_adda_top/tx_tdata_RF2[57]} {u_adda_top/tx_tdata_RF2[58]} {u_adda_top/tx_tdata_RF2[59]} {u_adda_top/tx_tdata_RF2[60]} {u_adda_top/tx_tdata_RF2[61]} {u_adda_top/tx_tdata_RF2[62]} {u_adda_top/tx_tdata_RF2[63]}]]
create_debug_port u_ila_dac_out probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_dac_out/probe2]
set_property port_width 64 [get_debug_ports u_ila_dac_out/probe2]
connect_debug_port u_ila_dac_out/probe2 [get_nets [list {u_adda_top/tx_tdata_RF2[0]} {u_adda_top/tx_tdata_RF2[1]} {u_adda_top/tx_tdata_RF2[2]} {u_adda_top/tx_tdata_RF2[3]} {u_adda_top/tx_tdata_RF2[4]} {u_adda_top/tx_tdata_RF2[5]} {u_adda_top/tx_tdata_RF2[6]} {u_adda_top/tx_tdata_RF2[7]} {u_adda_top/tx_tdata_RF2[8]} {u_adda_top/tx_tdata_RF2[9]} {u_adda_top/tx_tdata_RF2[10]} {u_adda_top/tx_tdata_RF2[11]} {u_adda_top/tx_tdata_RF2[12]} {u_adda_top/tx_tdata_RF2[13]} {u_adda_top/tx_tdata_RF2[14]} {u_adda_top/tx_tdata_RF2[15]} {u_adda_top/tx_tdata_RF2[16]} {u_adda_top/tx_tdata_RF2[17]} {u_adda_top/tx_tdata_RF2[18]} {u_adda_top/tx_tdata_RF2[19]} {u_adda_top/tx_tdata_RF2[20]} {u_adda_top/tx_tdata_RF2[21]} {u_adda_top/tx_tdata_RF2[22]} {u_adda_top/tx_tdata_RF2[23]} {u_adda_top/tx_tdata_RF2[24]} {u_adda_top/tx_tdata_RF2[25]} {u_adda_top/tx_tdata_RF2[26]} {u_adda_top/tx_tdata_RF2[27]} {u_adda_top/tx_tdata_RF2[28]} {u_adda_top/tx_tdata_RF2[29]} {u_adda_top/tx_tdata_RF2[30]} {u_adda_top/tx_tdata_RF2[31]} {u_adda_top/tx_tdata_RF2[32]} {u_adda_top/tx_tdata_RF2[33]} {u_adda_top/tx_tdata_RF2[34]} {u_adda_top/tx_tdata_RF2[35]} {u_adda_top/tx_tdata_RF2[36]} {u_adda_top/tx_tdata_RF2[37]} {u_adda_top/tx_tdata_RF2[38]} {u_adda_top/tx_tdata_RF2[39]} {u_adda_top/tx_tdata_RF2[40]} {u_adda_top/tx_tdata_RF2[41]} {u_adda_top/tx_tdata_RF2[42]} {u_adda_top/tx_tdata_RF2[43]} {u_adda_top/tx_tdata_RF2[44]} {u_adda_top/tx_tdata_RF2[45]} {u_adda_top/tx_tdata_RF2[46]} {u_adda_top/tx_tdata_RF2[47]} {u_adda_top/tx_tdata_RF2[48]} {u_adda_top/tx_tdata_RF2[49]} {u_adda_top/tx_tdata_RF2[50]} {u_adda_top/tx_tdata_RF2[51]} {u_adda_top/tx_tdata_RF2[52]} {u_adda_top/tx_tdata_RF2[53]} {u_adda_top/tx_tdata_RF2[54]} {u_adda_top/tx_tdata_RF2[55]} {u_adda_top/tx_tdata_RF2[56]} {u_adda_top/tx_tdata_RF2[57]} {u_adda_top/tx_tdata_RF2[58]} {u_adda_top/tx_tdata_RF2[59]} {u_adda_top/tx_tdata_RF2[60]} {u_adda_top/tx_tdata_RF2[61]} {u_adda_top/tx_tdata_RF2[62]} {u_adda_top/tx_tdata_RF2[63]}]]

# probe3
set_property MARK_DEBUG true [get_nets [list {u_adda_top/tx_tdata_RF3[0]} {u_adda_top/tx_tdata_RF3[1]} {u_adda_top/tx_tdata_RF3[2]} {u_adda_top/tx_tdata_RF3[3]} {u_adda_top/tx_tdata_RF3[4]} {u_adda_top/tx_tdata_RF3[5]} {u_adda_top/tx_tdata_RF3[6]} {u_adda_top/tx_tdata_RF3[7]} {u_adda_top/tx_tdata_RF3[8]} {u_adda_top/tx_tdata_RF3[9]} {u_adda_top/tx_tdata_RF3[10]} {u_adda_top/tx_tdata_RF3[11]} {u_adda_top/tx_tdata_RF3[12]} {u_adda_top/tx_tdata_RF3[13]} {u_adda_top/tx_tdata_RF3[14]} {u_adda_top/tx_tdata_RF3[15]} {u_adda_top/tx_tdata_RF3[16]} {u_adda_top/tx_tdata_RF3[17]} {u_adda_top/tx_tdata_RF3[18]} {u_adda_top/tx_tdata_RF3[19]} {u_adda_top/tx_tdata_RF3[20]} {u_adda_top/tx_tdata_RF3[21]} {u_adda_top/tx_tdata_RF3[22]} {u_adda_top/tx_tdata_RF3[23]} {u_adda_top/tx_tdata_RF3[24]} {u_adda_top/tx_tdata_RF3[25]} {u_adda_top/tx_tdata_RF3[26]} {u_adda_top/tx_tdata_RF3[27]} {u_adda_top/tx_tdata_RF3[28]} {u_adda_top/tx_tdata_RF3[29]} {u_adda_top/tx_tdata_RF3[30]} {u_adda_top/tx_tdata_RF3[31]} {u_adda_top/tx_tdata_RF3[32]} {u_adda_top/tx_tdata_RF3[33]} {u_adda_top/tx_tdata_RF3[34]} {u_adda_top/tx_tdata_RF3[35]} {u_adda_top/tx_tdata_RF3[36]} {u_adda_top/tx_tdata_RF3[37]} {u_adda_top/tx_tdata_RF3[38]} {u_adda_top/tx_tdata_RF3[39]} {u_adda_top/tx_tdata_RF3[40]} {u_adda_top/tx_tdata_RF3[41]} {u_adda_top/tx_tdata_RF3[42]} {u_adda_top/tx_tdata_RF3[43]} {u_adda_top/tx_tdata_RF3[44]} {u_adda_top/tx_tdata_RF3[45]} {u_adda_top/tx_tdata_RF3[46]} {u_adda_top/tx_tdata_RF3[47]} {u_adda_top/tx_tdata_RF3[48]} {u_adda_top/tx_tdata_RF3[49]} {u_adda_top/tx_tdata_RF3[50]} {u_adda_top/tx_tdata_RF3[51]} {u_adda_top/tx_tdata_RF3[52]} {u_adda_top/tx_tdata_RF3[53]} {u_adda_top/tx_tdata_RF3[54]} {u_adda_top/tx_tdata_RF3[55]} {u_adda_top/tx_tdata_RF3[56]} {u_adda_top/tx_tdata_RF3[57]} {u_adda_top/tx_tdata_RF3[58]} {u_adda_top/tx_tdata_RF3[59]} {u_adda_top/tx_tdata_RF3[60]} {u_adda_top/tx_tdata_RF3[61]} {u_adda_top/tx_tdata_RF3[62]} {u_adda_top/tx_tdata_RF3[63]}]]
create_debug_port u_ila_dac_out probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_dac_out/probe3]
set_property port_width 64 [get_debug_ports u_ila_dac_out/probe3]
connect_debug_port u_ila_dac_out/probe3 [get_nets [list {u_adda_top/tx_tdata_RF3[0]} {u_adda_top/tx_tdata_RF3[1]} {u_adda_top/tx_tdata_RF3[2]} {u_adda_top/tx_tdata_RF3[3]} {u_adda_top/tx_tdata_RF3[4]} {u_adda_top/tx_tdata_RF3[5]} {u_adda_top/tx_tdata_RF3[6]} {u_adda_top/tx_tdata_RF3[7]} {u_adda_top/tx_tdata_RF3[8]} {u_adda_top/tx_tdata_RF3[9]} {u_adda_top/tx_tdata_RF3[10]} {u_adda_top/tx_tdata_RF3[11]} {u_adda_top/tx_tdata_RF3[12]} {u_adda_top/tx_tdata_RF3[13]} {u_adda_top/tx_tdata_RF3[14]} {u_adda_top/tx_tdata_RF3[15]} {u_adda_top/tx_tdata_RF3[16]} {u_adda_top/tx_tdata_RF3[17]} {u_adda_top/tx_tdata_RF3[18]} {u_adda_top/tx_tdata_RF3[19]} {u_adda_top/tx_tdata_RF3[20]} {u_adda_top/tx_tdata_RF3[21]} {u_adda_top/tx_tdata_RF3[22]} {u_adda_top/tx_tdata_RF3[23]} {u_adda_top/tx_tdata_RF3[24]} {u_adda_top/tx_tdata_RF3[25]} {u_adda_top/tx_tdata_RF3[26]} {u_adda_top/tx_tdata_RF3[27]} {u_adda_top/tx_tdata_RF3[28]} {u_adda_top/tx_tdata_RF3[29]} {u_adda_top/tx_tdata_RF3[30]} {u_adda_top/tx_tdata_RF3[31]} {u_adda_top/tx_tdata_RF3[32]} {u_adda_top/tx_tdata_RF3[33]} {u_adda_top/tx_tdata_RF3[34]} {u_adda_top/tx_tdata_RF3[35]} {u_adda_top/tx_tdata_RF3[36]} {u_adda_top/tx_tdata_RF3[37]} {u_adda_top/tx_tdata_RF3[38]} {u_adda_top/tx_tdata_RF3[39]} {u_adda_top/tx_tdata_RF3[40]} {u_adda_top/tx_tdata_RF3[41]} {u_adda_top/tx_tdata_RF3[42]} {u_adda_top/tx_tdata_RF3[43]} {u_adda_top/tx_tdata_RF3[44]} {u_adda_top/tx_tdata_RF3[45]} {u_adda_top/tx_tdata_RF3[46]} {u_adda_top/tx_tdata_RF3[47]} {u_adda_top/tx_tdata_RF3[48]} {u_adda_top/tx_tdata_RF3[49]} {u_adda_top/tx_tdata_RF3[50]} {u_adda_top/tx_tdata_RF3[51]} {u_adda_top/tx_tdata_RF3[52]} {u_adda_top/tx_tdata_RF3[53]} {u_adda_top/tx_tdata_RF3[54]} {u_adda_top/tx_tdata_RF3[55]} {u_adda_top/tx_tdata_RF3[56]} {u_adda_top/tx_tdata_RF3[57]} {u_adda_top/tx_tdata_RF3[58]} {u_adda_top/tx_tdata_RF3[59]} {u_adda_top/tx_tdata_RF3[60]} {u_adda_top/tx_tdata_RF3[61]} {u_adda_top/tx_tdata_RF3[62]} {u_adda_top/tx_tdata_RF3[63]}]]

# probe4
set_property MARK_DEBUG true [get_nets {u_adda_top/ad9144_fifo_empty}]
create_debug_port u_ila_dac_out probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_dac_out/probe4]
set_property port_width 1 [get_debug_ports u_ila_dac_out/probe4]
connect_debug_port u_ila_dac_out/probe4 [get_nets {u_adda_top/ad9144_fifo_empty}]

# probe5
set_property MARK_DEBUG true [get_nets -of_objects [get_pins {u_adda_top/dac_fifo_16in64out_ch0/rst}]]
create_debug_port u_ila_dac_out probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_dac_out/probe5]
set_property port_width 1 [get_debug_ports u_ila_dac_out/probe5]
connect_debug_port u_ila_dac_out/probe5 [get_nets -of_objects [get_pins {u_adda_top/dac_fifo_16in64out_ch0/rst}]]

# probe6
set_property MARK_DEBUG true [get_nets -of_objects [get_pins {u_adda_top/adda_top_i/ad9144_core_reset}]]
create_debug_port u_ila_dac_out probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_dac_out/probe6]
set_property port_width 1 [get_debug_ports u_ila_dac_out/probe6]
connect_debug_port u_ila_dac_out/probe6 [get_nets -of_objects [get_pins {u_adda_top/adda_top_i/ad9144_core_reset}]]

# probe7
set_property MARK_DEBUG true [get_nets [list ad9144_tx_en0_OBUF ad9144_tx_en1_OBUF]]
create_debug_port u_ila_dac_out probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_dac_out/probe7]
set_property port_width 2 [get_debug_ports u_ila_dac_out/probe7]
connect_debug_port u_ila_dac_out/probe7 [get_nets [list ad9144_tx_en0_OBUF ad9144_tx_en1_OBUF]]

# probe8
set_property MARK_DEBUG true [get_nets {u_adda_top/ad9144_tx_data_tready}]
create_debug_port u_ila_dac_out probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_dac_out/probe8]
set_property port_width 1 [get_debug_ports u_ila_dac_out/probe8]
connect_debug_port u_ila_dac_out/probe8 [get_nets {u_adda_top/ad9144_tx_data_tready}]

# probe9
set_property MARK_DEBUG true [get_nets {u_adda_top/ad9144_tx_sync_0}]
create_debug_port u_ila_dac_out probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_dac_out/probe9]
set_property port_width 1 [get_debug_ports u_ila_dac_out/probe9]
connect_debug_port u_ila_dac_out/probe9 [get_nets {u_adda_top/ad9144_tx_sync_0}]


# probe10
set_property MARK_DEBUG true [get_nets -of_objects [get_pins {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/tx_reset_done}]]
create_debug_port u_ila_dac_out probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_dac_out/probe10]
set_property port_width 1 [get_debug_ports u_ila_dac_out/probe10]
connect_debug_port u_ila_dac_out/probe10 [get_nets -of_objects [get_pins {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/tx_reset_done}]]

# GT lane 0: container 3, channel 0

# GT lane 1: container 3, channel 1

# GT lane 2: container 3, channel 2

# GT lane 3: container 3, channel 3

# GT lane 4: container 4, channel 0

# GT lane 5: container 4, channel 1

# GT lane 6: container 4, channel 2

# GT lane 7: container 4, channel 3

# The explicit pin list is ordered lane0 bit0, lane0 bit1, ... lane7 bit1.
set_property MARK_DEBUG true [get_nets -of_objects [get_pins [list {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[3].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[0].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[0]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[3].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[0].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[1]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[3].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[1].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[0]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[3].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[1].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[1]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[3].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[2].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[0]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[3].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[2].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[1]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[3].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[3].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[0]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[3].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[3].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[1]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[4].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[0].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[0]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[4].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[0].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[1]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[4].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[1].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[0]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[4].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[1].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[1]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[4].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[2].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[0]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[4].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[2].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[1]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[4].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[3].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[0]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[4].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[3].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[1]}]]]
create_debug_port u_ila_dac_out probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_dac_out/probe11]
set_property port_width 16 [get_debug_ports u_ila_dac_out/probe11]
connect_debug_port u_ila_dac_out/probe11 [get_nets -of_objects [get_pins [list {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[3].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[0].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[0]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[3].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[0].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[1]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[3].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[1].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[0]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[3].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[1].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[1]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[3].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[2].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[0]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[3].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[2].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[1]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[3].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[3].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[0]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[3].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[3].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[1]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[4].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[0].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[0]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[4].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[0].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[1]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[4].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[1].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[0]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[4].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[1].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[1]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[4].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[2].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[0]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[4].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[2].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[1]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[4].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[3].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[0]} {u_adda_top/adda_top_i/ad9144_sub/jesd204_phy_0/inst/jesd204_phy_block_i/adda_top_jesd204_phy_0_3_gt_i/inst/gen_gtwizard_gthe3_top.adda_top_jesd204_phy_0_3_gt_gtwizard_gthe3_inst/gen_gtwizard_gthe3.gen_channel_container[4].gen_enabled_channel.gthe3_channel_wrapper_inst/channel_inst/gthe3_channel_gen.gen_gthe3_channel_inst[3].GTHE3_CHANNEL_PRIM_INST/TXBUFSTATUS[1]}]]]
# END AD9144_OUTPUT_ILA
