`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2026/03/06 09:31:45
// Design Name: 
// Module Name: wrapper_KU060_custom
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
module wrapper_KU060_custom(
    input           sysclk_p ,
    input           sysclk_n ,
    input           rst   ,
    input           sys_mmcm_sel_cmd_raw,
 
    input   [3:0]   ads54j60_A_p    ,
    input   [3:0]   ads54j60_A_n    ,
    input   [3:0]   ads54j60_B_p    ,
    input   [3:0]   ads54j60_B_n    ,
    
    input           gty224_clk_p    ,
    input           gty224_clk_n    ,    
    input           gty225_clk_p    ,
    input           gty225_clk_n    ,
    

    input   [1:0]   ads54j69_A_p    ,
    input   [1:0]   ads54j69_A_n    ,
    input   [1:0]   ads54j69_B_p    ,
    input   [1:0]   ads54j69_B_n    ,
    
    input           gty226_clk_p    ,
    input           gty226_clk_n    ,    
    input           gty227_clk_p    ,
    input           gty227_clk_n    ,  
    
    output  [7:0]   ad9144_da_p     ,
    output  [7:0]   ad9144_da_n     ,
    
    input           gty127_clk_p    ,
    input           gty127_clk_n    ,    
//    input           gty128_clk_p    ,
//    input           gty128_clk_n    ,  
   
    input           sysrefclk_p     ,   //lmk04828_clk1
    input           sysrefclk_n     ,    
    input           coreclk_p       ,   //lmk04828_clk2
    input           coreclk_n       ,
    
    //spi lmk04828
    output  	    lmk048_clk		,
    output  		lmk048_cs		,
    output   		lmk048_mosi		,
    output    	    lmk048_sync 	,
    input    	    lmk048_ld1 		,
    input    	    lmk048_ld2 		,
    //spi adc  ads54j60
    output 			ads54j60_sclk	,
    output 			ads54j60_sdio	,
    output 			ads54j60_cs		,
    input  			ads54j60_sdin	,
    output 			ads54j60_syncse	,
    output          ads54j60_reset  ,
    //spi adc  ads54j69
    output 			ads54j69_sclk	,
    output 			ads54j69_sdio	,
    output 			ads54j69_cs		,
    input  			ads54j69_sdin	,
    output 			ads54j69_syncse	,
    output          ads54j69_reset  ,
    //spi dac  ad9144
    output 			ad9144_sclk	    ,
    input 			ad9144_miso   	,
    output 			ad9144_mosi		,
    output  		ad9144_irq   	,
    output 			ad9144_cs   	,
    output          ad9144_tx_en0   ,
    output          ad9144_tx_en1   ,
    input 			da_sync_out0_p  ,
    input 			da_sync_out0_n  ,
    input 			da_sync_out1_p  ,
    input 			da_sync_out1_n  ,
    output  [3:0]   rf_out_en,
    output  [5:0]   user_led,
    output          uart_txd,  
    input           uart_rxd
);
    wire	[15:0] ads54j69_adc_data_ch0;
    wire	[15:0] ads54j69_adc_data_ch1;
    wire		   ads54j69_adc_valid;
    //j60
    wire	[15:0] ads54j60_adc_data_ch0;
    wire	[15:0] ads54j60_adc_data_ch1;
    wire		   ads54j60_adc_valid ;
    
    //ad9144 
    wire	[15:0]ad9144_tx_data_ch0; //sample 1G   
    wire	[15:0]ad9144_tx_data_ch1;
    wire	[15:0]ad9144_tx_data_ch2;
    wire	[15:0]ad9144_tx_data_ch3;            
    wire		   ad9144_tx_valid; 
    
    wire sys_rst;    
    wire sys_clk_in_buf;
    wire sys_clk_in;
    wire sys_clk_buf;
    wire sys_clk_125M_buf;
    wire sys_clk_250M_buf;
    wire sys_clk_500M_buf;
    wire sys_clk_locked;
    wire sys_clk;
    wire sys_clk_125M;
    wire sys_clk_250M;
    wire sys_clk_500M;
    wire sys_mmcm_sel_cmd_buf;
    wire sys_mmcm_sel_cmd;
    wire sys_mmcm_sel;
    wire sys_rst_raw;
    wire sys_rst_bar;
    wire sys_mmcm_rst;
    
//clk
 
//IBUFDS #(
//    .DIFF_TERM("FALSE"),        // HR Bank 不支持，必须设为 FALSE
//    .IBUF_LOW_PWR("TRUE"),
//    .IOSTANDARD("DIFF_SSTL18_I") // 改回不带 _DCI 的标准
//)core_clk_ibufds (
//    .O  (core_clk_in_buf),        // 转换后的单端时钟
//    .I  (coreclk_p),             // 差分正端（P）
//    .IB (coreclk_n)              // 差分负端（N）
//);
IBUFDS core_clk_ibufds (
    .O  (core_clk_in_buf),        // 转换后的单端时钟
    .I  (coreclk_p),             // 差分正端（P）
    .IB (coreclk_n)              // 差分负端（N）
);
 BUFG core_clk_in_bufg (
    .I (core_clk_in_buf),
    .O (core_clk)
); 
    

         
    board_ku060_adda_top  u_adda_top(  
        .ads54j60_A_n(ads54j60_A_n),
        .ads54j60_A_p(ads54j60_A_p),
        .ads54j60_B_n(ads54j60_B_n),
        .ads54j60_B_p(ads54j60_B_p), 
        
        .gty224_clk_n(gty224_clk_n),
        .gty224_clk_p(gty224_clk_p),
        .gty225_clk_n(gty225_clk_n),
        .gty225_clk_p(gty225_clk_p), 
            
        .ads54j69_A_n(ads54j69_A_n),
        .ads54j69_A_p(ads54j69_A_p),        
        .ads54j69_B_n(ads54j69_B_n),
        .ads54j69_B_p(ads54j69_B_p),
        .gty226_clk_n(gty226_clk_n),
        .gty226_clk_p(gty226_clk_p),
        .gty227_clk_n(gty227_clk_n),
        .gty227_clk_p(gty227_clk_p),
        .ad9144_da_n(ad9144_da_n),
        .ad9144_da_p(ad9144_da_p),
        
        .gty127_clk_n(gty127_clk_n),
        .gty127_clk_p(gty127_clk_p),
        .sysclk (sys_clk),
//        .sysclk_n(sysclk_n),
//        .sysclk_p(sysclk_p),
        .sysrefclk_n(sysrefclk_n),
        .sysrefclk_p(sysrefclk_p),        
//        .coreclk_n(coreclk_n),
//        .coreclk_p(coreclk_p),
        .coreclk(core_clk),
   // LMK048 ad9144_cs
        .lmk048_clk        (lmk048_clk),
        .lmk048_cs         (lmk048_cs),
        .lmk048_mosi       (lmk048_mosi),
        .lmk048_sync       (lmk048_sync),
        .lmk048_ld1        (lmk048_ld1),
        .lmk048_ld2        (lmk048_ld2),

        // ADC ADS54J60 SPI 接口
        .ads54j60_sclk     (ads54j60_sclk),
        .ads54j60_sdio     (ads54j60_sdio),
        .ads54j60_cs       (ads54j60_cs),
        .ads54j60_sdin     (ads54j60_sdin),
        .ads54j60_syncse   (ads54j60_syncse),
        .ads54j60_reset    (ads54j60_reset),

        // ADC ADS54J69 SPI 接口
        .ads54j69_sclk     (ads54j69_sclk),
        .ads54j69_sdio     (ads54j69_sdio),
        .ads54j69_cs       (ads54j69_cs),
        .ads54j69_sdin     (ads54j69_sdin),
        .ads54j69_syncse   (ads54j69_syncse),
        .ads54j69_reset    (ads54j69_reset),

        // DAC AD9144 SPI 接口
        .ad9144_sclk       (ad9144_sclk),
        .ad9144_miso       (ad9144_miso),
        .ad9144_mosi       (ad9144_mosi),
        .ad9144_irq        (ad9144_irq),
        .ad9144_cs         (ad9144_cs),
        .ad9144_tx_en0     (ad9144_tx_en0),
        .ad9144_tx_en1     (ad9144_tx_en1),

        // 同步输入
        .da_sync_out0_p    (da_sync_out0_p),
        .da_sync_out0_n    (da_sync_out0_n),
        .da_sync_out1_p    (da_sync_out1_p),
        .da_sync_out1_n    (da_sync_out1_n),

        // 射频使能
        .rf_out_en         (rf_out_en),

        // 用户LED
//        .user_led          (user_led),
        .ads54j69_adc_data_ch0(ads54j69_adc_data_ch0),
        .ads54j69_adc_data_ch1(ads54j69_adc_data_ch1),
        .ads54j69_adc_valid(ads54j69_adc_valid),
        //j60
        .ads54j60_adc_data_ch0(ads54j60_adc_data_ch0),
        .ads54j60_adc_data_ch1(ads54j60_adc_data_ch1),
        .ads54j60_adc_valid (ads54j60_adc_valid),
        
        //ad9144 
        .ad9144_tx_data_ch0(ad9144_tx_data_ch0), //sample 1G   
        .ad9144_tx_data_ch1(ad9144_tx_data_ch1),
        .ad9144_tx_data_ch2(ad9144_tx_data_ch2),
        .ad9144_tx_data_ch3(ad9144_tx_data_ch3),        
        .ad9144_tx_valid (ad9144_tx_valid)                                                       
      
);  
    wire [63:0] adc_in;
    wire [15:0] dac_out[0:3];
    assign adc_in = {ads54j60_adc_data_ch1,ads54j60_adc_data_ch0,ads54j69_adc_data_ch1,ads54j69_adc_data_ch0};
    assign ad9144_tx_data_ch0 = dac_out[0]; 
    assign ad9144_tx_data_ch1 = dac_out[1]; 
    assign ad9144_tx_data_ch2 = dac_out[2];      
    assign ad9144_tx_data_ch3 = dac_out[3]; 
    
    wire  spi_mosi;  
    wire  spi_miso;
    wire  spi_sclk;
    wire  spi_ss;
    wire  spi_io_tri;
       
 top #(
    .ADC_channel_count(4),    // ADC 通道数，可修改
    .DAC_channel_count(4),    // DAC 通道数，可修改
    .ADC_DATA_WIDTH   (16),   // 每通道 ADC 数据位宽，可修改
    .DAC_DATA_WIDTH   (16)    // 每通道 DAC 数据位宽，可修改
) u_top (
        .clk    (sys_clk),           // 输入时钟
        .rst    (sys_rst),           // 复位
        .txd    (uart_txd),           // 串口发送
        .rxd    (uart_rxd),           // 串口接收
        .err    (err),           // 错误指示

        .mosi   (spi_mosi),          // SPI 主出从入
        .miso   (spi_miso),          // SPI 主入从出
        .sclk   (spi_sclk),          // SPI 时钟
        .ss     (spi_ss),            // 16 位从设备选择 (ss[0]..ss[15])
        .io_tri (spi_io_tri),        // 三态控制

        .adc_in (adc_in),        // ADC 输入，位宽 = ADC_channel_count
        .dac_out({dac_out[3],dac_out[2],dac_out[1],dac_out[0]})        // DAC 输出，位宽 = DAC_channel_count
);

assign user_led[0] = ~sys_mmcm_sel; 
assign user_led[1] = ~(uart_rxd & uart_txd); 
assign user_led[2] = err;
assign user_led[3] = ~(&spi_ss);              // 检测是否有任何SPI片选被选中
assign user_led[4] = sys_rst;



//clk
//IBUFDS  #(
//    .DIFF_TERM("FALSE"),       // Differential Termination
//    .IBUF_LOW_PWR("TRUE"),     // Low power="TRUE", Highest performance="FALSE" 
//    .IOSTANDARD("LVDS")     // Specify the input I/O standard
//) sys_clk_ibufds (
//    .O  (sys_clk_in_buf),        // 转换后的单端时钟
//    .I  (sysclk_p),             // 差分正端（P）
//    .IB (sysclk_n)              // 差分负端（N）
//);
IBUFDS sys_clk_ibufds (
    .O  (sys_clk_in_buf),        // 转换后的单端时钟
    .I  (sysclk_p),             // 差分正端（P）
    .IB (sysclk_n)              // 差分负端（N）
);
 BUFG sys_clk_in_bufg (
    .I (sys_clk_in_buf),
    .O (sys_clk_in)
); 
   
  sys_clk_mmcm1  sys_clk_mmcm1_inst   (
        .clk_out1 ( sys_clk_buf),
        .clk_out2 ( sys_clk_125M_buf), 
        .clk_out3 ( sys_clk_250M_buf),
        .clk_out4 ( sys_clk_500M_buf),
        .reset (sys_mmcm_rst),
        
        .locked ( sys_clk_locked),
        .clk_in1 ( sys_clk_in),
        .clk_in2 (core_clk),
//        .clk_in2_p ( coreclk_p),
//        .clk_in2_n ( coreclk_n),
        .clk_in_sel ( sys_mmcm_sel )//'1' for sys_clk, '0' for ref_clk
    );
    
   BUFGCE  sys_clk_bufgce(
        .O ( sys_clk),
        .CE(  sys_clk_locked),
        .I (  sys_clk_buf)
    );
    BUFGCE sys_clk_125M_bufgce (
        .O (  sys_clk_125M),
        .CE(  sys_clk_locked),
        .I (  sys_clk_125M_buf)
    );
    BUFGCE sys_clk_250M_bufgce (
        .O (  sys_clk_250M),
        .CE(  sys_clk_locked),
        .I (  sys_clk_250M_buf)
    );
    BUFGCE sys_clk_500M_bufgce(
        .O (  sys_clk_500M),
        .CE(  sys_clk_locked),
        .I (  sys_clk_500M_buf)
    );

    // clk selection
    IBUF sys_mmcm_sel_cmd_ibuf (
        .O ( sys_mmcm_sel_cmd_buf),
        .I ( sys_mmcm_sel_cmd_raw)
    );    
// 例化 debouncer（按键消抖模块）
debouncer #(
    .debounce_time (10),       // 10ms 消抖时间
    .default_output(1'b1)      // 默认输出高电平（按键悬空高）
) sys_mmcm_sel_cmd_debouncer (
    .clk   (sys_clk_in),
    .rst   (1'b0),             // 时钟切换期间不复位消抖器
    .keyin (sys_mmcm_sel_cmd_buf),
    .keyout(sys_mmcm_sel_cmd)
);

// 例化 sys_mmcm_sel_ctrl（MMCM 选择控制器）
sys_mmcm_sel_ctrl sys_mmcm_sel_ctrl_inst (
    .clk              (sys_clk_in),        // 不使用来自 MMCM 的时钟
    .rst              (1'b0),              // 时钟切换期间不复位控制器
    .sys_mmcm_sel_cmd (sys_mmcm_sel_cmd),
    .sys_mmcm_sel     (sys_mmcm_sel),
    .sys_mmcm_rst     (sys_mmcm_rst)
);    
   IBUF  sys_rst_ibuf(
       .O ( sys_rst_raw),      
       .I ( rst)               
   );                         
                       
  
// 例化 debouncer（复位消抖模块）
debouncer #(
    .debounce_time (10),        // 10ms 消抖时间
    .default_output(1'b0)       // 默认输出低电平
) sys_rst_debouncer (
    .clk   (sys_clk),
    .rst   (!sys_clk_locked),   // 上电时复位系统（取反时钟锁定信号）
    .keyin (sys_rst_raw),       // 注意：若端口名为 "input"，在 Verilog 中是关键字，可能需要转义或修改模块端口名
    .keyout(sys_rst_bar)
);    
    
 assign  sys_rst = ~ sys_rst_bar;     
 ila_0 ila_data (
	.clk(sys_clk), // input wire clk
	.probe0(sys_rst_raw), // input wire [63:0]  probe0  
	.probe1(uart_txd), // input wire [0:0]  probe1 
	.probe2(uart_rxd), // input wire [63:0]  probe2 
	.probe3(ad9144_tx_data_ch0)
	
);
   
endmodule