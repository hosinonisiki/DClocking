`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2026/02/07 10:59:01
// Design Name: 
// Module Name: doppler_gen
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


module doppler_gen(
	input	rx_DPL_clk           					  ,
	input	rx_DPL_rst           					  ,
	input	rx_DPL_ce            					  ,

	input	[ 64 - 1 : 0 ]	    rx_carrier_fcw        ,
	output	[ 16 * 4 - 1 : 0 ]	tx_DPL_DoutBus_xb   
    );
	



	
//////////////////////////////////////////////////////////////////////////////
//                                                                            
//相位累加                                                                            
//                                                                            
//////////////////////////////////////////////////////////////////////////////

wire	[ 64 * 1 - 1 : 0 ]	doppler_p16_step    ;


reg	[ 64 * 1 - 1 : 0 ]	phase_p16_step  = 64'b0   ; 

	always@(posedge rx_DPL_clk ) begin
	   if(rx_DPL_rst) begin
	       phase_p16_step  <= 64'b0 ;
	   end else begin
		  phase_p16_step		<=  rx_carrier_fcw		 ;
		end
	end



wire	[ 4 * 32 - 1 : 0 ]	CWPA_PhsAccBus_96b   ;
	
CWPhsAccu_p4   I_CWPhsAccu_p4(
	.rx_CWPA_clk          ( rx_DPL_clk           ) ,
	.rx_CWPA_rst          ( rx_DPL_rst           ) ,
	.rx_CWPA_ce           ( 1'b1                 ) ,
        
	.rx_CWPA_PhsErr_32b   ( phase_p16_step       ) ,
        
	.tx_CWPA_PhsAcc_xb    ( CWPA_PhsAccBus_96b   )

);
//////////////////////////////////////////////////////////////////////////////
//                                                                            
//DDS                                                                            
//                                                                            
//////////////////////////////////////////////////////////////////////////////
wire	[ 16 * 4 - 1 : 0 ]	CWPA_PhsAccBus_128b   ;	


wire	[ 4 * 26 - 1 : 0 ]	dds_carrier_SineOut_96b    ;
wire	[ 4 * 26 - 1 : 0 ]	dds_carrier_CosineOut_96b  ;
wire	[ 4 * 16 - 1 : 0 ]	dds_carrier_CosineOut_64b  ;
wire	[ 4 * 64 - 1 : 0 ]	dds_carrier_Out_96b        ;
wire	[ 4 * 1 - 1 : 0 ] 	                dds_carrier_valid          ;

dds_carrier dds_carrier[3:0] (
  .aclk(rx_DPL_clk),                                // input wire aclk
  .s_axis_phase_tvalid(1'b1),  // input wire s_axis_phase_tvalid
  .s_axis_phase_tdata(CWPA_PhsAccBus_96b),    // input wire [15 : 0] s_axis_phase_tdata
  .m_axis_data_tvalid(dds_carrier_valid ),    // output wire m_axis_data_tvalid
  .m_axis_data_tdata(dds_carrier_CosineOut_64b)      // output wire [31 : 0] m_axis_data_tdata
);

	
reg	[ 16 * 4 - 1 : 0 ]	DPL_DoutBusRF_xb ='b0 	;

	always@(posedge rx_DPL_clk ) begin
		DPL_DoutBusRF_xb     <=  dds_carrier_CosineOut_64b    ;
//		DPL_DoutBusRF_xb     <=  Mult_RF_shift    ;
	end
	
//	assign	tx_DPL_DoutBusI_xb	=	DPL_DoutBusI_xb	;
//	assign	tx_DPL_DoutBusQ_xb	=	DPL_DoutBusQ_xb	;
	assign	tx_DPL_DoutBus_xb	=	DPL_DoutBusRF_xb	;
	
	
	
endmodule
