`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/12/29 14:12:48
// Design Name: 
// Module Name: mem_ethernet_top
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


module mem_ethernet_top #(
    parameter DATA_WIDTH = 64,
    parameter ADDR_WIDTH = 32,
    parameter ID_WIDTH   = 4
)
(
      // 系统时钟与复位
    input  wire        sys_clk,           // 系统时钟 200MHz
    input  wire        sys_clk_125M,
    input  wire        adc_clk,
    input  wire        rst,         // 系统复位
    // 内存接口 (DDR4)
    output wire        DDR4_act_n,
    output wire[16:0]  DDR4_adr,
    output wire[1:0]   DDR4_ba,
    output wire[0:0]   DDR4_bg,
    output wire[0:0]   DDR4_ck_c,
    output wire[0:0]   DDR4_ck_t,
    output wire[0:0]   DDR4_cke,
    output wire[0:0]   DDR4_cs_n,
    inout  wire[7:0]   DDR4_dm_n,
    inout  wire[63:0]  DDR4_dq,
    inout  wire[7:0]   DDR4_dqs_c,
    inout  wire[7:0]   DDR4_dqs_t,
    output wire[0:0]   DDR4_odt,
    output wire        DDR4_reset_n,          
    // 以太网接口 (RGMII)
    output wire        e_mdc,
    inout  wire        e_mdio,
    output reg         e_reset,
			
    // 发送接口
    output wire        rgmii_txc,
    output wire [3:0]  rgmii_txd,
    output wire        rgmii_tx_ctl,
    // 接收接口 (用于配置和控制)
    input  wire        rgmii_rxc,
    input  wire [3:0]  rgmii_rxd,
    input  wire        rgmii_rx_ctl,
   //交互 
    output  wire        eth_ready,
    output  wire        upload_complete,
  
    input  wire [15:0] mem_write_data,
    input  wire        mem_write_valid, 
    input  wire        capture_start,
    input  wire[15:0]  BUFFER0_BASE,
    input  wire[15:0]  BUFFER1_BASE,
    input  wire[31:0]  sample_len//采样长度  
);
    assign rst_n = ~ rst;
    wire         ui_clk;
    wire         ui_rst;
    
    wire [15:0]  fifo_read_data;       // 读取数据
    wire         fifo_read_en;            //FIFO读使能 
    wire [15:0]  read_usedw ;      //FIFO数据可读量    
    wire         read_req_ack;//读ADC采集数据应答
    wire         read_req;//读ADC数据请求
    wire         ad_sample_ack;//ADC采样应答
   // ============================================
    // 内存控制器 (双缓冲架构)
    // ============================================
    Memctrl_top u_memory_controller (
     // 系统时钟与复位
        .sys_clk                (sys_clk),
        .adc_clk                (adc_clk),          // 系统时钟 250MHz
        .gmii_tx_clk            (rgmii_txc),
        .rst                  (rst),        // 系统复位
        //寄存器
        .BUFFER0_BASE           (BUFFER0_BASE),
        .BUFFER1_BASE           (BUFFER1_BASE),
        .sample_len             (sample_len),//采样长度   
         // 用户控制接口
        .capture_start          (capture_start),    // 捕获开始
    //    .capture_en(capture_en),   // 捕获使能
    //    .upload_start(upload_start),     // 上传开始
    //    .upload_en(upload_en),    // 上传使能
        
        // 数据输入接口（16位采样数据）
        .write_data_i           (mem_write_data),       // 写入数据
        .write_valid_i          (mem_write_valid),      // 数据有效
        
        // 数据输出接口（64位读取数据）
        .read_data              (fifo_read_data),           //FIFO读出皿8bit数据/
        .read_en                (fifo_read_en),            //FIFO读使能 
        .read_usedw             (read_usedw      ),          //FIFO中的数据数量
        .read_req_ack           (read_req_ack    ),
        .read_req               (read_req        ),
        .ad_sample_ack          (ad_sample_ack   ),   
      
             // DDR4物理接口
        .DDR4_act_n             (DDR4_act_n),
        .DDR4_adr               (DDR4_adr),
        .DDR4_ba                (DDR4_ba),
        .DDR4_bg                (DDR4_bg),
        .DDR4_ck_c              (DDR4_ck_c),
        .DDR4_ck_t              (DDR4_ck_t),
        .DDR4_cke               (DDR4_cke),
        .DDR4_cs_n              (DDR4_cs_n),
        .DDR4_dm_n              (DDR4_dm_n),
        .DDR4_dq                (DDR4_dq),
        .DDR4_dqs_c             (DDR4_dqs_c),
        .DDR4_dqs_t             (DDR4_dqs_t),
        .DDR4_odt               (DDR4_odt),
        .DDR4_reset_n           (DDR4_reset_n),  
        .ui_clk                 (ui_clk),
        .ui_rst                 (ui_rst)
    );
  
  
    // ============================================
    // 以太网传输模块
    // ============================================
  
    ethernet_test eth1(
        .sys_clk                (sys_clk_125M),    
        .rst_n                  (rst_n      ),                   
        // 数据输入接口
//        .data_i             (mem_read_data[15:0]),  // 使用低16位
//        .data_valid_i       (mem_read_valid && upload_en),
//        .data_ack_o         (eth_data_ack),
        .fifo_data              (fifo_read_data       ),           //FIFO读出皿8bit数据/
        .fifo_data_count        (read_usedw      ),          //FIFO中的数据数量
        .fifo_rd_en             (fifo_read_en         ),             //FIFO读使胿
        
        .read_req_ack           (read_req_ack    ),
        .read_req               (read_req        ),
        .ad_sample_req          (capture_start_i   ),
        .ad_sample_ack          (ad_sample_ack   ),
        .sample_len             (sample_len      ),    
           
        .e_mdc                  (e_mdc      ),
        .e_mdio                 (e_mdio     ),
        .rgmii_txd              (rgmii_txd  ),
        .rgmii_txctl            (rgmii_tx_ctl),
        .rgmii_txc              (rgmii_txc  ),
        .rgmii_rxd              (rgmii_rxd  ),
        .rgmii_rxctl            (rgmii_rx_ctl),
        .rgmii_rxc              (rgmii_rxc  ),
        .led 	                ( 	  ),
        .ready_o                (eth_ready),
        .error_o                (eth_error)
 );  
    
    
    
endmodule
