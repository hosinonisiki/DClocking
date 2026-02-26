`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/12/24 10:56:51
// Design Name: 
// Module Name: MainController
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

module MainController (
    input  wire        clk,
    input  wire        rst_n,
    
    // 控制输入
    input  wire        start_cmd,
    input  wire [15:0] reg_capture_len,
    input  wire        ext_trigger_i,
    input  wire        single_mode,
    input  wire        continuous_mode,
    input  wire        immediate_mode,
    input  wire        normal_trigger_mode,   
    input  wire        adv_trigger_mode, 
    input  wire        adv_trigger_mode_stop,       
    // 状态输入
    input  wire        preprocessed_valid,
    input  wire        trigger_detected,
    
    input  wire        eth_ready_i, 
    input  wire        upload_complete, 
    // 控制输出
    output reg         capture_start_o,
    output reg         capture_en_o,
    output reg         upload_start_o,
    output reg         upload_en_o,
    output reg [31:0]  capture_counter,
    // 状态输出
    output reg  [3:0]  fsm_state_o

//    output wire        operation_mode_o
);
    
    // ========== 状态定义 ==========
   localparam     IDLE        = 4'h0;
   localparam     CONFIG      = 4'h1;
   localparam     WAIT_TRIG   = 4'h2;
   localparam     PRE_CAPTURE = 4'h3;
   localparam     CAPTURING   = 4'h4;
   localparam     WAIT_ADV_TRIG   = 4'h5;
   localparam     PRE_ADV_CAPTURE = 4'h6;
   localparam     ADV_CAPTURING   = 4'h7;
   localparam     POST_CAPTURE= 4'h8;
   localparam     PRE_UPLOAD  = 4'h9;
   localparam     UPLOADING   = 4'hA;
   localparam     POST_UPLOAD = 4'hB;
    
    // ========== 内部信号 ==========
    reg [3:0]  state;

    
//    reg [31:0] capture_counter;
    reg [31:0] capture_length;
    reg        capture_complete;

    
                
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            fsm_state_o <= 4'h0;
            capture_start_o <= 1'b0;
            upload_start_o <= 1'b0;
        end
        else begin      
            case (state)
                IDLE: begin
                    if (start_cmd) begin
                        state <= CONFIG;
                    end
                    else begin
                        capture_start_o <= 1'b0;
                        upload_start_o <= 1'b0;
                    end
                end           
                CONFIG: begin              
                    // 计算捕获长度
                    capture_length <=  32'h1 <<reg_capture_len; 
                    if (immediate_mode) begin
                        state <= PRE_CAPTURE;
                        capture_start_o <= 1'b1;
                    end 
                    else if(normal_trigger_mode)begin
                        state <= WAIT_TRIG;
                    end
                     else if(adv_trigger_mode)begin
                        state <= WAIT_ADV_TRIG;
                    end
                end
            
                WAIT_TRIG: begin
                    if (trigger_detected || ext_trigger_i) begin
                        state <= PRE_CAPTURE;
                        capture_start_o <= 1'b1;
                    end
                end                                       
                PRE_CAPTURE: begin
                    state <= CAPTURING;
                end
            
                CAPTURING: begin
                    if (capture_complete) begin
                        state <= POST_CAPTURE;
                    end               
                end
                
                WAIT_ADV_TRIG: begin
                    if (trigger_detected || ext_trigger_i) begin
                        state <= PRE_ADV_CAPTURE;
                        capture_start_o <= 1'b1;
                    end
                end
                PRE_ADV_CAPTURE: begin
                    state <= ADV_CAPTURING;
                end
            
                ADV_CAPTURING: begin
                    if (adv_trigger_mode_stop) begin
                        state <= POST_CAPTURE;
                    end               
                end                      
                POST_CAPTURE: begin
                    if (eth_ready_i) begin
                        state <= PRE_UPLOAD;
                        upload_start_o <= 1'b1;
                     end
                end
            
                PRE_UPLOAD: begin
                    state <= UPLOADING;
                end
            
                UPLOADING: begin
                    if (upload_complete) begin
                        state <= POST_UPLOAD;
                    end
                end
            
                POST_UPLOAD: begin
                    if (continuous_mode) begin
                    // 持续模式
                        if (adv_trigger_mode) begin
                            state <= WAIT_ADV_TRIG;
                        end 
                        else begin
                            state <= CONFIG;
                        end
                    end 
                    else if(single_mode)begin
                    // 单次模式
                        state <= IDLE;
                    end
                end
            
            endcase
        end
    end
    
    // ========== 时序逻辑 ==========
 
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            capture_en_o <= 1'b0;
            capture_counter <= 32'h0;
        end 
        else begin   
            // 捕获使能控制
            if ((state == CAPTURING) | (state ==ADV_CAPTURING)) begin
                capture_en_o <= 1'b1;
                if (preprocessed_valid) begin
                    capture_counter <= capture_counter + 1;
                end
            end 
            else begin
                capture_en_o <= 1'b0;
                capture_counter <= 32'h0;
            end           
            // 捕获完成判断
            capture_complete = (capture_counter >= capture_length);
        end
    end
 
  always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin        
            upload_en_o <= 1'b0;
        end 
        else begin           
            // 上传使能控制
            if (state == UPLOADING) begin
                upload_en_o <= 1'b1;
            end else begin
                upload_en_o <= 1'b0;
            end          
        end
    end   
endmodule
