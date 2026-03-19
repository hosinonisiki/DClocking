`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2026/02/03 16:00:23
// Design Name: 
// Module Name: transport128
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


module transport128(
input [127:0]datain,

output [127:0] dataout,

output [127:0] dataout_lsb,
output [127:0] dataout_msb
);

wire [127:0] datain_r1;
wire [127:0] datain_lsb_r1;
wire [127:0] datain_msb_r1;
//assign datain_r1 = {    datain [47:40],datain [39:32],


//						datain [63:56],datain [55:48],
//						datain [15:8 ],datain [7:0 ],
//						datain [31:24], datain [23:16]
						
//					};
assign datain_r1 = {    datain [119:112],datain [127:120],  
                        datain [103:96],datain [111:104],
                        datain [87:80],datain [95:88], 
                        datain [71:64],datain [79:72],
						datain [55:48],datain [63:56],
						datain [39:32],datain [47:40],
						datain [23:16],datain [31:24],	
						datain [7:0 ] ,datain [15:8 ]				
					};
//assign datain_lsb_r1 = {datain [23:16],datain [31:24],
//						datain [55:48],datain [63:56],
//						datain [7:0 ],datain [15:8 ],
//						datain [39:32],datain [47:40] 
						
//					};			
										
assign datain_lsb_r1 = {
                        datain [23:16] , datain [31:24],   //a1
						datain [55:48] , datain [63:56] ,//a3	
						datain [119:112],datain [127:120],//a7
						datain [87:80],datain [95:88],//a5
						
						datain [ 7: 0] , datain [15: 8] , //a0	
					    datain [39:32] , datain [47:40] , //a2					    			                        																						
						datain [103:96],datain [111:104], //a6											
						datain [71:64],datain [79:72] //a4
																				
					};			

	

assign datain_msb_r1 = {
                        datain [71:64],datain [79:72], //a4                  
                        datain [103:96],datain [111:104], //a6
                        datain [39:32] , datain [47:40] , //a2
                        datain [ 7: 0] , datain [15: 8] , //a0	
                        
                        datain [87:80],datain [95:88],//a5                        
						datain [119:112],datain [127:120],//a7
					    datain [55:48] , datain [63:56], //a3	
					    datain [23:16] , datain [31:24]   //a1															
																															
					};	
//assign datain_msb_r1 = {
//						datain [71:64],datain [79:72],
//						datain [ 7: 0] , datain [15: 8] ,
//						datain [87:80],datain [95:88],
//						datain [23:16] , datain [31:24],
//						datain [103:96],datain [111:104],
//						datain [39:32] , datain [47:40] ,
//						datain [119:112],datain [127:120],
//						datain [55:48] , datain [63:56] 						
//					};						
											
//assign datain_r1 = {    
//						datain [103:96],datain [111:104],datain [119:112],datain [127:120],
//						datain [71:64],datain [79:72],datain [87:80],datain [95:88],
//						datain [39:32],datain [47:40],datain [55:48],datain [63:56],
//						datain [7:0 ] ,datain [15:8 ],datain [23:16],datain [31:24]
//					};					
//assign datain_r1 = {    datain [71:64],datain [79:72],datain [87:80],datain [95:88],
//						datain [103:96],datain [111:104],datain [119:112],datain [127:120],
//						datain [7:0 ] ,datain [15:8 ],datain [23:16],datain [31:24],
//						datain [39:32],datain [47:40],datain [55:48],datain [63:56]
						
//					};
//assign datain_lsb_r1 = {datain [39:32],datain [47:40],datain [55:48],datain [63:56],
//						datain [103:96],datain [111:104],datain [119:112],datain [127:120],
//						datain [7:0 ],datain [15:8 ],datain [23:16],datain [31:24],
//						datain [71:64],datain [79:72],datain [87:80],datain [95:88]
						
//					};			


//assign datain_msb_r1 = {
//						datain [71:64],datain [79:72],datain [87:80],datain [95:88] ,
//						datain [ 7: 0] , datain [15: 8] ,datain [23:16],datain [31:24],
//						datain [103:96],datain [111:104],datain [119:112],datain [127:120],
//						datain [39:32],datain [47:40],datain [55:48],datain [63:56]
//					};	
					
	
						
		assign dataout     = datain_r1       ;
		assign dataout_lsb = datain_lsb_r1    ;
		assign dataout_msb = datain_msb_r1    ;

endmodule
