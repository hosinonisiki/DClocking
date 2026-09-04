`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2026/01/27 13:55:47
// Design Name: 
// Module Name: board_ku060_adda_top
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


module board_ku060_adda_top(
    input           rst,
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
     
    input           sysclk        ,
    
    input           sysrefclk_p     ,   //lmk04828_clk1
    input           sysrefclk_n     ,    
//    input           coreclk_p       ,   //lmk04828_clk2
//    input           coreclk_n       ,
    input           coreclk       ,
    
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
    
    output  [3:0]   rf_out_en       ,
    
//    output  [5:0]   user_led ,
    output	[15:0] ads54j69_adc_data_ch0,
    output	[15:0] ads54j69_adc_data_ch1,
    output		   ads54j69_adc_valid,
    //j60
    output	[15:0] ads54j60_adc_data_ch0,
    output	[15:0] ads54j60_adc_data_ch1,
    output		   ads54j60_adc_valid ,
    
    //ad9144 
    input	[15:0]ad9144_tx_data_ch0, //sample 1G   
    input	[15:0]ad9144_tx_data_ch1,
    input	[15:0]ad9144_tx_data_ch2,
    input	[15:0]ad9144_tx_data_ch3,        
    
    input		   ad9144_tx_valid         
    
    );
//    wire	[15:0] ads54j69_adc_data_ch0;
//    wire	[15:0] ads54j69_adc_data_ch1;
//    wire		   ads54j69_adc_valid;
//    //j60
//    wire	[15:0] ads54j60_adc_data_ch0;
//    wire	[15:0] ads54j60_adc_data_ch1;
//    wire		   ads54j60_adc_valid ;
    
//    //ad9144 
//    wire	[15:0]ad9144_tx_data_ch0; //sample 1G   
//    wire	[15:0]ad9144_tx_data_ch1;
//    wire	[15:0]ad9144_tx_data_ch2;
//    wire	[15:0]ad9144_tx_data_ch3;            
//    wire		   ad9144_tx_valid; 
      
//    assign user_led  = 6'b101010 ;
    
//    assign rf_out_en = 4'b0000   ;
    

  wire clk_250M;
  wire ad9144_core_reset;
  wire [255:0]ad9144_tx_data_tdata;
  wire ad9144_tx_data_tready;
  wire ad9144_tx_sync_0;
  wire ad9144_tx_sync_1;

  wire [127:0]ads54j60_data_ch0_tdata;
  wire ads54j60_data_ch0_tvalid;
  wire [127:0]ads54j60_data_ch1_tdata;
  wire ads54j60_data_ch1_tvalid;
  wire ads54j60_core_reset;
  wire ads54j60_sync_0;
  wire ads54j60_sync_1;
  
  wire [63:0]ads54j69_data_ch0_tdata;
  wire ads54j69_data_ch0_tvalid;
  wire [63:0]ads54j69_data_ch1_tdata;
  wire ads54j69_data_ch1_tvalid;
  wire ads54j69_core_reset;
  wire ads54j69_sync_0;
  wire ads54j69_sync_1;


  wire ad9144_core_clk_o;
  wire j60_core_clk_o;
  wire j69_core_clk_o;
  wire [15:0]csb;
  wire [31:0]gpio2_i;
  wire [31:0]gpio2_o;
  wire [31:0]gpio_i;
  wire [31:0]gpio_o;
  wire [15:0]sclk;
  wire [15:0]sdio_i;
  wire [15:0]sdio_o;
  wire [15:0]sdio_oe;

IBUFDS   i_tx_sync_0 (
    .I  (da_sync_out0_p),
    .IB (da_sync_out0_n),
    .O  (ad9144_tx_sync_0)
); 
IBUFDS   i_tx_sync_1 (
    .I  (da_sync_out1_p),
    .IB (da_sync_out1_n),
    .O  (ad9144_tx_sync_1)
); 

wire    [63:0]  ad9144_tx_data_tdata_ch0;
wire    [63:0]  ad9144_tx_data_tdata_ch1;
wire    [63:0]  ad9144_tx_data_tdata_ch2;
wire    [63:0]  ad9144_tx_data_tdata_ch3;

  adda_top adda_top_i
       (.ad9144_core_clk_o(ad9144_core_clk_o),
        .ad9144_refclk_0_clk_n(gty127_clk_n),
        .ad9144_refclk_0_clk_p(gty127_clk_p),
        .ad9144_core_reset(ad9144_core_reset),
        .ad9144_tx_data_0_tdata(ad9144_tx_data_tdata_ch0),
        .ad9144_tx_data_1_tdata(ad9144_tx_data_tdata_ch1),
        .ad9144_tx_data_2_tdata(ad9144_tx_data_tdata_ch2),
        .ad9144_tx_data_3_tdata(ad9144_tx_data_tdata_ch3),
        .ad9144_tx_data_0_tready(ad9144_tx_data_tready),
        .ad9144_tx_sync(ad9144_tx_sync_0),
        .ad9144_txn_out(ad9144_da_n),
        .ad9144_txp_out(ad9144_da_p),
        .ads54j60_data_ch0_tdata(ads54j60_data_ch0_tdata),
        .ads54j60_data_ch0_tvalid(ads54j60_data_ch0_tvalid),
        .ads54j60_data_ch1_tdata(ads54j60_data_ch1_tdata),
        .ads54j60_data_ch1_tvalid(ads54j60_data_ch1_tvalid),
        .ads54j60_refclk_0_clk_n(gty224_clk_n),
        .ads54j60_refclk_0_clk_p(gty224_clk_p),
        .ads54j60_refclk_1_clk_n(gty225_clk_n),
        .ads54j60_refclk_1_clk_p(gty225_clk_p),
        .ads54j60_core_reset(ads54j60_core_reset),
        .ads54j60_rxn_in_0(ads54j60_A_n),
        .ads54j60_rxp_in_0(ads54j60_A_p),
        .ads54j60_rxn_in_1(ads54j60_B_n),
        .ads54j60_rxp_in_1(ads54j60_B_p),
        .ads54j60_sync_0(ads54j60_sync_0),
        .ads54j60_sync_1(ads54j60_sync_1),
        .ads54j69_data_ch0_tdata(ads54j69_data_ch0_tdata),
        .ads54j69_data_ch0_tvalid(ads54j69_data_ch0_tvalid),
        .ads54j69_data_ch1_tdata(ads54j69_data_ch1_tdata),
        .ads54j69_data_ch1_tvalid(ads54j69_data_ch1_tvalid),
        .ads54j69_refclk_0_clk_n(gty226_clk_n),
        .ads54j69_refclk_0_clk_p(gty226_clk_p),
        .ads54j69_refclk_1_clk_n(gty227_clk_n),
        .ads54j69_refclk_1_clk_p(gty227_clk_p),
        .ads54j69_core_reset(ads54j69_core_reset),
        .ads54j69_rxn_in_0(ads54j69_A_n),
        .ads54j69_rxp_in_0(ads54j69_A_p),        
        .ads54j69_rxn_in_1(ads54j69_B_n),
        .ads54j69_rxp_in_1(ads54j69_B_p),
        .ads54j69_sync_0(ads54j69_sync_0),
        .ads54j69_sync_1(ads54j69_sync_1),
        .clk_250M(clk_250M),
        .board_sysclk(sysclk),
//        .board_sysclk_clk_p(sysclk_p),
//        .core_clk_clk_n(coreclk_n),
//        .core_clk_clk_p(coreclk_p),
        .core_clk(coreclk),
        .j60_core_clk_o(j60_core_clk_o),
        .j69_core_clk_o(j69_core_clk_o),
        .gpio2_i(gpio2_i),
        .gpio2_o(gpio2_o),
        .gpio_i(gpio_i),
        .gpio_o(gpio_o),
        .csb(csb),
        .sclk(sclk),
        .sdio_i(sdio_i),
        .sdio_o(sdio_o),
        .sdio_oe(sdio_oe),
        .sysref_clk_clk_n(sysrefclk_n),
        .sysref_clk_clk_p(sysrefclk_p));
  
assign lmk048_clk = sclk[0];
assign lmk048_cs = csb[0];
assign lmk048_mosi = (sdio_oe[0])?sdio_o[0]:'bz;
assign sdio_i[0] = lmk048_ld1;
assign lmk048_sync = gpio_o[0];
assign gpio_i[1:0] = { lmk048_ld2,lmk048_ld1};
  
assign ads54j60_reset = gpio_o[1];
assign ads54j60_sclk = sclk[6];
assign ads54j60_sdio = sdio_o[6];
assign ads54j60_cs = csb[6];
assign sdio_i[6] = ads54j60_sdin; 
assign ads54j60_core_reset = gpio_o[2];
assign ads54j60_syncse = ads54j60_sync_0 && ads54j60_sync_1 ;

assign ads54j69_reset = gpio_o[3];
assign ads54j69_sclk = sclk[7];
assign ads54j69_sdio = sdio_o[7];
assign ads54j69_cs = csb[7];
assign sdio_i[7] = ads54j69_sdin; 
assign ads54j69_core_reset = gpio_o[4]; 
assign ads54j69_syncse = ads54j69_sync_0 && ads54j69_sync_1 ;
  
assign ad9144_sclk = sclk[10];
assign ad9144_mosi = sdio_o[10];
assign ad9144_cs = csb[10];
assign sdio_i[10] = ad9144_miso; 
assign ad9144_core_reset = gpio_o[5];
assign ad9144_tx_en0 = gpio_o[6];
assign ad9144_tx_en1 = gpio_o[6];
assign rf_out_en = 4'b0000   ;

  
  ///////////////////////////////////////////////////
  ///// ads54j69 data  
  //////////////////////////////////////////////////
wire [63:0]   ads54j69_data_msb_ch0;
wire [63:0]   ads54j69_data_msb_ch1;
  
transport transports0(
	.datain  			( ads54j69_data_ch0_tdata     	),
	.dataout 			(      	),
	.dataout_lsb 		(    ),
	.dataout_msb 		( ads54j69_data_msb_ch0   )
);

transport transports1(
	.datain  			( ads54j69_data_ch1_tdata     ),
	.dataout 			(       ),
	.dataout_lsb 		(    ),
	.dataout_msb 		(  ads54j69_data_msb_ch1  )
);

wire	[31:0] ads54j69_fifo_data_ch0     ;
wire	[31:0] ads54j69_fifo_data_ch1     ;
wire		   ads54j69_fifo_valid        ;
wire		   ads54j69_fifo_empty        ;

fifo_64in32out fifo_64in32out_ch0 (
  .rst          (   rst                  ),
  .wr_clk       (   j69_core_clk_o                       ), // input wire wr_clk//125M
  .rd_clk       (   coreclk                   ), // input wire rd_clk
  .din          (   ads54j69_data_msb_ch0        ), // input wire [63 : 0] din
  .wr_en        (   ads54j69_syncse                    ), // input wire wr_en
  .rd_en        (   !ads54j69_fifo_empty         ), // input wire rd_en
  .dout         (   ads54j69_fifo_data_ch0       ), // output wire [15 : 0] dout
  .full         (            				   ), // output wire full
  .empty        (   ads54j69_fifo_empty          )
);

fifo_64in32out fifo_64in32out_ch1 (
  .rst          (   rst                  ),
  .wr_clk       (   j69_core_clk_o                       ), // input wire wr_clk
  .rd_clk       (   coreclk                   ), // input wire rd_clk
  .din          (   ads54j69_data_msb_ch1		   ), // input wire [63 : 0] din
  .wr_en        (   ads54j69_syncse                    ), // input wire wr_en
  .rd_en        (   !ads54j69_fifo_empty         ), // input wire rd_en
  .dout         (   ads54j69_fifo_data_ch1       ), // output wire [15 : 0] dout
  .full         (            				   ), // output wire full
  .empty        (                              )
);

assign ads54j69_adc_data_ch0    =  ads54j69_fifo_data_ch0[15:0]  ;  //div 2
assign ads54j69_adc_data_ch1    =  ads54j69_fifo_data_ch1 [15:0] ;
assign ads54j69_adc_valid       =  ads54j69_fifo_valid       ;

 ///////////////////////////////////////////////////
  ///// ads54j60 data  
  //////////////////////////////////////////////////
wire [127:0]   ads54j60_data_msb_ch0;
wire [127:0]   ads54j60_data_lsb_ch0;
wire [127:0]   ads54j60_data_ch0;
wire [127:0]   ads54j60_data_msb_ch1;
  
transport128 transports1280(
	.datain  			( ads54j60_data_ch0_tdata     	),
	.dataout 			( ads54j60_data_ch0     	),
	.dataout_lsb 		(  ads54j60_data_lsb_ch0  ),
	.dataout_msb 		( ads54j60_data_msb_ch0   )
);

transport128 transports1281(
	.datain  			( ads54j60_data_ch1_tdata     ),
	.dataout 			(        ),
	.dataout_lsb 		(    ),
	.dataout_msb 		( ads54j60_data_msb_ch1   )
);

wire	[63:0] ads54j60_fifo_data_ch0     ;
wire	[63:0] ads54j60_fifo_data_ch1     ;
wire		   ads54j60_fifo_valid        ;
wire		   ads54j60_fifo_empty        ;

fifo_128in64out fifo_128in64out_ch0 (
  .rst          (   rst                  ),
  .wr_clk       (   j60_core_clk_o               ), // input wire wr_clk//125M
  .rd_clk       (   coreclk                 ), // input wire rd_clk
  .din          (   ads54j60_data_msb_ch0        ), // input wire [63 : 0] din
  .wr_en        (   ads54j60_syncse              ), // input wire wr_en
  .rd_en        (   !ads54j60_fifo_empty         ), // input wire rd_en
  .dout         (   ads54j60_fifo_data_ch0       ), // output wire [15 : 0] dout
  .full         (            				     ), // output wire full
  .empty        (   ads54j60_fifo_empty          )
);

fifo_128in64out fifo_128in64out_ch1 (
  .rst          (   rst                  ),
  .wr_clk       (   j60_core_clk_o                       ), // input wire wr_clk
  .rd_clk       (   coreclk                   ), // input wire rd_clk
  .din          (   ads54j60_data_msb_ch1		   ), // input wire [63 : 0] din
  .wr_en        (   ads54j60_syncse                    ), // input wire wr_en
  .rd_en        (   !ads54j60_fifo_empty         ), // input wire rd_en
  .dout         (   ads54j60_fifo_data_ch1       ), // output wire [15 : 0] dout
  .full         (            				   ), // output wire full
  .empty        (                              )
);

assign ads54j60_adc_data_ch0    =  ads54j60_fifo_data_ch0[15:0]    ;
assign ads54j60_adc_data_ch1    =  ads54j60_fifo_data_ch1[15:0]    ;
assign ads54j60_adc_valid       =  ads54j60_fifo_valid       ;

 ///////////////////////////////////////////////////
  ///// ad9144 data  
  //////////////////////////////////////////////////
  wire    [63:0]  	 tx_tdata_RF   	   ;   
  wire    [63:0]  	 tx_tdata_RF1   	   ; 
  wire    [63:0]  	 tx_tdata_RF2   	   ; 
  wire    [63:0]  	 tx_tdata_RF3   	   ; 
dac_fifo_16in64out dac_fifo_16in64out_ch0 (
  .rst          (   rst                  ),
  .wr_clk       (   coreclk                       ), // input wire wr_clk
  .rd_clk       (   ad9144_core_clk_o                   ), // input wire rd_clk
  .din          (   ad9144_tx_data_ch0		   ), // input wire [15 : 0] din
  .wr_en        (   ad9144_tx_valid                    ), // input wire wr_en
  .rd_en        (   !ad9144_fifo_empty         ), // input wire rd_en
  .dout         (   tx_tdata_RF       ), // output wire [63 : 0] dout
  .full         (            				   ), // output wire full
  .empty        (   ad9144_fifo_empty           )
);


dac_fifo_16in64out dac_fifo_16in64out_ch1 (
  .rst          (   rst                  ),
  .wr_clk       (   coreclk                       ), // input wire wr_clk
  .rd_clk       (   ad9144_core_clk_o                   ), // input wire rd_clk
  .din          (   ad9144_tx_data_ch1		   ), // input wire [15 : 0] din
  .wr_en        (   ad9144_tx_valid                    ), // input wire wr_en
  .rd_en        (   !ad9144_fifo_empty         ), // input wire rd_en
  .dout         (   tx_tdata_RF1       ), // output wire [63: 0] dout
  .full         (            				   ), // output wire full
  .empty        (              )
);

dac_fifo_16in64out dac_fifo_16in64out_ch2 (
  .rst          (   rst                  ),
  .wr_clk       (   coreclk                       ), // input wire wr_clk
  .rd_clk       (   ad9144_core_clk_o                   ), // input wire rd_clk
  .din          (   ad9144_tx_data_ch2		   ), // input wire [15 : 0] din
  .wr_en        (   ad9144_tx_valid                    ), // input wire wr_en
  .rd_en        (   !ad9144_fifo_empty         ), // input wire rd_en
  .dout         (   tx_tdata_RF2      ), // output wire [63 : 0] dout
  .full         (            				   ), // output wire full
  .empty        (              )
);

dac_fifo_16in64out dac_fifo_16in64out_ch3 (
  .rst          (   rst                  ),
  .wr_clk       (   coreclk                       ), // input wire wr_clk
  .rd_clk       (   ad9144_core_clk_o                   ), // input wire rd_clk
  .din          (   ad9144_tx_data_ch3		   ), // input wire [15 : 0] din
  .wr_en        (   ad9144_tx_valid                    ), // input wire wr_en
  .rd_en        (   !ad9144_fifo_empty         ), // input wire rd_en
  .dout         (   tx_tdata_RF3       ), // output wire [63 : 0] dout
  .full         (            				   ), // output wire full
  .empty        (              )
);
/////////////////////////////////////test////////////////////
//wire [63:0]   carrier_fcw ;
//wire [9:0]   vio_send_power_atten ;
//vio_ftw vio_ftw_u (
//  .clk(ad9144_core_clk_o),                // input wire clk
//  .probe_out0(carrier_fcw),
//   .probe_out1(vio_send_power_atten)
//);
 
//  wire    [16*4-1:0]  	 tx_tdata_RF   	   ;   
////doppler_gen doppler_gen(
////	.rx_DPL_clk           					  	(	ad9144_core_clk_o ),
////	.rx_DPL_rst           					  	(	0			        ),
////	.rx_carrier_fcw           					(	carrier_fcw			),
////	.rx_DPL_ce            					  	(	1'b1				),
////	.tx_DPL_DoutBus_xb                          (	tx_tdata_RF		)
////);

//Mod_TOP mod_source   (
//	.dac_clk         		(	ad9144_core_clk_o	           ),
//	.carrier_fcw		    (	carrier_fcw                        ),
//	.send_power_atten		(	vio_send_power_atten           ),
//	.source_doutRF			(	tx_tdata_RF                    )

//	 );

assign ad9144_tx_data_tdata_ch0 = {
	      
	       tx_tdata_RF[ 1 *16-9 : 1 *16-16],   //  data0[7:0]
	       tx_tdata_RF[ 2 *16-9 : 2 *16-16],   //  data1[7:0]	      
	       tx_tdata_RF[ 3 *16-9 : 3 *16-16],   //  data2[7:0]
	       tx_tdata_RF[ 4 *16-9 : 4 *16-16],   //  data3[7:0]
	       
	       tx_tdata_RF[ 1 *16-1 : 1 *16-8 ],   //  data0[15:8]
	       tx_tdata_RF[ 2 *16-1 : 2 *16-8 ],   //  data1[15:8]      
	       tx_tdata_RF[ 3 *16-1 : 3 *16-8 ],   //  data2[15:8]
	       tx_tdata_RF[ 4 *16-1 : 4 *16-8 ]    //  data3[15:8]

				    } ;   
assign ad9144_tx_data_tdata_ch1 = {
	      
	       tx_tdata_RF1[ 1 *16-9 : 1 *16-16],   //  data0[7:0]
	       tx_tdata_RF1[ 2 *16-9 : 2 *16-16],   //  data1[7:0]	      
	       tx_tdata_RF1[ 3 *16-9 : 3 *16-16],   //  data2[7:0]
	       tx_tdata_RF1[ 4 *16-9 : 4 *16-16],   //  data3[7:0]
	       
	       tx_tdata_RF1[ 1 *16-1 : 1 *16-8 ],   //  data0[15:8]
	       tx_tdata_RF1[ 2 *16-1 : 2 *16-8 ],   //  data1[15:8]      
	       tx_tdata_RF1[ 3 *16-1 : 3 *16-8 ],   //  data2[15:8]
	       tx_tdata_RF1[ 4 *16-1 : 4 *16-8 ]    //  data3[15:8]

				    } ;   
assign ad9144_tx_data_tdata_ch2 = {
	      
	       tx_tdata_RF2[ 1 *16-9 : 1 *16-16],   //  data0[7:0]
	       tx_tdata_RF2[ 2 *16-9 : 2 *16-16],   //  data1[7:0]	      
	       tx_tdata_RF2[ 3 *16-9 : 3 *16-16],   //  data2[7:0]
	       tx_tdata_RF2[ 4 *16-9 : 4 *16-16],   //  data3[7:0]
	       
	       tx_tdata_RF2[ 1 *16-1 : 1 *16-8 ],   //  data0[15:8]
	       tx_tdata_RF2[ 2 *16-1 : 2 *16-8 ],   //  data1[15:8]      
	       tx_tdata_RF2[ 3 *16-1 : 3 *16-8 ],   //  data2[15:8]
	       tx_tdata_RF2[ 4 *16-1 : 4 *16-8 ]    //  data3[15:8]
				    } ;   
assign ad9144_tx_data_tdata_ch3 = {
	      
	       tx_tdata_RF3[ 1 *16-9 : 1 *16-16],   //  data0[7:0]
	       tx_tdata_RF3[ 2 *16-9 : 2 *16-16],   //  data1[7:0]	      
	       tx_tdata_RF3[ 3 *16-9 : 3 *16-16],   //  data2[7:0]
	       tx_tdata_RF3[ 4 *16-9 : 4 *16-16],   //  data3[7:0]
	       
	       tx_tdata_RF3[ 1 *16-1 : 1 *16-8 ],   //  data0[15:8]
	       tx_tdata_RF3[ 2 *16-1 : 2 *16-8 ],   //  data1[15:8]      
	       tx_tdata_RF3[ 3 *16-1 : 3 *16-8 ],   //  data2[15:8]
	       tx_tdata_RF3[ 4 *16-1 : 4 *16-8 ]    //  data3[15:8]

				    } ;
/////////////////////////////////////////////////////////////////////////////				    
 ila_1 ila1_data (
	.clk(coreclk), // input wire clk


	.probe0(ad9144_tx_sync_0), // input wire [63:0]  probe0  
	.probe1(ad9144_tx_data_tready), // input wire [0:0]  probe1 
	.probe2(ads54j60_adc_data_ch0), // input wire [63:0]  probe2 
	.probe3(ads54j69_adc_data_ch0)
	
); 
  
 
  
endmodule
