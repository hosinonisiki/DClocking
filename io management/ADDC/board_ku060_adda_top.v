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

//vio_dac_data vio_dac_data (
//  .clk(ad9144_core_clk_o),                // input wire clk
//  .probe_out0(ad9144_tx_data_tdata_ch0),  // output wire [63 : 0] probe_out0
//  .probe_out1(ad9144_tx_data_tdata_ch1),  // output wire [63 : 0] probe_out1
//  .probe_out2(ad9144_tx_data_tdata_ch2),  // output wire [63 : 0] probe_out2
//  .probe_out3(ad9144_tx_data_tdata_ch3)  // output wire [63 : 0] probe_out3
//);
assign ad9144_tx_data_tdata_ch0 = ad9144_tx_data_tdata[63:0];
assign ad9144_tx_data_tdata_ch1 = ad9144_tx_data_tdata[127:64];
assign ad9144_tx_data_tdata_ch2 = ad9144_tx_data_tdata[191:128];
assign ad9144_tx_data_tdata_ch3 = ad9144_tx_data_tdata[255:192];
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
        .ads54j60_sync_0(ads54j60_syncse),
        .ads54j60_sync_1( ),
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
        .ads54j69_sync_0(ads54j69_syncse),
        .ads54j69_sync_1( ),
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

assign ads54j69_reset = gpio_o[3];
assign ads54j69_sclk = sclk[7];
assign ads54j69_sdio = sdio_o[7];
assign ads54j69_cs = csb[7];
assign sdio_i[7] = ads54j69_sdin; 
assign ads54j69_core_reset = gpio_o[4]; 
  
assign ad9144_sclk = sclk[10];
assign ad9144_mosi = sdio_o[10];
assign ad9144_cs = csb[10];
assign sdio_i[10] = ad9144_miso; 


//wire    dac_tx_en ;
//wire    rf_tx_en ;
//vio_dac_txen vio_dac_txen (
//  .clk(ad9144_core_clk_o),                // input wire clk
//  .probe_out0(dac_tx_en),  // output wire [0 : 0] probe_out0
//  .probe_out1(rf_tx_en)  // output wire [0 : 0] probe_out1
//);
//assign ad9144_tx_en0 = dac_tx_en;
//assign ad9144_tx_en1 = dac_tx_en;
//assign rf_out_en = {rf_tx_en,rf_tx_en,rf_tx_en,rf_tx_en};
assign ad9144_tx_en0 = ad9144_tx_valid;
assign ad9144_tx_en1 = ad9144_tx_valid;
assign rf_out_en = {ad9144_tx_valid,ad9144_tx_valid,ad9144_tx_valid,ad9144_tx_valid};

assign ad9144_core_reset = gpio_o[5];
////j69     
//wire [63:0]   ads54j69_data_ch0;
//wire [63:0]   ads54j69_data_lsb_ch0;
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
  .wr_clk       (   j69_core_clk_o                       ), // input wire wr_clk//125M
  .rd_clk       (   coreclk                   ), // input wire rd_clk
  .din          (   ads54j69_data_msb_ch0        ), // input wire [63 : 0] din
  .wr_en        (   ads54j69_syncse                    ), // input wire wr_en
  .rd_en        (   !ads54j69_fifo_empty         ), // input wire rd_en
  .dout         (   ads54j69_fifo_data_ch0       ), // output wire [15 : 0] dout
  .full         (            				   ), // output wire full
  .empty        (   ads54j69_fifo_empty          ), // output wire empty
  .valid        (   ads54j69_fifo_valid          )  // output wire valid
);

fifo_64in32out fifo_64in32out_ch1 (
  .wr_clk       (   j69_core_clk_o                       ), // input wire wr_clk
  .rd_clk       (   coreclk                   ), // input wire rd_clk
  .din          (   ads54j69_data_msb_ch1		   ), // input wire [63 : 0] din
  .wr_en        (   ads54j69_syncse                    ), // input wire wr_en
  .rd_en        (   !ads54j69_fifo_empty         ), // input wire rd_en
  .dout         (   ads54j69_fifo_data_ch1       ), // output wire [15 : 0] dout
  .full         (            				   ), // output wire full
  .empty        (                              ), // output wire empty
  .valid        (           			       )  // output wire valid
);

assign ads54j69_adc_data_ch0    =  ads54j69_fifo_data_ch0[15:0]  ;  //div 2
assign ads54j69_adc_data_ch1    =  ads54j69_fifo_data_ch1 [15:0] ;
assign ads54j69_adc_valid       =  ads54j69_fifo_valid       ;

////j60
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
  .wr_clk       (   j60_core_clk_o               ), // input wire wr_clk//125M
  .rd_clk       (   coreclk                 ), // input wire rd_clk
  .din          (   ads54j60_data_msb_ch0        ), // input wire [63 : 0] din
  .wr_en        (   ads54j60_syncse              ), // input wire wr_en
  .rd_en        (   !ads54j60_fifo_empty         ), // input wire rd_en
  .dout         (   ads54j60_fifo_data_ch0       ), // output wire [15 : 0] dout
  .full         (            				     ), // output wire full
  .empty        (   ads54j60_fifo_empty          ), // output wire empty
  .valid        (   ads54j60_fifo_valid          )  // output wire valid
);

fifo_128in64out fifo_128in64out_ch1 (
  .wr_clk       (   j60_core_clk_o                       ), // input wire wr_clk
  .rd_clk       (   coreclk                   ), // input wire rd_clk
  .din          (   ads54j60_data_msb_ch1		   ), // input wire [63 : 0] din
  .wr_en        (   ads54j60_syncse                    ), // input wire wr_en
  .rd_en        (   !ads54j60_fifo_empty         ), // input wire rd_en
  .dout         (   ads54j60_fifo_data_ch1       ), // output wire [15 : 0] dout
  .full         (            				   ), // output wire full
  .empty        (                              ), // output wire empty
  .valid        (           			       )  // output wire valid
);

assign ads54j60_adc_data_ch0    =  ads54j60_fifo_data_ch0[15:0]    ;
assign ads54j60_adc_data_ch1    =  ads54j60_fifo_data_ch1[15:0]    ;
assign ads54j60_adc_valid       =  ads54j60_fifo_valid       ;


 ///ad9144  
  dac_axi256_tx  dac_axis_tx256_inst(
        .clk (ad9144_core_clk_o),
        .rst(ad9144_core_reset),
        .tx_tdata_out (ad9144_tx_data_tdata),
        .tx_tready_in(ad9144_tx_valid),
        .data_a_in (ad9144_tx_data_ch0),
        .data_b_in (ad9144_tx_data_ch1),
        .data_c_in (ad9144_tx_data_ch2),
        .data_d_in (ad9144_tx_data_ch3)       
    );
//assign gpio2_i[31:0] = mod_if_freq_H;
//assign gpio3_i[31:0] = mod_if_freq_L;
//ila_0 ila_data (
//	.clk(j60_core_clk_o), // input wire clk


//	.probe0(ads54j60_data_ch0_tdata), // input wire [63:0]  probe0  
//	.probe1(ads54j60_data_ch0_tvalid), // input wire [0:0]  probe1 
//	.probe2(ads54j69_data_ch0_tdata), // input wire [63:0]  probe2 
//	.probe3(ads54j69_data_ch0_tvalid), // input wire [0:0]  probe3 
//	.probe4(ads54j60_syncse), // input wire [0:0]  probe4 
//	.probe5(ads54j69_syncse), // input wire [0:0]  probe5 
////	.probe6(ad9144_tx_sync_0), // input wire [0:0]  probe6
////	.probe7(ad9144_tx_data_tready), // input wire [0:0]  probe6
//	.probe6(ads54j60_data_ch0)
	
//);
 ila_1 ila1_data (
	.clk(coreclk), // input wire clk


	.probe0(ad9144_tx_sync_0), // input wire [63:0]  probe0  
	.probe1(ad9144_tx_data_tready), // input wire [0:0]  probe1 
	.probe2(ads54j60_adc_data_ch0), // input wire [63:0]  probe2 
	.probe3(ads54j69_adc_data_ch0)
	
); 
  
wire  glblclk_i       ;
wire [63:0]   vio_ftw ;
//vio_ftw vio_ftw (
//  .clk(ad9144_core_clk_o),                // input wire clk
//  .probe_out0(vio_ftw)  // output wire [63 : 0] probe_out0
//);

wire    [16*4-1:0]  	 tx_tdata_RF   	   ;

//Mod_TOP mod_source   (
//	.dac_clk         		(	ad9144_core_clk_o	           ),
//	.carrier_fcw		    (	vio_ftw                        ),
//	.source_doutRF			(	tx_tdata_RF                    )

//	 );
//assign ad9144_tx_data_tdata_ch0 = {
//	       tx_tdata_RF[ 4 *16-9 : 4 *16-16],
//	       tx_tdata_RF[ 4 *16-1 : 4 *16-8 ],
	      
//	       tx_tdata_RF[ 3 *16-9 : 3 *16-16],
//	       tx_tdata_RF[ 3 *16-1 : 3 *16-8 ],
	      
//	       tx_tdata_RF[ 2 *16-9 : 2 *16-16],
//	       tx_tdata_RF[ 2 *16-1 : 2 *16-8 ],
	      
//	       tx_tdata_RF[ 1 *16-9 : 1 *16-16],
//	       tx_tdata_RF[ 1 *16-1 : 1 *16-8 ]
//				    } ;   
  
endmodule
