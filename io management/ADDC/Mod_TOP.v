`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2026/02/07 10:55:40
// Design Name: 
// Module Name: Mod_TOP
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


module Mod_TOP(
	input					 dac_clk 		       ,
	input					 sim_clk	           ,
	input					 sim2_clk	           ,
	input                    rstn_modu             ,  
	input    [2:0]           modu_type             ,
	input    [31:0]          symbol_rate           ,
	input    [31:0]          info_rate             ,
	input    [63:0]          carrier_fcw           ,
	input    [51:0]          fre_offset_send       ,
	input    [55:0]          symbol_offset_send    ,
	input    [2:0]           shaping_type          ,
	input                    shaping_en            ,
	input    [4:0]           shaping_alpha         ,
	input    [1:0]           diff_sel              ,
	input    [7:0]           iq_power_ratio        ,
	input					 double_single		   ,//'1': double   ;  '0' : single;
	input                    rs_code_sel           ,
	input    [2:0]           rs_inter_depth        ,
	input    [7:0]           rs_code_len           ,
	input                    rs_mother_code        ,
	input                    rs_base               ,
	input    [2:0]           date_type             ,//0 :PN;1:file ;2:fix_date;3:added date;
    input[15:0]	             file_data		       ,
    input 		             file_valid		       ,
    output 		             file_rd		       ,
	input    [7:0]           fix_data_I            ,
	input    [7:0]           fix_data_Q            ,
	input    [3:0]           pn_source_type        ,
	input    [19:0]          frame_noenc_data_len  ,
	input    [19:0]          frame_data_len        ,
	input    [6:0]           frame_asm_len         ,
	input    [63:0]          frame_asm_I           ,
	input    [63:0]          frame_asm_Q           ,
	input                    conv_code_sel         ,
	input                    conv_double_sel       ,
	input    [2:0]           conv_rate_sel         ,
	input                    conv_swap_sel         ,
	input	 [1:0]			 conv_G1G2			   ,//0??G1-G2  ;  1: G1-/G2 ?? 2??G2-G1; 3: G2-/G1  
	input                    ldpc_code_sel         ,
	input    [3:0]           ldpc_ratio            ,
	input                    scram_sel             ,
	input                    scram_prepost         ,
    input	[19:0]	         frm_length            ,
    input   [2:0]            pn_class              ,
    input	[1:0]	         pn_gen_type	       ,
    input	[5:0]	         pn_poly_width         ,
    input	[31:0]	         pn_poly               ,
    input	[31:0]           pn_state_I            ,
    input	[31:0]           pn_state_Q            ,
	input                    tcm_sel      		   ,
	input   [1:0]            tcm_ratio      	   ,
	input    [9:0]           send_power_atten      ,
	input    [7:0]           crc_sel               ,
	input                    crc_en                ,
	input                    carrier_type          ,  //0:only carrier 1: modulated data
	input 				     dpl_on				   ,
	input 				     dpl_type			   ,
	input 	   [31:0]	     dpl_rate			   ,
	input 	   [31:0]	     dpl_range			   ,
	input 	 			     noise_on			   ,
	input 	   [1:0]	     noise_type			   ,
	input 	   [9:0]	     c_n0				   ,
	input                    dout_en               ,  //0 : off ;  1: on 
	input                    spec_en               ,  //0 : off ;  1: on 
	
	//output          
	output    [31:0]         topcie_data           ,
	output                   topcie_valid          ,
	
	output                   source_valid          ,
	output    [16*4-1:0]  	 source_doutRF   	   

    );


parameter	DATA_WIDTH = 16	;

	wire[ 16*4 -1 :0 ] 	data_I_phase0_all	;
	wire[ 16*4 -1 :0 ] 	data_Q_phase0_all	;
    
assign		data_I_phase0_all[  1 * 16 -1 :  0 * 16 ] =   'h4b00  ;
assign		data_I_phase0_all[  2 * 16 -1 :  1 * 16 ] =   'h4b00  ;
assign		data_I_phase0_all[  3 * 16 -1 :  2 * 16 ] =   'h4b00  ;
assign		data_I_phase0_all[  4 * 16 -1 :  3 * 16 ] =   'h4b00  ;
//assign		data_I_phase0_all[  5 * 16 -1 :  4 * 16 ] =   'h4b00  ;
//assign		data_I_phase0_all[  6 * 16 -1 :  5 * 16 ] =   'h4b00  ;
//assign		data_I_phase0_all[  7 * 16 -1 :  6 * 16 ] =   'h4b00  ;
//assign		data_I_phase0_all[  8 * 16 -1 :  7 * 16 ] =   'h4b00  ;
//assign		data_I_phase0_all[  9 * 16 -1 :  8 * 16 ] =   'h4b00  ;
//assign		data_I_phase0_all[ 10 * 16 -1 :  9 * 16 ] =   'h4b00  ;
//assign		data_I_phase0_all[ 11 * 16 -1 : 10 * 16 ] =   'h4b00  ;
//assign		data_I_phase0_all[ 12 * 16 -1 : 11 * 16 ] =   'h4b00  ;
//assign		data_I_phase0_all[ 13 * 16 -1 : 12 * 16 ] =   'h4b00  ;
//assign		data_I_phase0_all[ 14 * 16 -1 : 13 * 16 ] =   'h4b00  ;
//assign		data_I_phase0_all[ 15 * 16 -1 : 14 * 16 ] =   'h4b00  ;
//assign		data_I_phase0_all[ 16 * 16 -1 : 15 * 16 ] =   'h4b00  ;

assign		data_Q_phase0_all[  1 * 16 -1 :  0 * 16 ] =   'hb500  ;
assign		data_Q_phase0_all[  2 * 16 -1 :  1 * 16 ] =   'hb500  ;
assign		data_Q_phase0_all[  3 * 16 -1 :  2 * 16 ] =   'hb500  ;
assign		data_Q_phase0_all[  4 * 16 -1 :  3 * 16 ] =   'hb500  ;
//assign		data_Q_phase0_all[  5 * 16 -1 :  4 * 16 ] =   'hb500  ;
//assign		data_Q_phase0_all[  6 * 16 -1 :  5 * 16 ] =   'hb500  ;
//assign		data_Q_phase0_all[  7 * 16 -1 :  6 * 16 ] =   'hb500  ;
//assign		data_Q_phase0_all[  8 * 16 -1 :  7 * 16 ] =   'hb500  ;
//assign		data_Q_phase0_all[  9 * 16 -1 :  8 * 16 ] =   'hb500  ;
//assign		data_Q_phase0_all[ 10 * 16 -1 :  9 * 16 ] =   'hb500  ;
//assign		data_Q_phase0_all[ 11 * 16 -1 : 10 * 16 ] =   'hb500  ;
//assign		data_Q_phase0_all[ 12 * 16 -1 : 11 * 16 ] =   'hb500  ;
//assign		data_Q_phase0_all[ 13 * 16 -1 : 12 * 16 ] =   'hb500  ;
//assign		data_Q_phase0_all[ 14 * 16 -1 : 13 * 16 ] =   'hb500  ;
//assign		data_Q_phase0_all[ 15 * 16 -1 : 14 * 16 ] =   'hb500  ;
//assign		data_Q_phase0_all[ 16 * 16 -1 : 15 * 16 ] =   'hb500  ;

//////////////////////////////////////////////////////////////////////////////////
////////// Doppler
//////////////////////////////////////////////////////////////////////////////////

	wire[ 16* 2 -1 :0 ] 	data_I_dpl_all	;
	wire[ 16* 2 -1 :0 ] 	data_Q_dpl_all	;
	wire[ 16* 4 -1 :0 ] 	data_RF_dpl_all	;
doppler_gen doppler_gen(
	.rx_DPL_clk           					  	(	dac_clk				),
	.rx_DPL_rst           					  	(	0			        ),
	.rx_carrier_fcw           					(	carrier_fcw			),
	.rx_DPL_ce            					  	(	1'b1				),
//	.rx_DPL_DinBuxI_xb     						(	data_I_phase0_all	),
//	.rx_DPL_DinBuxQ_xb     						(	data_Q_phase0_all	),
//	.rx_DPL_on		      						(	1'b1				),
	.tx_DPL_DoutBus_xb                          (	data_RF_dpl_all		)
);

//////////////////////////////////////////////////////////////////////////////////
////////// Power Atten
//////////////////////////////////////////////////////////////////////////////////
	wire	[17:0]	dout_pat_i	;
	wire	[17:0]	dout_pat_q	;	


	reg	[17:0]	reg_dout_pat_i	=0;
	reg	[17:0]	reg_dout_pat_q	=0;	
    always @( posedge dac_clk  )
    begin
        reg_dout_pat_i  <=  dout_pat_i  ;
    end


//	power_atten_table	power_atten_table(
//		.addra	(	send_power_atten	),
//		.addrb	(	send_power_atten	),
//		.clka	(	dac_clk				),
//		.clkb	(	dac_clk				),
//		.douta	(	dout_pat_i			),
//		.doutb	(	dout_pat_q			)
//	);
	
//	power_atten_table	power_atten_table(
//		.addra	(	send_power_atten	),
////		.addrb	(	send_power_atten	),
//		.clka	(	dac_clk				),
////		.clkb	(	dac_clk				),
//		.douta	(	dout_pat_i			)
////		.doutb	(	dout_pat_q			)
//	);
	assign dout_pat_i = 18'h04000;
	wire[16*4 -1 :0 ] 	pout_atten_i	;
	wire[16*8 -1 :0 ] 	pout_atten_q	;
	
	// Instantiate each multiplier separately.  An array of IP instances relies on
	// tool-specific port-array expansion, which can fail when binding the IP
	// wrapper; explicit slices make each core's 18x16-bit interface unambiguous.
	genvar rf_ch;
	generate
		for (rf_ch = 0; rf_ch < 4; rf_ch = rf_ch + 1) begin : gen_mult_18x16_rf
			mult_18x16 mult_18x16_RF (
				.A   (reg_dout_pat_i),
				.B   (data_RF_dpl_all[rf_ch*16 +: 16]),
				.CLK (dac_clk),
				.P   (pout_atten_i[rf_ch*16 +: 16])
			);
		end
	endgenerate
//	mult_18x16	mult_18x16_Q[7:0]	(
//		.A		(	reg_dout_pat_i		),
//		.B		(	mod_out_temp_Q		),
//		.CLK	(	dac_clk				),
//		.P		(	pout_atten_q		)
//	);

reg [16*16 -1 :0 ] reg_pout_atten_i	= 0 ;
    always @( posedge dac_clk  )
    begin
        reg_pout_atten_i  <=  pout_atten_i  ;
    end

reg  [16*4-1:0]  	 reg_source_doutRF   	= 0 ;   

    always @( posedge dac_clk  )
    begin

        	reg_source_doutRF =  reg_pout_atten_i;

    end  
  

assign      source_doutRF  =  reg_source_doutRF     ;
   
   
//ila_adc_data ila_dac (
//	.clk(dac_clk), // input wire clk


//	.probe0(data_RF_dpl_all[  1 *16-1 :  1 *16-16 ]), // input wire [15:0]  probe0  
//	.probe1(data_RF_dpl_all[  2 *16-1 :  2 *16-16 ]), // input wire [15:0]  probe1 
//	.probe2(data_RF_dpl_all[  3 *16-1 :  3 *16-16 ]), // input wire [15:0]  probe2 
//	.probe3(data_RF_dpl_all[  4 *16-1 :  4 *16-16 ]), // input wire [15:0]  probe3
//	.probe4(pout_atten_i   [  1 *16-1 :  1 *16-16 ]), // input wire [15:0]  probe4  
//	.probe5(pout_atten_i   [  2 *16-1 :  2 *16-16 ]), // input wire [15:0]  probe5 
//	.probe6(pout_atten_i   [  3 *16-1 :  3 *16-16 ]), // input wire [15:0]  probe6 
//	.probe7(pout_atten_i   [  4 *16-1 :  4 *16-16 ])  // input wire [15:0]  probe7
//); 
   
   
endmodule
