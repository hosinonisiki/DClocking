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
    inout   		lmk048_mosi		,
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

    // Front-panel interface (active-low through NVT2010PW)
    input   [1:0]   panel_btn_n,
    output  [9:0]   panel_led,

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
    wire sys_mmcm_sel_cmd_0;
    wire sys_mmcm_sel_cmd;
    wire sys_mmcm_sel;
    wire sys_rst_raw;
    wire sys_rst_bar;
    wire sys_mmcm_rst;

    wire panel_btn0_raw_n;
    wire panel_btn1_raw_n;
    wire btn0_n;
    wire btn1_n;
    wire core_clk_in_buf;
    wire core_clk;

    // core_clk is 250 MHz. Ownership changes once, 20 s after MMCM lock.
    localparam [32:0] SPI_HANDOFF_DELAY_CYCLES = 33'd5000000000;
    reg [32:0] spi_handoff_cnt = 33'd0;
    reg        spi_owner = 1'b0;
    wire       top_rst;
    wire       spi_mosi;
    wire       spi_miso;
    wire       spi_sclk;
    wire [0:15] spi_ss;
    wire       spi_io_tri;
    wire [0:3] spi_query_result;
    wire       soft_lmk048_clk;
    wire       soft_lmk048_cs;
    wire       soft_lmk048_mosi;
    wire       soft_ads54j60_sclk;
    wire       soft_ads54j60_sdio;
    wire       soft_ads54j60_cs;
    wire       soft_ads54j69_sclk;
    wire       soft_ads54j69_sdio;
    wire       soft_ads54j69_cs;
    wire       soft_ad9144_sclk;
    wire       soft_ad9144_mosi;
    wire       soft_ad9144_cs;
    
////clk
//wire gty_128_clk;
// IBUFDS_GTEY #(
//    .REFCLK_HROW_CK_SEL(2'b00),        // HROWʱ��ѡ��ͨ����Ϊ00
//    .CLKCM_CFG("TRUE"),                 // ʱ��У������
//    .CLKRCV_TRST("TRUE"),               // ����������
//    .CLKRCV_DLY_B(1'b0),                // �����ӳ�
//    .REFCLK_SRC("REF_PLL"),             // �ο�ʱ��Դѡ��
//    .SIM_DEVICE("ULTRASCALE_PLUS")      // �����ã�����ʵ��оƬ�޸�
//) gty_ibufds_inst (
//    .O          (gty_128_clk),    // ����ʱ�����
//    .ODIV2      (),                     // ����Ƶ���������Ҫ�����գ�
//    .I          (gty128_clk_p),         // �������P
//    .IB         (gty128_clk_n)          // �������N
//);

//wire global_clk;
//BUFG_GT bufg_gt_inst (
//    .O          (global_clk),           // ȫ��ʱ�����
//    .CE         (1'b1),                 // ʱ��ʹ�ܣ�����Ч��
//    .CEMASK     (1'b0),                 // CE����
//    .CLR        (1'b0),                 // �첽����
//    .CLRMASK    (1'b0),                 // CLR����
//    .DIV        (3'b000),               // ��Ƶϵ����000=����Ƶ��001=2��Ƶ...
//    .I          (gty_128_clk)     // ʱ������
//);

//IBUFDS #(
//    .DIFF_TERM("FALSE"),        // HR Bank ��֧�֣�������Ϊ FALSE
//    .IBUF_LOW_PWR("TRUE"),
//    .IOSTANDARD("DIFF_SSTL18_I") // �Ļز��� _DCI �ı�׼
//)core_clk_ibufds (
//    .O  (core_clk_in_buf),        // ת����ĵ���ʱ��
//    .I  (coreclk_p),             // ������ˣ�P��
//    .IB (coreclk_n)              // ��ָ��ˣ�N��
//);
IBUFDS core_clk_ibufds (
    .O  (core_clk_in_buf),        // ת����ĵ���ʱ��
    .I  (coreclk_p),             // ������ˣ�P��
    .IB (coreclk_n)              // ��ָ��ˣ�N��
);
 BUFG core_clk_in_bufg (
    .I (core_clk_in_buf),
    .O (core_clk)
); 

always @(posedge core_clk) begin
    if (!spi_owner) begin
        if (!sys_clk_locked)
            spi_handoff_cnt <= 33'd0;
        else if (spi_handoff_cnt == SPI_HANDOFF_DELAY_CYCLES - 1'b1)
            spi_owner <= 1'b1;
        else
            spi_handoff_cnt <= spi_handoff_cnt + 1'b1;
    end
end

assign top_rst = sys_rst | ~spi_owner;
//wire core_clk_200M;
//  clk_wiz_0 inst_core_clk
//  (
//  // Clock out ports  
//  .clk_out1(core_clk),
//  .clk_out2(core_clk_200M),
//  // Status and control signals               
//  .reset(sys_rst), 
//  .locked(),
// // Clock in ports
//  .clk_in1_p(coreclk_p),
//  .clk_in1_n(coreclk_n)
//  );    

         
    board_ku060_adda_top  u_adda_top( 
        .rst    (sys_rst), 
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
        .sysclk (sys_clk_in),
//        .sysclk_n(sysclk_n),
//        .sysclk_p(sysclk_p),
        .sysrefclk_n(sysrefclk_n),
        .sysrefclk_p(sysrefclk_p),        
//        .coreclk_n(coreclk_n),
//        .coreclk_p(coreclk_p),
        .coreclk(sys_clk),
   // LMK048 ad9144_cs
        .lmk048_clk        (soft_lmk048_clk),
        .lmk048_cs         (soft_lmk048_cs),
        .lmk048_mosi       (soft_lmk048_mosi),
        .lmk048_sync       (lmk048_sync),
        .lmk048_ld1        (lmk048_ld1),
        .lmk048_ld2        (lmk048_ld2),

        // ADC ADS54J60 SPI �ӿ�
        .ads54j60_sclk     (soft_ads54j60_sclk),
        .ads54j60_sdio     (soft_ads54j60_sdio),
        .ads54j60_cs       (soft_ads54j60_cs),
        .ads54j60_sdin     (ads54j60_sdin),
        .ads54j60_syncse   (ads54j60_syncse),
        .ads54j60_reset    (ads54j60_reset),

        // ADC ADS54J69 SPI �ӿ�
        .ads54j69_sclk     (soft_ads54j69_sclk),
        .ads54j69_sdio     (soft_ads54j69_sdio),
        .ads54j69_cs       (soft_ads54j69_cs),
        .ads54j69_sdin     (ads54j69_sdin),
        .ads54j69_syncse   (ads54j69_syncse),
        .ads54j69_reset    (ads54j69_reset),

        // DAC AD9144 SPI �ӿ�
        .ad9144_sclk       (soft_ad9144_sclk),
        .ad9144_miso       (ad9144_miso),
        .ad9144_mosi       (soft_ad9144_mosi),
        .ad9144_irq        (ad9144_irq),
        .ad9144_cs         (soft_ad9144_cs),
        .ad9144_tx_en0     (ad9144_tx_en0),
        .ad9144_tx_en1     (ad9144_tx_en1),

        // ͬ������
        .da_sync_out0_p    (da_sync_out0_p),
        .da_sync_out0_n    (da_sync_out0_n),
        .da_sync_out1_p    (da_sync_out1_p),
        .da_sync_out1_n    (da_sync_out1_n),

        // ��Ƶʹ��
        .rf_out_en         (rf_out_en),

        // �û�LED
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
        .ad9144_tx_valid (1'b1)                                                       
      
);

// Board-level SPI ownership mux. Soft-core channels are 0/6/7/10.
assign lmk048_clk  = spi_owner ? spi_sclk  : soft_lmk048_clk;
assign lmk048_cs   = spi_owner ? spi_ss[0] : soft_lmk048_cs;
assign lmk048_mosi = spi_owner
                   ? (spi_io_tri ? 1'bz : spi_mosi)
                   : soft_lmk048_mosi;

assign ads54j60_sclk = spi_owner ? spi_sclk  : soft_ads54j60_sclk;
assign ads54j60_sdio = spi_owner ? spi_mosi  : soft_ads54j60_sdio;
assign ads54j60_cs   = spi_owner ? spi_ss[6] : soft_ads54j60_cs;

assign ads54j69_sclk = spi_owner ? spi_sclk  : soft_ads54j69_sclk;
assign ads54j69_sdio = spi_owner ? spi_mosi  : soft_ads54j69_sdio;
assign ads54j69_cs   = spi_owner ? spi_ss[7] : soft_ads54j69_cs;

assign ad9144_sclk = spi_owner ? spi_sclk   : soft_ad9144_sclk;
assign ad9144_mosi = spi_owner ? spi_mosi   : soft_ad9144_mosi;
assign ad9144_cs   = spi_owner ? spi_ss[10] : soft_ad9144_cs;

assign spi_miso = !spi_ss[0]  ? lmk048_mosi   :
                  !spi_ss[6]  ? ads54j60_sdin :
                  !spi_ss[7]  ? ads54j69_sdin :
                  !spi_ss[10] ? ad9144_miso   : 1'b0;
wire [63:0] adc_in;
wire [15:0] dac_out[0:3];
assign adc_in = {ads54j60_adc_data_ch1,ads54j60_adc_data_ch0,ads54j69_adc_data_ch1,ads54j69_adc_data_ch0};
assign ad9144_tx_data_ch0 = dac_out[0]; 
assign ad9144_tx_data_ch1 = dac_out[1]; 
assign ad9144_tx_data_ch2 = dac_out[2];      
assign ad9144_tx_data_ch3 = dac_out[3]; 
    
 top #(
    .ADC_channel_count(4),    // ADC ͨ���������޸�
    .DAC_channel_count(4)    // DAC ͨ���������޸�
) u_top (
        .clk    (sys_clk),           // ����ʱ��
        .rst    (top_rst),           // Hold main logic until SPI handoff
        .txd    (uart_txd),           // ���ڷ���
        .rxd    (uart_rxd),           // ���ڽ���
        .err    (err),           // ����ָʾ

        .mosi   (spi_mosi),          // SPI ��������
        .miso   (spi_miso),          // SPI ����ӳ�
        .sclk   (spi_sclk),          // SPI ʱ��
        .ss     (spi_ss),            // 16 λ���豸ѡ�� (ss[0]..ss[15])
        .io_tri (spi_io_tri),        // ��̬����
        .query_result(spi_query_result),

        .adc_in (adc_in),        // ADC ���룬λ�� = ADC_channel_count
        .dac_out({dac_out[3],dac_out[2],dac_out[1],dac_out[0]})        // DAC �����λ�� = DAC_channel_count
);

assign user_led[0] = ~sys_mmcm_sel; 
assign user_led[1] = ~(uart_rxd & uart_txd); 
assign user_led[2] = err;
assign user_led[3] = ~(&spi_ss);              // ����Ƿ����κ�SPIƬѡ��ѡ��
assign user_led[4] = sys_rst;

// One active-low LED is selected at a time. LED0 is the reset state.
assign panel_led[0] = 1'b1;
assign panel_led[1] = sys_clk_locked;
assign panel_led[2] = spi_owner;
assign panel_led[3] = ~sys_mmcm_sel;
assign panel_led[4] = spi_query_result[0]; // LMK PLL1 digital lock status
assign panel_led[5] = ~(uart_rxd & uart_txd); 
assign panel_led[6] = ~(&spi_ss);
assign panel_led[7] = 1'b0; // Reserved
assign panel_led[8] = err;
assign panel_led[9] = sys_rst;



//clk
//IBUFDS  #(
//    .DIFF_TERM("FALSE"),       // Differential Termination
//    .IBUF_LOW_PWR("TRUE"),     // Low power="TRUE", Highest performance="FALSE" 
//    .IOSTANDARD("LVDS")     // Specify the input I/O standard
//) sys_clk_ibufds (
//    .O  (sys_clk_in_buf),        // ת����ĵ���ʱ��
//    .I  (sysclk_p),             // ������ˣ�P��
//    .IB (sysclk_n)              // ��ָ��ˣ�N��
//);
IBUFDS sys_clk_ibufds (
    .O  (sys_clk_in_buf),        // ת����ĵ���ʱ��
    .I  (sysclk_p),             // ������ˣ�P��
    .IB (sysclk_n)              // ��ָ��ˣ�N��
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
        .clk_in1 ( core_clk), // Use 250MHz LMK clk source for jesd204 synchronization
        .clk_in2 ( ), // Fill in when 250MHz OSC is back alive
        .clk_in_sel ( sys_mmcm_sel )//'1' for sys_clk, '0' for ref_clk
    );   
//  sys_clk_mmcm1  sys_clk_mmcm1_inst   (
//        .clk_out1 ( sys_clk_buf),
//        .clk_out2 ( sys_clk_125M_buf), 
//        .clk_out3 ( sys_clk_250M_buf),
//        .clk_out4 ( sys_clk_500M_buf),
//        .reset (sys_mmcm_rst),
        
//        .locked ( sys_clk_locked),
//        .clk_in1 ( sys_clk_in),
//        .clk_in2 (core_clk),
////        .clk_in2_p ( coreclk_p),
////        .clk_in2_n ( coreclk_n),
//        .clk_in_sel ( sys_mmcm_sel )//'1' for sys_clk, '0' for ref_clk
//    );
    
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
// ���� debouncer����������ģ�飩
debouncer #(
    .debounce_time (10),       // 10ms ����ʱ��
    .default_output(1'b1)      // Ĭ������ߵ�ƽ���������ոߣ�
) sys_mmcm_sel_cmd_debouncer (
    .clk   (sys_clk_in),
    .rst   (1'b0),             // ʱ���л��ڼ䲻��λ������
    .keyin (sys_mmcm_sel_cmd_buf),
    .keyout(sys_mmcm_sel_cmd_0)
);
assign sys_mmcm_sel_cmd = sys_mmcm_sel_cmd_0 & btn0_n;

// ���� sys_mmcm_sel_ctrl��MMCM ѡ���������
sys_mmcm_sel_ctrl sys_mmcm_sel_ctrl_inst (
    .clk              (sys_clk_in),        // ��ʹ������ MMCM ��ʱ��
    .rst              (1'b0),              // ʱ���л��ڼ䲻��λ������
    .sys_mmcm_sel_cmd (sys_mmcm_sel_cmd),
    .sys_mmcm_sel     (sys_mmcm_sel),
    .sys_mmcm_rst     (sys_mmcm_rst)
);    
   IBUF  sys_rst_ibuf(
       .O ( sys_rst_raw),      
       .I ( rst)               
   );                         
                       
  
// ���� debouncer����λ����ģ�飩
debouncer #(
    .debounce_time (10),        // 10ms ����ʱ��
    .default_output(1'b0)       // Ĭ������͵�ƽ
) sys_rst_debouncer (
    .clk   (sys_clk),
    .rst   (!sys_clk_locked),   // �ϵ�ʱ��λϵͳ��ȡ��ʱ�������źţ�
    .keyin (sys_rst_raw),       // ע�⣺���˿���Ϊ "input"���� Verilog ���ǹؼ��֣�������Ҫת����޸�ģ��˿���
    .keyout(sys_rst_bar)
);

// Front-panel buttons use the same IBUF -> debouncer path as sys_rst.
IBUF panel_btn0_ibuf (
    .O (panel_btn0_raw_n),
    .I (panel_btn_n[0])
);

IBUF panel_btn1_ibuf (
    .O (panel_btn1_raw_n),
    .I (panel_btn_n[1])
);

debouncer #(
    .debounce_time  (10),
    .default_output(1'b1)
) panel_btn0_debouncer (
    .clk   (sys_clk_in),
    .rst   (1'b0),
    .keyin (panel_btn0_raw_n),
    .keyout(btn0_n)
);

debouncer #(
    .debounce_time  (10),
    .default_output(1'b1)
) panel_btn1_debouncer (
    .clk   (sys_clk),
    .rst   (!sys_clk_locked),
    .keyin (panel_btn1_raw_n),
    .keyout(btn1_n)
);
    
 assign  sys_rst = (~sys_rst_bar) | (~btn1_n);
 ila_0 ila_data (
	.clk(sys_clk), // input wire clk
	.probe0(sys_rst_raw), // input wire [63:0]  probe0  
	.probe1(uart_txd), // input wire [0:0]  probe1 
	.probe2(uart_rxd), // input wire [63:0]  probe2 
	.probe3(ad9144_tx_data_ch0)
	
);
   
endmodule
