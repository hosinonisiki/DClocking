`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2026/01/08 10:08:37
// Design Name: 
// Module Name: ChannelTriggerDetector
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


module ChannelTriggerDetector(
    input  wire        clk,
    input  wire        rst_n,
    
    // 数据输入
    input  wire [15:0] sig_a_buf,        // ADC输入数据
    input  wire [15:0] sig_b_buf,        
    input  wire [15:0] sig_c_buf,
    input  wire [15:0] sig_d_buf,  
    input  wire        data_valid_i,
    input  wire        ext_trigger_i,
    input  wire        capture_start_i,
    
    // 配置
    input  wire [2:0]  trigger_channel,
    input  wire [3:0]  reg_trigger_type,
    input  wire [15:0] reg_trigger_value,
    input  wire [15:0] reg_sustain_count,
    
    // 输出
    output wire        trigger_detected_o,
    output wire [15:0] trigger_data_o,
    output wire        trigger_data_valid_o
);

// 选择触发通道数据
    wire [15:0] selected_data;
    
    assign selected_data = (trigger_channel == 2'b00) ? sig_a_buf :
                           (trigger_channel == 2'b01) ? sig_b_buf :
                           (trigger_channel == 2'b10) ? sig_c_buf :
                            sig_d_buf;

   
    TriggerDetector u_trigger_detector (
        .clk                (clk),
        .rst_n              (rst_n),    
        .data_in            (selected_data),
        .data_valid_i       (data_valid_i),
        .ext_trigger_i      (ext_trigger_i),
        // 配置
        .reg_trigger_type   (reg_trigger_type),     // 触发类型
        .reg_trigger_value  (reg_trigger_value),    // 触发阈值
        .reg_sustain_count  (reg_sustain_count),    // 持续计数       
        // 输出
        .trigger_detected_o (trigger_detected_o),
        .trigger_data_o     (trigger_data_o),
        .trigger_data_valid_o(trigger_data_valid_o)

    );

endmodule
