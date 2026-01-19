`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2026/01/07 15:38:05
// Design Name: 
// Module Name: oscilloscope
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


module oscilloscope(
     // 系统时钟与复位
    input  wire        clk,           // adc数据时钟
    input  wire        rst,         // 系统复位
    //寄存器
    input  wire [511:0] core_param_in,    
    // 数据输入接口
    input  wire [15:0]  sig_a_buf,        // ADC输入数据
    input  wire [15:0]  sig_b_buf,        
    input  wire [15:0]  sig_c_buf,
    input  wire [15:0]  sig_d_buf,  
   
  // ================= 触发接口 =================
    input  wire         ext_trigger_i,   // 外部触发输入
    
   //交互 
    input  wire        eth_ready,
    input  wire        upload_complete,
    output wire [63:0] mem_write_data,
    output wire        mem_write_valid,
    output wire        capture_start,
    output wire[15:0]  BUFFER0_BASE,
    output wire[15:0]  BUFFER1_BASE,
    output wire[31:0]  sample_len//采样长度  
//    // 状态指示
//    output wire [3:0]  status_led_o,      // 状态指示灯
//    output wire [7:0]  debug_o            // 调试输出  
    );
  // ============================================
    // 内部信号声明
    // ============================================
  
    
    // 数据流信号
    wire [63:0] preprocessed_data;
    wire        preprocessed_valid;
      
//    wire [15:0] mem_write_data;
//    wire        mem_write_valid;
     
    // 触发信号
    wire        trigger_detected;
    wire [15:0] trigger_condition_data;
    wire        trig_det_data_valid;  
   
    // 控制信号
    wire        capture_start;
    wire        capture_en;
    wire        upload_start;
    wire        upload_en;
  
    wire        single_mode;
    wire        continuous_mode;
    reg        immediate_mode;
    reg        normal_trigger_mode;   
    reg        adv_trigger_mode ;
  
    
    // 状态信号
    wire [3:0]  fsm_state;
    wire        buffer_full;
    wire        buffer_empty;
    wire [31:0] capture_counter;
    
    // 错误信号
    wire        mem_error;
    wire        eth_error;
    wire        buffer_error;
    wire [7:0]  error_code;
    assign rst_n = ~ rst;

 // 控制与触发接口
   wire        start_cmd;// 开始指令
   wire        reg_operation_mode;// 0-单次模式,1-持续模式  
   wire [2:0]  reg_trigger_mode;// 000-立即模式,001-一般触发,010-高级触发
   wire [3:0]  reg_trigger_type;// 触发类型
   wire [1:0]  trigger_channel;     // 00=CH1,01=CH2,10=CH3,11=CH4
   wire [3:0]  upload_channels;    //  上传通道选择 (位图)bit0=CH1,bit1=CH2,bit2=CH3,bit3=CH4     
   wire [15:0] reg_downsample_ratio;// 降采样倍数
   wire [15:0] reg_trigger_value;// 触发阈值（16位）
   wire [15:0] reg_sustain_count;// 持续计数
   wire [15:0] reg_capture_len;// 捕获长度（0-15，实际长度=2^N）
//   wire [15:0]  pre_trigger_points;
//   wire [15:0]  post_trigger_points;
   wire [15:0] BUFFER0_BASE;
   wire [15:0] BUFFER1_BASE;      

  


   
   // 0x00
   assign start_cmd = core_param_in[0];// [50] 开始指令
   // 0x01
   assign reg_operation_mode = core_param_in[32];// 0-单次模式,1-持续模式 
   // 0x02
   assign reg_trigger_mode = core_param_in[66:64];// 000-立即模式,001-一般触发,010-高级触发
   // 0x03
   assign reg_trigger_type = core_param_in[99:96];// 触发类型
   // 0x04
   assign trigger_channel = core_param_in[129:128];     // 00=CH1,01=CH2,10=CH3,11=adc_clk   
   // 0x05
   assign upload_channels = core_param_in[163:160];     // 上传通道选择 (位图) bit0=CH1,bit1=CH2,bit2=CH3,bit3=CH4   
   // 0x06  
   assign reg_downsample_ratio = core_param_in[208:192];// 降采样倍数
   // 0x07
   assign reg_trigger_value = core_param_in[239:224];// 触发阈值（16位）
   // 0x08
   assign reg_sustain_count = core_param_in[271:256];// 持续计数
   // 0x09
   assign reg_capture_len = core_param_in[303:288];// 捕获长度（0-15，实际长度=2^N）
   // 0x0A
   assign BUFFER0_BASE = core_param_in[335:320];
   // 0x0B
   assign BUFFER1_BASE = core_param_in[367:352];      
  
 
   

    // ========== 组合逻辑 ==========
  // 操作模式
    assign single_mode = ~reg_operation_mode;
    assign continuous_mode = reg_operation_mode;
   // 解析控制寄存器
//    assign immediate_mode = (reg_trigger_mode == 3'b000);
//    assign normal_trigger_mode = (reg_trigger_mode == 3'b001);
//    assign adv_trigger_mode = (reg_trigger_mode == 3'b010);
  always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            immediate_mode <= 1'b0;
            normal_trigger_mode  <= 1'b0;
            adv_trigger_mode  <= 1'b0;
        end
        else begin
            if(reg_trigger_mode == 3'b000)begin
                immediate_mode <= 1'b1;
                normal_trigger_mode  <= 1'b0;
                adv_trigger_mode  <= 1'b0;
            end
            else if(reg_trigger_mode == 3'b001)begin
                immediate_mode <= 1'b0;
                normal_trigger_mode  <= 1'b1;
                adv_trigger_mode  <= 1'b0;
            end 
            else if(reg_trigger_mode == 3'b010)begin
                immediate_mode <= 1'b0;
                normal_trigger_mode  <= 1'b0;
                adv_trigger_mode  <= 1'b1;
            end
            else begin
                immediate_mode <= 1'b1;
                normal_trigger_mode  <= 1'b0;
                adv_trigger_mode  <= 1'b0;
            end    
        end
    end
    reg [1:0] adv_trigger_mode_dly;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            adv_trigger_mode_dly <= 2'b00; 
        end
        else begin
            adv_trigger_mode_dly <= {adv_trigger_mode_dly[0],adv_trigger_mode};
        end
    end         
   assign adv_trigger_mode_stop =  (~adv_trigger_mode_dly[0]) & (adv_trigger_mode_dly[1] );       
    // ============================================
    // 数据预处理模块
    // ============================================
    DataPreprocessor u_data_preprocessor (
        .clk                (clk),
        .rst_n              (rst_n),     
        // 数据输入
        .sig_a_buf          (sig_a_buf),
        .sig_b_buf          (sig_b_buf),        
        .sig_c_buf          (sig_c_buf),
        .sig_d_buf          (sig_d_buf),            
        // 配置
        .reg_downsample_ratio(reg_downsample_ratio),  // 降采样倍数 
        .upload_channels    (upload_channels),      
        // 数据输出
        .preprocessed_data   (preprocessed_data),
        .preprocessed_valid  (preprocessed_valid)

    );
  
    // ============================================
    // 触发检测模块
    // ============================================
    
    ChannelTriggerDetector u_ChannelTriggerDetector (
        .clk                (clk),
        .rst_n              (rst_n),       
        // 数据输入
        .sig_a_buf          (preprocessed_data[15:0]),
        .sig_b_buf          (preprocessed_data[31:16]),        
        .sig_c_buf          (preprocessed_data[47:32]),
        .sig_d_buf          (preprocessed_data[63:48]),       
        .data_valid_i       (preprocessed_valid),
        
        // 外部触发
        .ext_trigger_i      (ext_trigger_i),
        .capture_start_i    (capture_start),
        // 配置
        .trigger_channel    (trigger_channel),      // 触发通道选择
        .reg_trigger_type   (reg_trigger_type),     // 触发类型
        .reg_trigger_value  (reg_trigger_value),    // 触发阈值
        .reg_sustain_count  (reg_sustain_count),    // 持续计数     
        // 输出
        .trigger_detected_o (trigger_detected),
        .trigger_data_o     (trigger_condition_data),
        .trigger_data_valid_o(trig_det_data_valid) 
        
    );
    // ============================================
    // 主控制器状态机
    // ============================================
    MainController u_main_controller (
        .clk                (clk),
        .rst_n              (rst_n),     
        // 控制输入
        .start_cmd          (start_cmd),
//        .reg_trigger_mode   (reg_trigger_mode),
        .reg_capture_len    (reg_capture_len),    
        .ext_trigger_i      (ext_trigger_i),
//        .reg_operation_mode(reg_operation_mode), 
        .single_mode        (single_mode),
        .continuous_mode    (continuous_mode),
        .immediate_mode     (immediate_mode),
        .normal_trigger_mode(normal_trigger_mode),   
        .adv_trigger_mode   (adv_trigger_mode),
        .adv_trigger_mode_stop (adv_trigger_mode_stop),           
        // 状态输入
        .preprocessed_valid (preprocessed_valid),        
        .trigger_detected   (trigger_detected),
        .eth_ready_i        (eth_ready),    
        .upload_complete    (upload_complete),
        // 控制输出
        .capture_start_o    (capture_start),
        .capture_en_o       (capture_en),
        .upload_start_o     (upload_start),
        .upload_en_o        (upload_en),
        .capture_counter    (capture_counter),
        // 状态输出
        .fsm_state_o        (fsm_state)
 
    
    );
    
 
    
    // ============================================
    // 触发数据选择器 (支持高级触发模式)
    // ============================================
    wire [63:0] adv_trigger_data;
    wire        adv_trigger_valid;
             // 高级触发模式实例化环形缓冲区
            AdvancedTriggerHandler u_adv_trigger (
                .clk                (clk),
                .rst_n              (rst_n),
         // 数据输入                                
                .sig_a_buf          (preprocessed_data[15:0]),                 
                .sig_b_buf          (preprocessed_data[31:16]),                 
                .sig_c_buf          (preprocessed_data[47:32]),                 
                .sig_d_buf          (preprocessed_data[63:48]),                 
                .data_valid_i       (preprocessed_valid),
                
                // 触发信号
                .trigger_detected   (trigger_detected),
                .adv_trigger_mode   (adv_trigger_mode),
                .adv_trigger_mode_stop (adv_trigger_mode_stop),
                // 配置
                .upload_channels    (upload_channels),
                .pre_trigger_points (reg_capture_len),  // 预触发样本
//                .post_trigger_points(post_trigger_points), // 后触发样本                            
                // 数据输出
                .data_out           (adv_trigger_data),
                .data_out_valid     (adv_trigger_valid),
                .adv_data_num       (adv_data_num )           
               
            );  
     assign mem_write_data  = adv_trigger_mode ? adv_trigger_data : preprocessed_data;
     assign mem_write_valid = adv_trigger_mode ? adv_trigger_valid && capture_en : preprocessed_valid && capture_en;
     assign sample_len = adv_trigger_mode ? adv_data_num : capture_counter;
//    // ============================================
//    // 调试与状态输出
//    // ============================================
//    assign status_led_o = fsm_state;  // 状态机状态显示
    
//    // 调试信号输出
//    assign debug_o = {
//        preproc_data_valid,    // bit 7
//        trigger_detected,      // bit 6
//        capture_en,        // bit 5
//        upload_en,         // bit 4
//        buffer_full,           // bit 3
//        eth_ready,             // bit 2
//        error_o,               // bit 1
//        pll_locked             // bit 0
//    };
   
    
       
endmodule
