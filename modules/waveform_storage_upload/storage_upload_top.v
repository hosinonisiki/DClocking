`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2026/01/12 15:26:59
// Design Name: 
// Module Name: storage_upload_top
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
//┌─────────────────────────────────────────────────────────────┐
//│                      StorageUploadModule                     │
//├─────────────────────────────────────────────────────────────┤
//│                                                             │
//│
//│   数据预处理   ───→│  触发检测    │───→│  主控制器    │   
//│         ▼                   ▼                   ▼          
//│  │高级触发器    │←───│  内存控制器  │───→│ 以太网传输   │   
//│  │(环形缓冲)   │              

//////////////////////////////////////////////////////////////////////////////////
`timescale 1ns/1ps

module storage_upload_top (
    // 系统时钟与复位
    input  wire        sys_clk,           // 系统时钟 200MHz
    input  wire        sys_clk_125M,
    input  wire        adc_clk,
    input  wire        rst,         // 系统复位
    //寄存器
    input  wire [128:0]core_param_in,    
    // 数据输入接口
    input  wire [15:0] sig_a_buf,        // ADC输入数据
    input  wire [15:0] sig_b_buf,        
    input  wire [15:0] sig_c_buf,
    input  wire [15:0] sig_d_buf,  
    input  wire        adc_data_valid_i,  // ADC数据有效标志 
   // ================= 触发接口 =================
    input  wire         ext_trigger_i,   // 外部触发输入      
    // 内存接口 (DDR4)
    output wire        DDR4_act_n,
    output wire[16:0]  DDR4_adr,
    output wire[1:0]   DDR4_ba,
    output wire[0:0]   DDR4_bg,
    output wire[0:0]   DDR4_ck_c,
    output wire[0:0]   DDR4_ck_t,
    output wire[0:0]   DDR4_cke,
    output wire[0:0]   DDR4_cs_n,
    inout  wire[7:0]   DDR4_dm_n,
    inout  wire[63:0]  DDR4_dq,
    inout  wire[7:0]   DDR4_dqs_c,
    inout  wire[7:0]   DDR4_dqs_t,
    output wire[0:0]   DDR4_odt,
    output wire        DDR4_reset_n,         
   
    
    // 以太网接口 (RGMII)	
    // 发送接口
    output wire        rgmii_txc,
    output wire [3:0]  rgmii_txd,
    output wire        rgmii_tx_ctl,
    // 接收接口 (用于配置和控制)
    input  wire        rgmii_rxc,
    input  wire [3:0]  rgmii_rxd,
    input  wire        rgmii_rx_ctl,
    
    output wire        e_mdc,
    inout  wire        e_mdio,
    output wire        e_reset	
  
);   
    
    // ============================================
    // 内部信号声明
    // ============================================
    //交互 
    wire        eth_ready;
    wire        upload_complete;
    wire [63:0] mem_write_data;
    wire        mem_write_valid;
    wire        capture_start;
    wire[15:0]  BUFFER0_BASE;
    wire[15:0]  BUFFER1_BASE;
    wire[31:0]  sample_len;//采样长度  
   
    oscilloscope(
        // 系统时钟与复位
        .clk                (adc_clk),      
        .rst(rst),        // 系统复位    
        //寄存器
        .core_param_in      (core_param_in),    
        // 数据输入
        .sig_a_buf          (sig_a_buf),
        .sig_b_buf          (sig_b_buf),        
        .sig_c_buf          (sig_c_buf),
        .sig_d_buf          (sig_d_buf),            
        // 外部触发
        .ext_trigger_i      (ext_trigger_i),           
       //交互
        .eth_ready          (eth_ready),
        .upload_complete    (upload_complete), 
        .mem_write_data     (mem_write_data       ),           //FIFO读出皿8bit数据/
        .mem_write_valid    (mem_write_valid      ),          //FIFO中的数据数量
        .capture_start      (capture_start        ),             //FIFO读使胿
        .BUFFER0_BASE       (BUFFER0_BASE    ),
        .BUFFER1_BASE       (BUFFER1_BASE    ),
        .sample_len         (sample_len      )   
   
    );
    
    
    mem_ethernet_top (
       // 系统时钟与复位
        .sys_clk            (sys_clk),
        .sys_clk_125M       (sys_clk_125M),
        .adc_clk            (adc_clk),          // 系统时钟 250MHz
        .rst                (rst),        // 系统复位
          // DDR4物理接口
        .DDR4_act_n         (DDR4_act_n),
        .DDR4_adr           (DDR4_adr),
        .DDR4_ba            (DDR4_ba),
        .DDR4_bg            (DDR4_bg),
        .DDR4_ck_c          (DDR4_ck_c),
        .DDR4_ck_t          (DDR4_ck_t),
        .DDR4_cke           (DDR4_cke),
        .DDR4_cs_n          (DDR4_cs_n),
        .DDR4_dm_n          (DDR4_dm_n),
        .DDR4_dq            (DDR4_dq),
        .DDR4_dqs_c         (DDR4_dqs_c),
        .DDR4_dqs_t         (DDR4_dqs_t),
        .DDR4_odt           (DDR4_odt),
        .DDR4_reset_n       (DDR4_reset_n),   
                
        // 以太网接口 (RGMII)
        .rgmii_txd          (rgmii_txd  ),
        .rgmii_txctl        (rgmii_tx_ctl),
        .rgmii_txc          (rgmii_txc  ),
        .rgmii_rxd          (rgmii_rxd  ),
        .rgmii_rxctl        (rgmii_rx_ctl),
        .rgmii_rxc          (rgmii_rxc  ),       
 
        .e_mdc              (e_mdc      ),
        .e_mdio             (e_mdio     ),
        .e_reset            (e_reset),
      //交互
        .eth_ready          (eth_ready),
        .upload_complete    (upload_complete), 
        .mem_write_data     (mem_write_data       ),           //FIFO读出皿8bit数据/
        .mem_write_valid    (mem_write_valid      ),          //FIFO中的数据数量
        .capture_start      (capture_start        ),             //FIFO读使胿
        .BUFFER0_BASE       (BUFFER0_BASE    ),
        .BUFFER1_BASE       (BUFFER1_BASE    ),
        .sample_len         (sample_len      )   	    	

   

);


    
endmodule   
//    // ============================================
//    // 数据预处理模块
//    // ============================================
//    DataPreprocessor u_data_preprocessor (
//        .clk               (sys_clk_250M),
//        .rst_n             (rst_n),     
//        // 数据输入
//        .data_in           (adc_data_i),
//        .data_valid_i      (adc_data_valid_i),       
//        // 配置
//        .reg_sample_div_i (reg_sample_div_i),  // 降采样倍数       
//        // 数据输出
//        .data_out          (preproc_data),
//        .data_out_valid    (preproc_data_valid)
//    );
   
//   // 触发检测到捕获启动的同步
//reg trigger_latched;
//always @(posedge clk_250m) begin
//    if (trigger_detected && !capture_en)
//        trigger_latched <= 1;
//    else if (capture_start)
//        trigger_latched <= 0;
//end

//assign capture_start = trigger_latched ||  immediate_mode;  // 立即模式 
//    // ============================================
//    // 触发检测模块
//    // ============================================
//    TriggerDetector u_trigger_detector (
//        .clk                  (sys_clk_250M),
//        .rst_n                (rst_n),
        
//        // 数据输入
//        .data_in                (preproc_data),
//        .data_valid_i           (preproc_data_valid),
        
//        // 外部触发
//        .ext_trigger_i          (ext_trigger_i),
//        .capture_start_i        (capture_start),
//        // 配置
////        .trigger_mode_i         (control_reg_i[2:0]),      // 触发模式
//        .trigger_type_i         (reg_trigger_type_i),     // 触发类型
//        .trigger_value_i        (reg_trigger_value_i),    // 触发阈值
//        .sustain_count_i        (reg_sustain_count_i),    // 持续计数
        
//        // 输出
//        .trigger_detected_o     (trigger_detected),
//        .trigger_data_o         (trigger_condition_data),
//        .trigger_data_valid_o   (trig_det_data_valid),
        
//        // 状态
//        .trigger_latched_o      ()
//    );
//    // ============================================
//    // 主控制器状态机
//    // ============================================
//    MainController u_main_controller (
//        .clk              (sys_clk_250M),
//        .rst_n            (rst_n),
        
//        // 控制输入
//        .start_cmd_i      (start_cmd_i),
//        .reg_ctrl_mode_i   (reg_ctrl_mode_i),
//        .reg_capture_len_i (reg_capture_len_i),    
//        .ext_trigger_i      (ext_trigger_i),
//        .reg_operation_mode_i(reg_operation_mode_i),       
//        // 状态输入
//        .preproc_data_valid(preproc_data_valid),        
//        .trigger_detected_i (trigger_detected),
//        .eth_ready_i        (eth_ready),    
        
//        // 控制输出
//        .capture_start_o    (capture_start),
//        .capture_en_o       (capture_en),
//        .upload_start_o     (upload_start),
//        .upload_en_o        (upload_en),
        
//        // 状态输出
//        .fsm_state_o        (fsm_state),
//        .single_mode(single_mode),
//        .continuous_mode(continuous_mode),
//        .immediate_mode(immediate_mode),
//        .normal_trigger_mode(normal_trigger_mode),   
//        .adv_trigger_mode(adv_trigger_mode)     
    
//    );
    
 
    
//    // ============================================
//    // 触发数据选择器 (支持高级触发模式)
//    // ============================================
//    wire [15:0] adv_trigger_data;
//    wire        adv_trigger_valid;
    
//    generate
//        if (adv_trigger_mode) begin : ADV_TRIG_ENABLE
//            // 高级触发模式实例化环形缓冲区
//            AdvancedTriggerHandler u_adv_trigger (
//                .clk                  (sys_clk_250M),
//                .rst_n                (rst_n),
                
//                // 数据输入
//                .data_in                 (preproc_data),
//                .data_valid_i           (preproc_data_valid),
                
//                // 触发信号
//                .trigger_detected              (trigger_detected),
                
//                // 配置
//                .pre_trigger_samples_i          (pre_trigger_samples_i),  // 预触发样本
//                .post_trigger_samples_i         (post_trigger_samples_i), // 后触发样本                            
//                // 数据输出
//                .data_out                 (adv_trigger_data),
//                .data_out_valid           (adv_trigger_valid)           
               
//            );
            
//            assign mem_write_data  = adv_trigger_data;
//            assign mem_write_valid = adv_trigger_valid && capture_en;
            
//        end else if(normal_trigger_mode) begin : NORMAL_MODE
//            // 普通模式直接使用预处理数据
//            assign mem_write_data  = preproc_data;
//            assign mem_write_valid = preproc_data_valid && capture_en;
//        end
//    endgenerate
    
// wire gmii_tx_clk;
    
// wire [15:0] read_usedw;
//   // ============================================
//    // 内存控制器 (双缓冲架构)
//    // ============================================
//  Memctrl_top u_memory_controller (
//     // 系统时钟与复位
//    .sys_clk(sys_clk),
//    .adc_clk (adc_clk),          // 系统时钟 250MHz
//    .gmii_tx_clk(gmii_tx_clk),
//    .rst_n(rst_n),        // 系统复位
//    //寄存器
//    .BUFFER0_BASE(BUFFER0_BASE),
//    .BUFFER1_BASE(BUFFER1_BASE),
//    .sample_len (sample_len),//采样长度   
//     // 用户控制接口
//    .capture_start(capture_start),    // 捕获开始
//    .capture_en(capture_en),   // 捕获使能
//    .upload_start(upload_start),     // 上传开始
//    .upload_en(upload_en),    // 上传使能
    
//    // 数据输入接口（16位采样数据）
//    .write_data_i(mem_write_data),       // 写入数据
//    .write_valid_i(mem_write_valid),      // 数据有效
    
//    // 数据输出接口（64位读取数据）
//    .read_data(fifo_read_data       ),           //FIFO读出皿8bit数据/
//    .read_en(fifo_read_en),            //FIFO读使能 
//    .read_usedw(read_usedw      ),          //FIFO中的数据数量
//    .read_req_ack(read_req_ack    ),
//    .read_req(read_req        ),
//    .ad_sample_ack(ad_sample_ack   ),   
  
//         // DDR4物理接口
//    .DDR4_act_n(DDR4_act_n),
//    .DDR4_adr(DDR4_adr),
//    .DDR4_ba(DDR4_ba),
//    .DDR4_bg(DDR4_bg),
//    .DDR4_ck_c(DDR4_ck_c),
//    .DDR4_ck_t(DDR4_ck_t),
//    .DDR4_cke(DDR4_cke),
//    .DDR4_cs_n(DDR4_cs_n),
//    .DDR4_dm_n(DDR4_dm_n),
//    .DDR4_dq(DDR4_dq),
//    .DDR4_dqs_c(DDR4_dqs_c),
//    .DDR4_dqs_t(DDR4_dqs_t),
//    .DDR4_odt(DDR4_odt),
//    .DDR4_reset_n(DDR4_reset_n),  
//    .ui_clk(ui_clk),
//    .ui_rst(ui_rst),
//    .buffer_full_o      (buffer_full),
//    .error_o            (mem_error),
//    .buffer_error_i     (buffer_error)
//    );
  
  
//    // ============================================
//    // 以太网传输模块
//    // ============================================
  
//   ethernet_test eth1
// (
//  .rst_n         (rst_n      ),
//  .sys_clk 	     (sys_clk_125M 	  ),
//     // 数据输入接口                         
//        // 数据输入接口
////        .data_i             (mem_read_data[15:0]),  // 使用低16位
////        .data_valid_i       (mem_read_valid && upload_en),
////        .data_ack_o         (eth_data_ack),

//  .fifo_data              (fifo_read_data       ),           //FIFO读出皿8bit数据/
//  .fifo_data_count         (read_usedw      ),          //FIFO中的数据数量
//  .fifo_rd_en              (fifo_read_en         ),             //FIFO读使胿
  
//  .read_req_ack            (read_req_ack    ),
//  .read_req                (read_req        ),
//  .ad_sample_req           (capture_start_i   ),
//  .ad_sample_ack           (ad_sample_ack   ),
//  .sample_len              (sample_len      ),    
     
//  .e_mdc         (e_mdc      ),
//  .e_mdio        (e_mdio     ),
//  .rgmii_txd     (rgmii_txd  ),
//  .rgmii_txctl   (rgmii_tx_ctl),
//  .rgmii_txc     (rgmii_txc  ),
//  .rgmii_rxd     (rgmii_rxd  ),
//  .rgmii_rxctl   (rgmii_rx_ctl),
//  .rgmii_rxc     (rgmii_rxc  ),
//   .led 	         ( 	  ),
//   .ready_o            (eth_ready),
//   .error_o            (eth_error)
// );
     
  


//    mem_ethernet_top u_mem_ethernet_top (
//        // 时钟与复位
//        .clk         (sys_clk_250M),
//        .mem_clk_i    (sys_clk),
//        .ether_clk    (),
//        .rst_n            (rst),
        
//        // 写入接口
//        .write_data_i       (mem_write_data),
//        .write_valid_i      (mem_write_valid),
////        .write_start_i      (capture_start),
////        .write_enable_i     (capture_en),
////        .write_length_i     (write_length_i),  // 捕获长度指数
//        .capture_start_i (capture_start),    // 捕获开始
//        .capture_en_i (capture_en),   // 捕获使能
//        .upload_start_i(upload_start),     // 上传开始
//        .upload_en_i(upload_en),    // 上传使能      
//        // 读取接口 (用于上传)
//        .read_ready_i       (upload_en && eth_ready),
//        .read_data_o        (mem_read_data),
//        .read_valid_o       (mem_read_valid),
//        .read_ack_i         (eth_data_ack),
        
//         // DDR4物理接口
//        .DDR4_act_n(DDR4_act_n),
//        .DDR4_adr(DDR4_adr),
//        .DDR4_ba(DDR4_ba),
//        .DDR4_bg(DDR4_bg),
//        .DDR4_ck_c(DDR4_ck_c),
//        .DDR4_ck_t(DDR4_ck_t),
//        .DDR4_cke(DDR4_cke),
//        .DDR4_cs_n(DDR4_cs_n),
//        .DDR4_dm_n(DDR4_dm_n),
//        .DDR4_dq(DDR4_dq),
//        .DDR4_dqs_c(DDR4_dqs_c),
//        .DDR4_dqs_t(DDR4_dqs_t),
//        .DDR4_odt(DDR4_odt),
//        .DDR4_reset_n(DDR4_reset_n),  
        
//        // 状态输出
//        .buffer_full_o      (buffer_full),
//        .buffer_empty_o     (buffer_empty),
//        .active_buffer_o    (active_buffer),
//        .write_counter_o    (write_counter),
//        .read_counter_o     (read_counter),
        
//        // 错误输出
//        .error_o            (mem_error),
//        .error_code_o       (), 
        
//        // 数据输入接口
//        .data_i             (mem_read_data[15:0]),  // 使用低16位
//        .data_valid_i       (mem_read_valid && upload_en),
//        .data_ack_o         (eth_data_ack),
//        .ready_o            (eth_ready),
        
//        // 配置接口
//        .src_mac_i          (48'h00_11_22_33_44_55),  // 源MAC地址
//        .dst_mac_i          (48'hFF_FF_FF_FF_FF_FF),  // 广播地址
//        .src_ip_i           (32'hC0A80101),          // 192.168.1.1
//        .dst_ip_i           (control_reg_i[31:0]),   // 目标IP
//        .src_port_i         (16'h1F90),              // 8080
//        .dst_port_i         (control_reg_i[15:0]),   // 目标端口
//        .packet_length_i    ({control_reg_i[30:27], 4'b0}), // 包长度
        
//        // RGMII物理接口
//        .rgmii_txc_o        (rgmii_txc),
//        .rgmii_txd_o        (rgmii_txd),
//        .rgmii_tx_ctl_o     (rgmii_tx_ctl),
        
//        // 状态输出
//        .tx_busy_o          (),
//        .tx_done_o          (),
//        .byte_count_o       (),
        
//        // 错误输出
//        .error_o            (eth_error),
//        .error_code_o       ()
//    );