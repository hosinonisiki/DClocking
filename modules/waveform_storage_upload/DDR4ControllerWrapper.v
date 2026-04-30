`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/12/26 10:32:46
// Design Name: 
// Module Name: DDR4ControllerWrapper
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


// DDR4控制器包装模块
// ============================================
module DDR4ControllerWrapper (
    // 系统接口
    input  wire        sys_clk_i,
    input  wire        sys_rst,
   
     // DDR4物理接口
   output wire         c0_ddr4_act_n,
   output wire [16:0]  c0_ddr4_adr,
   output wire [1:0]   c0_ddr4_ba,
   output wire [0:0]   c0_ddr4_bg,
   output wire [0:0]   c0_ddr4_cke,
   output wire [0:0]   c0_ddr4_odt,
   output wire [0:0]   c0_ddr4_cs_n,
   output wire [0:0]   c0_ddr4_ck_t,
   output wire [0:0]   c0_ddr4_ck_c,
   output wire         c0_ddr4_reset_n,
   inout  wire [7:0]   c0_ddr4_dm_dbi_n,
   inout  wire [63:0]  c0_ddr4_dq,
   inout  wire [7:0]   c0_ddr4_dqs_c,
   inout  wire [7:0]   c0_ddr4_dqs_t,

// output                c0_init_calib_complete,
   output wire         c0_ddr4_ui_clk,
   output wire         c0_ddr4_ui_clk_sync_rst,
// output               dbg_clk,
   // AXI从接口
   // Slave Interface Write Address Ports
   input  wire          c0_ddr4_aresetn,
// input  [3:0]      c0_ddr4_s_axi_awid,
   input  wire [31:0]   c0_ddr4_s_axi_awaddr,
   input  wire [7:0]    c0_ddr4_s_axi_awlen,
   input  wire [2:0]    c0_ddr4_s_axi_awsize,
   input  wire [1:0]    c0_ddr4_s_axi_awburst,
   input  wire [0:0]    c0_ddr4_s_axi_awlock,
   input  wire [3:0]    c0_ddr4_s_axi_awcache,
   input  wire [2:0]    c0_ddr4_s_axi_awprot,
   input  wire [3:0]    c0_ddr4_s_axi_awqos,
   input  wire          c0_ddr4_s_axi_awvalid,
   output wire          c0_ddr4_s_axi_awready,
   // Slave Interface Write Data Ports
   input  wire [63:0]   c0_ddr4_s_axi_wdata,
   input  wire [7:0]    c0_ddr4_s_axi_wstrb,
   input  wire          c0_ddr4_s_axi_wlast,
   input  wire          c0_ddr4_s_axi_wvalid,
   output wire          c0_ddr4_s_axi_wready,
   // Slave Interface Write Response Ports
   input  wire          c0_ddr4_s_axi_bready,
   output wire [3:0]    c0_ddr4_s_axi_bid,
   output wire [1:0]    c0_ddr4_s_axi_bresp,
   output               c0_ddr4_s_axi_bvalid,
   // Slave Interface Read Address Ports
   input  wire [3:0]    c0_ddr4_s_axi_arid,
   input  wire [31:0]   c0_ddr4_s_axi_araddr,
   input  wire [7:0]    c0_ddr4_s_axi_arlen,
   input  wire [2:0]    c0_ddr4_s_axi_arsize,
   input  wire [1:0]    c0_ddr4_s_axi_arburst,
   input  wire [0:0]    c0_ddr4_s_axi_arlock,
   input  wire [3:0]    c0_ddr4_s_axi_arcache,
   input  wire [2:0]    c0_ddr4_s_axi_arprot,
   input  wire [3:0]    c0_ddr4_s_axi_arqos,
   input  wire          c0_ddr4_s_axi_arvalid,
   output wire          c0_ddr4_s_axi_arready,
   // Slave Interface Read Data Ports
   input  wire          c0_ddr4_s_axi_rready,
   output wire [3:0]    c0_ddr4_s_axi_rid,
   output wire [63:0]   c0_ddr4_s_axi_rdata,
   output wire [1:0]    c0_ddr4_s_axi_rresp,
   output wire          c0_ddr4_s_axi_rlast,
   output wire          c0_ddr4_s_axi_rvalid
   // Debug Port
//   output wire [511:0]             dbg_bus 
    
);

    // ============================================
    // Xilinx MIG DDR4控制器实例
    // ============================================
   
   ddr4_0  inst (
       .sys_rst                (sys_rst),
       .c0_sys_clk_i           (sys_clk_i),           
       .c0_init_calib_complete (),
       .c0_ddr4_act_n          (c0_ddr4_act_n),
       .c0_ddr4_adr            (c0_ddr4_adr),
       .c0_ddr4_ba             (c0_ddr4_ba),
       .c0_ddr4_bg             (c0_ddr4_bg),
       .c0_ddr4_cke            (c0_ddr4_cke),
       .c0_ddr4_odt            (c0_ddr4_odt),
       .c0_ddr4_cs_n           (c0_ddr4_cs_n),
       .c0_ddr4_ck_t           (c0_ddr4_ck_t),
       .c0_ddr4_ck_c           (c0_ddr4_ck_c),
       .c0_ddr4_reset_n        (c0_ddr4_reset_n),
       .c0_ddr4_dm_dbi_n       (c0_ddr4_dm_dbi_n),
       .c0_ddr4_dq             (c0_ddr4_dq),
       .c0_ddr4_dqs_c          (c0_ddr4_dqs_c),
       .c0_ddr4_dqs_t          (c0_ddr4_dqs_t),
       .c0_ddr4_ui_clk                (c0_ddr4_ui_clk),
       .c0_ddr4_ui_clk_sync_rst       (c0_ddr4_ui_clk_sync_rst),
       .dbg_clk                                    (),

       .c0_ddr4_aresetn                                (c0_ddr4_aresetn),
       // Slave Interface Write Address Ports
       .c0_ddr4_s_axi_awid                             ({1'b0,1'b0,1'b0,1'b0}),
       .c0_ddr4_s_axi_awaddr                           (c0_ddr4_s_axi_awaddr),
       .c0_ddr4_s_axi_awlen                            (c0_ddr4_s_axi_awlen),
       .c0_ddr4_s_axi_awsize                           (c0_ddr4_s_axi_awsize),
       .c0_ddr4_s_axi_awburst                          (c0_ddr4_s_axi_awburst),
       .c0_ddr4_s_axi_awlock                           (c0_ddr4_s_axi_awlock),
       .c0_ddr4_s_axi_awcache                          (c0_ddr4_s_axi_awcache),
       .c0_ddr4_s_axi_awprot                           (c0_ddr4_s_axi_awprot),
       .c0_ddr4_s_axi_awqos                            (c0_ddr4_s_axi_awqos),
       .c0_ddr4_s_axi_awvalid                          (c0_ddr4_s_axi_awvalid),
       .c0_ddr4_s_axi_awready                          (c0_ddr4_s_axi_awready),
       // Slave Interface Write Data Ports
       .c0_ddr4_s_axi_wdata                            (c0_ddr4_s_axi_wdata),
       .c0_ddr4_s_axi_wstrb                            (c0_ddr4_s_axi_wstrb),
       .c0_ddr4_s_axi_wlast                            (c0_ddr4_s_axi_wlast),
       .c0_ddr4_s_axi_wvalid                           (c0_ddr4_s_axi_wvalid),
       .c0_ddr4_s_axi_wready                           (c0_ddr4_s_axi_wready),
       // Slave Interface Write Response Ports
       .c0_ddr4_s_axi_bid                              (c0_ddr4_s_axi_bid),
       .c0_ddr4_s_axi_bresp                            (c0_ddr4_s_axi_bresp),
       .c0_ddr4_s_axi_bvalid                           (c0_ddr4_s_axi_bvalid),
       .c0_ddr4_s_axi_bready                           (c0_ddr4_s_axi_bready),
       // Slave Interface Read Address Ports
       .c0_ddr4_s_axi_arid                             (c0_ddr4_s_axi_arid),
       .c0_ddr4_s_axi_araddr                           (c0_ddr4_s_axi_araddr),
       .c0_ddr4_s_axi_arlen                            (c0_ddr4_s_axi_arlen),
       .c0_ddr4_s_axi_arsize                           (c0_ddr4_s_axi_arsize),
       .c0_ddr4_s_axi_arburst                          (c0_ddr4_s_axi_arburst),
       .c0_ddr4_s_axi_arlock                           (c0_ddr4_s_axi_arlock),
       .c0_ddr4_s_axi_arcache                          (c0_ddr4_s_axi_arcache),
       .c0_ddr4_s_axi_arprot                           (c0_ddr4_s_axi_arprot),
       .c0_ddr4_s_axi_arqos                            (c0_ddr4_s_axi_arqos),
       .c0_ddr4_s_axi_arvalid                          (c0_ddr4_s_axi_arvalid),
       .c0_ddr4_s_axi_arready                          (c0_ddr4_s_axi_arready),
       // Slave Interface Read Data Ports
       .c0_ddr4_s_axi_rid                              (c0_ddr4_s_axi_rid),
       .c0_ddr4_s_axi_rdata                            (c0_ddr4_s_axi_rdata),
       .c0_ddr4_s_axi_rresp                            (c0_ddr4_s_axi_rresp),
       .c0_ddr4_s_axi_rlast                            (c0_ddr4_s_axi_rlast),
       .c0_ddr4_s_axi_rvalid                           (c0_ddr4_s_axi_rvalid),
       .c0_ddr4_s_axi_rready                           (c0_ddr4_s_axi_rready),
       // Debug Port
       .dbg_bus               () 
   ); 


endmodule