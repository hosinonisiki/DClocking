`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2026/02/03 09:32:52
// Design Name: 
// Module Name: transport
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


module transport(
input [63:0]datain,

output [63:0] dataout,
output [63:0] dataout_lsb,
output [63:0] dataout_msb
);

wire [63:0] datain_r1;
wire [63:0] datain_lsb_r1;
wire [63:0] datain_msb_r1;
assign datain_r1 = {    
						datain [55:48],datain [63:56],
						datain [39:32],datain [47:40],
						datain [23:16],datain [31:24],	
						datain [7:0 ] ,datain [15:8 ]				
					};
//assign datain_r1 = {    datain [39:32],datain [47:40],
//						datain [55:48],datain [63:56],
//						datain [7:0 ] ,datain [15:8 ],
//						datain [23:16],datain [31:24]
						
//					};
assign datain_lsb_r1 = {datain [23:16],datain [31:24],
						datain [55:48],datain [63:56],
						datain [7:0 ],datain [15:8 ],
						datain [39:32],datain [47:40] 
						
					};			


assign datain_msb_r1 = {
						datain [39:32] , datain [47:40] ,
						datain [ 7: 0] , datain [15: 8] ,
						datain [55:48] , datain [63:56] ,
						datain [23:16] , datain [31:24]
					};		
		assign dataout     = datain_r1        ;
		assign dataout_lsb = datain_lsb_r1    ;
		assign dataout_msb = datain_msb_r1    ;

endmodule
