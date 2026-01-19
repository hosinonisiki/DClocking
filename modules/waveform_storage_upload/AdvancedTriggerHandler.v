`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/12/29 08:55:57
// Design Name: 
// Module Name: AdvancedTriggerHandler
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
// 高级触发模式处理（环形缓冲）
//////////////////////////////////////////////////////////////////////////////////


module AdvancedTriggerHandler (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [15:0] sig_a_buf,        
    input  wire [15:0] sig_b_buf,        
    input  wire [15:0] sig_c_buf,
    input  wire [15:0] sig_d_buf,  
    input  wire        data_valid_i,
    //触发信号
    input  wire        trigger_detected,
    input  wire        adv_trigger_mode,
    input  wire        adv_trigger_mode_stop,   
    input  wire [15:0] pre_trigger_points,
//    input  wire [15:0] post_trigger_points,
    input  wire [3:0]  upload_channels,   
    output reg  [63:0] data_out,
    output reg         data_out_valid,
    output wire [31:0] adv_data_num
);
    
    // 环形缓冲区，存储触发前后的数据
    parameter RING_BUFFER_SIZE = 4096;  // 4K样本
    
    reg [15:0] ring_buffer0 [0:RING_BUFFER_SIZE-1];
    reg [15:0] ring_buffer1 [0:RING_BUFFER_SIZE-1];
    reg [15:0] ring_buffer2 [0:RING_BUFFER_SIZE-1];
    reg [15:0] ring_buffer3 [0:RING_BUFFER_SIZE-1];
                
    reg [15:0] write_ptr, read_ptr;
    reg [15:0] trigger_ptr;
    reg capturing;
    reg  [31:0] output_counter;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            write_ptr <= 16'h0;
            read_ptr <= 16'h0;
            trigger_ptr <= 16'h0;
            capturing <= 1'b0;
            data_out_valid <= 1'b0;
            output_counter <= 32'h0;
            data_out      <= 64'd0;
        end 
        else if (adv_trigger_mode) begin
            if (data_valid_i) begin
            // 持续写入环形缓冲区
                ring_buffer0[write_ptr] <= sig_a_buf;
                ring_buffer1[write_ptr] <= sig_b_buf;           
                ring_buffer2[write_ptr] <= sig_c_buf;           
                ring_buffer3[write_ptr] <= sig_d_buf;                 
                write_ptr <= (write_ptr + 1)% RING_BUFFER_SIZE ;        
                if (trigger_detected && !capturing) begin
                    capturing <= 1;
                    trigger_ptr <= write_ptr;  // 记录触发位置
                    output_counter <= 32'h0;
                    // 计算读取起始位置（触发前）
                    if (write_ptr >= (pre_trigger_points )) begin
                        read_ptr <= (write_ptr - pre_trigger_points) % RING_BUFFER_SIZE;
                    end
                    else begin
                        read_ptr <= RING_BUFFER_SIZE - ((pre_trigger_points) - write_ptr);
                    end
                end
                // 触发后数据输出
                else if (capturing) begin
                    // 读取触发前后的数据
                    data_out[15:0]  <= upload_channels[0] ? ring_buffer0[read_ptr] : 16'h0;
                    data_out[31:16] <= upload_channels[1] ? ring_buffer1[read_ptr] : 16'h0;
                    data_out[47:32] <= upload_channels[2] ? ring_buffer2[read_ptr] : 16'h0;
                    data_out[63:48] <= upload_channels[3] ? ring_buffer3[read_ptr] : 16'h0;
                 
                    data_out_valid <= 1;
                    read_ptr <= (read_ptr + 1) % RING_BUFFER_SIZE;
                    output_counter <= output_counter + 32'h1;
                end
            end
            else begin
                data_out_valid <= 1'b0;
            end
        end
        else if(adv_trigger_mode_stop) begin
            capturing <= 0;
            data_out_valid <= 1'b0;           
        end
        
    end         
   
   assign adv_data_num = output_counter; 
endmodule
