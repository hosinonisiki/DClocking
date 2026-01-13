`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/12/25 13:55:02
// Design Name: 
// Module Name: TriggerDetector
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
// 触发检测模块（带噪声滤波）
//////////////////////////////////////////////////////////////////////////////////


module TriggerDetector (
    input  wire        clk,
    input  wire        rst_n,
    
    // 数据输入
    input  wire [15:0] data_in,        // ADC输入数据
    input  wire        data_valid_i,
    input  wire        ext_trigger_i,    
    // 配置
    input  wire [3:0]  reg_trigger_type,
    input  wire [15:0] reg_trigger_value,
    input  wire [15:0] reg_sustain_count,
    
    // 输出
    output reg         trigger_detected_o,
    output wire [15:0] trigger_data_o,
    output wire        trigger_data_valid_o,
    
    // 状态
    output reg         trigger_latched_o
);
    // 触发类型编码
    localparam TRIG_NONE        = 4'h0;   // 无触发（仅用于立即模式）
    localparam TRIG_GT          = 4'h1;   // 大于阈值
    localparam TRIG_LT          = 4'h2;   // 小于阈值
    localparam TRIG_EQ          = 4'h3;   // 等于阈值
    localparam TRIG_GT_SUSTAIN  = 4'h4;   // 持续大于
    localparam TRIG_LT_SUSTAIN  = 4'h5;   // 持续小于
    localparam TRIG_EQ_SUSTAIN  = 4'h6;   // 持续等于
    localparam TRIG_RISING_EDGE = 4'h7;   // 等于阈值且上升沿
    localparam TRIG_FALLING_EDGE= 4'h8;   // 等于阈值且下降沿  

//// ========== 内部信号 ==========
//// 消抖阈值
    localparam DEBOUNCE_THRESHOLD = 16'h0010; 
      
    // 消抖计数器（用于消除噪声干扰）
    reg [15:0] prev_data;
    reg trigger_condition_met;
    reg [15:0] sustain_counter;  // 持续条件计数器
    
    // 边沿检测
    wire rising_edge = (data_in > prev_data) && 
                      ((data_in - prev_data) > DEBOUNCE_THRESHOLD); // 阈值为16
    wire falling_edge = (data_in < prev_data) && 
                       ((prev_data - data_in) > DEBOUNCE_THRESHOLD);
 
  
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            trigger_condition_met <= 1'b0;           
        end 
        else if (data_valid_i) begin   
            // 检测触发条件
            case (reg_trigger_type)
                TRIG_NONE: trigger_condition_met = 1'b0;  // 无触发
                TRIG_GT: trigger_condition_met = (data_in > reg_trigger_value);// 大于
                TRIG_LT: trigger_condition_met = (data_in < reg_trigger_value);// 小于
                TRIG_EQ: trigger_condition_met = (data_in == reg_trigger_value);// 等于
                TRIG_GT_SUSTAIN: trigger_condition_met = (data_in > reg_trigger_value) && (sustain_counter >= reg_sustain_count); // 持续大于
                TRIG_LT_SUSTAIN: trigger_condition_met = (data_in < reg_trigger_value) && (sustain_counter >= reg_sustain_count); // 持续小于
                TRIG_EQ_SUSTAIN: trigger_condition_met = (data_in == reg_trigger_value) && (sustain_counter >= reg_sustain_count); // 持续等于             
                TRIG_RISING_EDGE: trigger_condition_met = rising_edge && (data_in == reg_trigger_value);// 上升沿
                TRIG_FALLING_EDGE: trigger_condition_met = falling_edge && (data_in == reg_trigger_value);// 下降沿 
                default: trigger_condition_met = 0;
            endcase        
        end
    end
    
    
     always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            trigger_detected_o <= 1'b0;
            sustain_counter <= 16'h0;
            prev_data <= 16'h0;
        end 
        else if (data_valid_i) begin
            prev_data <= data_in;        
            // 持续条件检测
            if (reg_trigger_type == TRIG_GT_SUSTAIN ||  reg_trigger_type == TRIG_LT_SUSTAIN ||reg_trigger_type == TRIG_EQ_SUSTAIN) begin
                if (trigger_condition_met) begin
                    if (sustain_counter < 16'hFFFF) begin
                        sustain_counter <= sustain_counter + 1'b1;
                    end
                    else begin
                        sustain_counter <= sustain_counter;
                    end
                end 
                else begin
                    sustain_counter <= 16'h0;
                end
                // 持续条件
                trigger_detected_o <= (sustain_counter >= 4);
            end
            else begin
                // 简单条件检测
                trigger_detected_o <= trigger_condition_met || ext_trigger_i;
            end
        end
    end   
    
    // 数据直通
    assign trigger_data_o = data_in;
    assign trigger_data_valid_o = data_valid_i;  
    
     
     
        
endmodule
