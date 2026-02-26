`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2026/01/05 17:29:07
// Design Name: 
// Module Name: adc_sample
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


module adc_sample(
    input  wire        clk,
    input  wire        rst,
    input  wire [63:0] adc_data,
    input  wire        adc_valid_i,
    output reg         adc_buf_wr,
    output wire [63:0] adc_buf_data,
    
    input  wire [31:0] sample_len,
    input  wire        ad_sample_req,
    output reg         ad_sample_ack,                           
    input  wire        write_req_ack,
    output reg         write_req
       );
       
//`define TRIGGER

    localparam       S_IDLE     = 3'h0;
    localparam       S_REQ      = 3'h1;
    localparam       S_ACK_WAIT = 3'h2;
    localparam       S_SAMPLE   = 3'h3;
    localparam       S_WAIT     = 3'h4;
    
    
    reg signed[15:0]     adc_data_wide;
    reg signed[15:0]     adc_data_wide_d0;
    reg [31:0]           sample_cnt;
    reg [31:0]           wait_cnt;
    
    reg                  ad_sample_req_d0     ;
    reg                  ad_sample_req_d1     ;
    reg                  ad_sample_req_d2     ;
    
    reg [2:0]            state;
    
    assign adc_buf_data = adc_data;
      
      
//    always@(posedge clk or posedge rst) begin
//        if(rst == 1'b1)
//            adc_data_wide <= 16'd0;
//        else
//            adc_data_wide <= adc_data;
//    end
      
      
    always @(posedge clk or posedge rst)begin
        if (rst)begin
            ad_sample_req_d0 <= 1'b0 ;
            ad_sample_req_d1 <= 1'b0 ;
            ad_sample_req_d2 <= 1'b0 ;
        end
        else begin
            ad_sample_req_d0 <= ad_sample_req ;
            ad_sample_req_d1 <= ad_sample_req_d0 ;
            ad_sample_req_d2 <= ad_sample_req_d1 ;
        end
    end
     assign   ad_sample_req_pos = ad_sample_req_d1 & (~ad_sample_req_d2);
      
    always@(posedge clk or posedge rst)begin
        if(rst == 1'b1) begin
            state <= S_IDLE;
            wait_cnt <= 32'd0;
            sample_cnt <= 32'd0;
            adc_buf_wr <= 1'b0;
            ad_sample_ack <= 1'b0 ;
            write_req <= 1'b0;
        end
        else begin
            case(state)
                S_IDLE:begin
                    if (ad_sample_req_pos)begin
                        write_req <= 1'b1 ;
                        state <= S_REQ;                      
                    end
                    else begin
                        state <= S_IDLE ;
                        wait_cnt <= 32'd0;
                        sample_cnt <= 32'd0;
                        adc_buf_wr <= 1'b0;
                        ad_sample_ack <= 1'b0 ;
                        write_req <= 1'b0;
                    end
                end
                S_REQ :begin
                    if (write_req_ack)begin
                        write_req <= 1'b0 ;
                        state <= S_ACK_WAIT ;
                    end
                    else
                        state <= S_REQ ;
                end
                S_ACK_WAIT: begin
                    if (wait_cnt == 32'd40)begin
                        state <= S_SAMPLE ;
                        wait_cnt <= 32'd0 ;
                    end
                    else  begin
                        wait_cnt <= wait_cnt + 1'b1 ;
                        state <= S_ACK_WAIT ;
                    end
                end
                S_SAMPLE:  begin                 
                    ad_sample_ack <= 1'b1 ;
                    if(sample_cnt == sample_len)begin
                        sample_cnt <= 32'd0;
                        adc_buf_wr <= 1'b0;
                        state <= S_WAIT;
                    end
                    else  begin
                        sample_cnt <= adc_valid_i ? (sample_cnt + 32'd1) :sample_cnt;
                        adc_buf_wr <= 1'b1;
                    end   
                end
                S_WAIT: begin
                    ad_sample_ack <= 1'b0 ;
                    state <= S_IDLE;
                end
                default:
                  state <= S_IDLE;
            endcase
        end
    end
endmodule  
