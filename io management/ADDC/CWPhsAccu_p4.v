`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2026/02/07 11:00:36
// Design Name: 
// Module Name: CWPhsAccu_p4
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


module CWPhsAccu_p4(

	rx_CWPA_clk          ,
	rx_CWPA_rst          ,
	rx_CWPA_ce           ,

	rx_CWPA_PhsErr_32b   ,

	tx_CWPA_PhsAcc_xb
);




/////////////////////////////////////////////////////////////////////////////
//
// parameters
//
/////////////////////////////////////////////////////////////////////////////
parameter	DATA_WIDTH = 25	;

input	rx_CWPA_clk          ;
input	rx_CWPA_rst          ;
input	rx_CWPA_ce           ;

input	[ 63 : 0 ]	rx_CWPA_PhsErr_32b   ;
                     
output	[ 32 * 4 - 1 : 0 ]	tx_CWPA_PhsAcc_xb   ;

/////////////////////////////////////////////////////////////////////////////
//
// regs & wires
//
/////////////////////////////////////////////////////////////////////////////

wire	signed	[ 67 : 0 ]	PhsErr_35b	;
assign	PhsErr_35b = { {2{rx_CWPA_PhsErr_32b [ 63 ]}}, rx_CWPA_PhsErr_32b } ;

reg	signed	[ 65 : 0 ]	PhsErr1_35b	 = 0	;
reg	signed	[ 65 : 0 ]	PhsErr2_35b	 = 0	;
reg	signed	[ 65 : 0 ]	PhsErr3_35b	 = 0	;
reg	signed	[ 65 : 0 ]	PhsErr4_35b	 = 0	;
//reg	signed	[ 67 : 0 ]	PhsErr5_35b	 = 0	;
//reg	signed	[ 67 : 0 ]	PhsErr6_35b	 = 0	;
//reg	signed	[ 67 : 0 ]	PhsErr7_35b	 = 0	;
//reg	signed	[ 67 : 0 ]	PhsErr8_35b	 = 0	;
//reg	signed	[ 67 : 0 ]	PhsErr9_35b	 = 0	;
//reg	signed	[ 67 : 0 ]	PhsErr10_35b = 0	;
//reg	signed	[ 67 : 0 ]	PhsErr11_35b = 0	;
//reg	signed	[ 67 : 0 ]	PhsErr12_35b = 0	;
//reg	signed	[ 67 : 0 ]	PhsErr13_35b = 0	;
//reg	signed	[ 67 : 0 ]	PhsErr14_35b = 0	;
//reg	signed	[ 67 : 0 ]	PhsErr15_35b = 0	;
//reg	signed	[ 67 : 0 ]	PhsErr16_35b = 0	;

reg	[ 65 : 0 ]	PhsAcc_temp0_35b	= 66'h3_ffff_ffff_ffff_ffff	;
reg	[ 65 : 0 ]	PhsAcc_temp1_35b	= 66'h3_ffff_ffff_ffff_ffff	;
reg	[ 65 : 0 ]	PhsAcc_temp2_35b	= 66'h3_ffff_ffff_ffff_ffff	;
reg	[ 65 : 0 ]	PhsAcc_temp3_35b	= 66'h3_ffff_ffff_ffff_ffff	;
//reg	[ 67 : 0 ]	PhsAcc_temp4_35b	= 68'hf_ffff_ffff_ffff_ffff	;
//reg	[ 67 : 0 ]	PhsAcc_temp5_35b	= 68'hf_ffff_ffff_ffff_ffff	;
//reg	[ 67 : 0 ]	PhsAcc_temp6_35b	= 68'hf_ffff_ffff_ffff_ffff	;
//reg	[ 67 : 0 ]	PhsAcc_temp7_35b	= 68'hf_ffff_ffff_ffff_ffff	;
//reg	[ 67 : 0 ]	PhsAcc_temp8_35b	= 68'hf_ffff_ffff_ffff_ffff	;
//reg	[ 67 : 0 ]	PhsAcc_temp9_35b	= 68'hf_ffff_ffff_ffff_ffff	;
//reg	[ 67 : 0 ]	PhsAcc_temp10_35b	= 68'hf_ffff_ffff_ffff_ffff	;
//reg	[ 67 : 0 ]	PhsAcc_temp11_35b	= 68'hf_ffff_ffff_ffff_ffff	;
//reg	[ 67 : 0 ]	PhsAcc_temp12_35b	= 68'hf_ffff_ffff_ffff_ffff	;
//reg	[ 67 : 0 ]	PhsAcc_temp13_35b	= 68'hf_ffff_ffff_ffff_ffff	;
//reg	[ 67 : 0 ]	PhsAcc_temp14_35b	= 68'hf_ffff_ffff_ffff_ffff	;
//reg	[ 67 : 0 ]	PhsAcc_temp15_35b	= 68'hf_ffff_ffff_ffff_ffff	;


//////////////////////////////////////////////////////////////////////////////
//
//累加
//
//////////////////////////////////////////////////////////////////////////////
always @( posedge rx_CWPA_clk  )
begin        
	if(rx_CWPA_rst) begin
		PhsErr1_35b		<= 0	;
		PhsErr2_35b		<= 0	;
		PhsErr3_35b		<= 0	;
		PhsErr4_35b		<= 0	;
//		PhsErr5_35b		<= 0	;
//		PhsErr6_35b		<= 0	;
//		PhsErr7_35b		<= 0	;
//		PhsErr8_35b		<= 0	;
//		PhsErr9_35b		<= 0	;
//		PhsErr10_35b	<= 0	;
//		PhsErr11_35b	<= 0	;
//		PhsErr12_35b	<= 0	;
//		PhsErr13_35b	<= 0	;
//		PhsErr14_35b	<= 0	;
//		PhsErr15_35b	<= 0	;
//		PhsErr16_35b	<= 0	;

		PhsAcc_temp0_35b	<= 66'h3_ffff_ffff_ffff_ffff	;
		PhsAcc_temp1_35b	<= 66'h3_ffff_ffff_ffff_ffff	;
		PhsAcc_temp2_35b	<= 66'h3_ffff_ffff_ffff_ffff	;
		PhsAcc_temp3_35b	<= 66'h3_ffff_ffff_ffff_ffff	;
//		PhsAcc_temp4_35b	<= 68'hf_ffff_ffff_ffff_ffff	;
//		PhsAcc_temp5_35b	<= 68'hf_ffff_ffff_ffff_ffff	;
//		PhsAcc_temp6_35b	<= 68'hf_ffff_ffff_ffff_ffff	;
//		PhsAcc_temp7_35b	<= 68'hf_ffff_ffff_ffff_ffff	;
//		PhsAcc_temp8_35b	<= 68'hf_ffff_ffff_ffff_ffff	;
//		PhsAcc_temp9_35b	<= 68'hf_ffff_ffff_ffff_ffff	;
//		PhsAcc_temp10_35b	<= 68'hf_ffff_ffff_ffff_ffff	;
//		PhsAcc_temp11_35b	<= 68'hf_ffff_ffff_ffff_ffff	;
//		PhsAcc_temp12_35b	<= 68'hf_ffff_ffff_ffff_ffff	;
//		PhsAcc_temp13_35b	<= 68'hf_ffff_ffff_ffff_ffff	;
//		PhsAcc_temp14_35b	<= 68'hf_ffff_ffff_ffff_ffff	;
//		PhsAcc_temp15_35b	<= 68'hf_ffff_ffff_ffff_ffff	;
	end else begin
	   if ( rx_CWPA_ce )
	   begin
			PhsErr1_35b  <= ( PhsErr_35b       )                         ;
			PhsErr2_35b  <= ( PhsErr_35b <<< 1 )                         ;
			PhsErr3_35b  <= ( PhsErr_35b       ) + ( PhsErr_35b <<< 1 )  ;
			PhsErr4_35b  <= ( PhsErr_35b <<< 2 )                         ;
//			PhsErr5_35b  <= ( PhsErr_35b <<< 2 ) + ( PhsErr_35b       )  ;
//			PhsErr6_35b  <= ( PhsErr_35b <<< 2 ) + ( PhsErr_35b <<< 1 )  ;
//			PhsErr7_35b  <= ( PhsErr_35b <<< 3 ) - ( PhsErr_35b       )  ;
//			PhsErr8_35b  <= ( PhsErr_35b <<< 3 )                         ; 
//			PhsErr9_35b  <= ( PhsErr_35b <<< 3 ) + ( PhsErr_35b       )  ;
//			PhsErr10_35b <= ( PhsErr_35b <<< 3 ) + ( PhsErr_35b <<< 1 )  ;
//			PhsErr11_35b <= ( PhsErr_35b <<< 3 ) + ( PhsErr_35b <<< 1 )  + ( PhsErr_35b       )  ;
//			PhsErr12_35b <= ( PhsErr_35b <<< 3 ) + ( PhsErr_35b <<< 2 )  ;
//			PhsErr13_35b <= ( PhsErr_35b <<< 3 ) + ( PhsErr_35b <<< 2 )  + ( PhsErr_35b       )  ;
//			PhsErr14_35b <= ( PhsErr_35b <<< 4 ) - ( PhsErr_35b <<< 1 )  ;
//			PhsErr15_35b <= ( PhsErr_35b <<< 4 ) - ( PhsErr_35b       )  ;
//			PhsErr16_35b <= ( PhsErr_35b <<< 4 )                         ; 
	   end                                                     
	   else                                                    
	   begin                                                   
	   end
	   
	   if ( rx_CWPA_ce )
	   begin
		
		PhsAcc_temp0_35b  <= PhsAcc_temp3_35b + PhsErr1_35b 	;
		PhsAcc_temp1_35b  <= PhsAcc_temp3_35b + PhsErr2_35b 	;
		PhsAcc_temp2_35b  <= PhsAcc_temp3_35b + PhsErr3_35b 	;
		PhsAcc_temp3_35b  <= PhsAcc_temp3_35b + PhsErr4_35b 	;
//		PhsAcc_temp4_35b  <= PhsAcc_temp15_35b + PhsErr5_35b 	;
//		PhsAcc_temp5_35b  <= PhsAcc_temp15_35b + PhsErr6_35b 	;
//		PhsAcc_temp6_35b  <= PhsAcc_temp15_35b + PhsErr7_35b 	;
//		PhsAcc_temp7_35b  <= PhsAcc_temp15_35b + PhsErr8_35b 	;
//		PhsAcc_temp8_35b  <= PhsAcc_temp15_35b + PhsErr9_35b 	;
//		PhsAcc_temp9_35b  <= PhsAcc_temp15_35b + PhsErr10_35b	;
//		PhsAcc_temp10_35b <= PhsAcc_temp15_35b + PhsErr11_35b	;
//		PhsAcc_temp11_35b <= PhsAcc_temp15_35b + PhsErr12_35b	;
//		PhsAcc_temp12_35b <= PhsAcc_temp15_35b + PhsErr13_35b	;
//		PhsAcc_temp13_35b <= PhsAcc_temp15_35b + PhsErr14_35b	;
//		PhsAcc_temp14_35b <= PhsAcc_temp15_35b + PhsErr15_35b	;
//		PhsAcc_temp15_35b <= PhsAcc_temp15_35b + PhsErr16_35b	;
			
	   end
	   else
	   begin
	   end
	end
end
        
//////////////////////////////////////////////////////////////////////////////
//
//Out
//
//////////////////////////////////////////////////////////////////////////////
assign	tx_CWPA_PhsAcc_xb [  1 * 32 - 1 :  0 * 32 ] = { 7'b0, PhsAcc_temp0_35b  [ 63 : 63 - DATA_WIDTH + 1 ]	} ;
assign	tx_CWPA_PhsAcc_xb [  2 * 32 - 1 :  1 * 32 ] = { 7'b0, PhsAcc_temp1_35b  [ 63 : 63 - DATA_WIDTH + 1 ]	} ;
assign	tx_CWPA_PhsAcc_xb [  3 * 32 - 1 :  2 * 32 ] = { 7'b0, PhsAcc_temp2_35b  [ 63 : 63 - DATA_WIDTH + 1 ]	} ;
assign	tx_CWPA_PhsAcc_xb [  4 * 32 - 1 :  3 * 32 ] = { 7'b0, PhsAcc_temp3_35b  [ 63 : 63 - DATA_WIDTH + 1 ]	} ;
//assign	tx_CWPA_PhsAcc_xb [  5 * 32 - 1 :  4 * 32 ] = { 7'b0, PhsAcc_temp4_35b  [ 63 : 63 - DATA_WIDTH + 1 ]	} ;
//assign	tx_CWPA_PhsAcc_xb [  6 * 32 - 1 :  5 * 32 ] = { 7'b0, PhsAcc_temp5_35b  [ 63 : 63 - DATA_WIDTH + 1 ]	} ;
//assign	tx_CWPA_PhsAcc_xb [  7 * 32 - 1 :  6 * 32 ] = { 7'b0, PhsAcc_temp6_35b  [ 63 : 63 - DATA_WIDTH + 1 ]	} ;
//assign	tx_CWPA_PhsAcc_xb [  8 * 32 - 1 :  7 * 32 ] = { 7'b0, PhsAcc_temp7_35b  [ 63 : 63 - DATA_WIDTH + 1 ]	} ;
//assign	tx_CWPA_PhsAcc_xb [  9 * 32 - 1 :  8 * 32 ] = { 7'b0, PhsAcc_temp8_35b  [ 63 : 63 - DATA_WIDTH + 1 ]	} ;
//assign	tx_CWPA_PhsAcc_xb [ 10 * 32 - 1 :  9 * 32 ] = { 7'b0, PhsAcc_temp9_35b  [ 63 : 63 - DATA_WIDTH + 1 ]	} ;
//assign	tx_CWPA_PhsAcc_xb [ 11 * 32 - 1 : 10 * 32 ] = { 7'b0, PhsAcc_temp10_35b [ 63 : 63 - DATA_WIDTH + 1 ]	} ;
//assign	tx_CWPA_PhsAcc_xb [ 12 * 32 - 1 : 11 * 32 ] = { 7'b0, PhsAcc_temp11_35b [ 63 : 63 - DATA_WIDTH + 1 ]	} ;
//assign	tx_CWPA_PhsAcc_xb [ 13 * 32 - 1 : 12 * 32 ] = { 7'b0, PhsAcc_temp12_35b [ 63 : 63 - DATA_WIDTH + 1 ]	} ;
//assign	tx_CWPA_PhsAcc_xb [ 14 * 32 - 1 : 13 * 32 ] = { 7'b0, PhsAcc_temp13_35b [ 63 : 63 - DATA_WIDTH + 1 ]	} ;
//assign	tx_CWPA_PhsAcc_xb [ 15 * 32 - 1 : 14 * 32 ] = { 7'b0, PhsAcc_temp14_35b [ 63 : 63 - DATA_WIDTH + 1 ]	} ;
//assign	tx_CWPA_PhsAcc_xb [ 16 * 32 - 1 : 15 * 32 ] = { 7'b0, PhsAcc_temp15_35b [ 63 : 63 - DATA_WIDTH + 1 ]	} ;

//////////////////////////////////////////////////////////////////////////////
//
//
//
//////////////////////////////////////////////////////////////////////////////


endmodule
