`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2026/01/05 17:06:25
// Design Name: 
// Module Name: Memctrl_top
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


module Memctrl_top(
   // 系统时钟与复位
    input  wire        sys_clk,
    input  wire        adc_clk,          // 系统时钟 250MHz
    input  wire        gmii_tx_clk,
    input  wire        rst,        // 系统复位
    //寄存器
    input  wire[15:0]  BUFFER0_BASE,
    input  wire[15:0]  BUFFER1_BASE,
    input  wire[31:0]  sample_len,//采样长度   
     // 用户控制接口
    input  wire        capture_start,    // 捕获开始
//    input  wire        capture_en,   // 捕获使能
//    input  wire        upload_start,     // 上传开始
//    input  wire        upload_en,    // 上传使能
    output             write_en,
    // 数据输入接口（16位采样数据）
    input  wire [63:0] write_data_i,       // 写入数据
    input  wire        write_valid_i,      // 数据有效
    // 数据输出接口（64位读取数据）
    output wire[15:0]  read_data,        // 读取数据
    input  wire        read_en,            //FIFO读使能 
//    output wire        read_valid_o,       // 数据有效
//    input  wire        read_ready_i,       // 读取准备好 
    output wire [15:0] read_usedw,       //FIFO数据可读量    
    output wire        read_req_ack,//读ADC采集数据应答
    input  wire        read_req,//读ADC数据请求
    output wire        ad_sample_ack,//ADC采样应答
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
    output wire        ui_clk,
    output wire        ui_rst
  

    );
    parameter MEM_DATA_BITS          = 64;             //external memory user interface data width
    parameter ADDR_BITS              = 29;             //external memory user interface address width
    parameter BUSRT_BITS             = 10;             //external memory user interface burst width
    
    
    wire                            write_en;
    wire[63:0]                      write_data;
    wire                            write_req;
    wire                            write_req_ack;
    
    wire                            rd_burst_req;
    wire[BUSRT_BITS - 1:0]          rd_burst_len;
    wire[ADDR_BITS - 1:0]           rd_burst_addr;
    wire                            rd_burst_data_valid;
    wire[MEM_DATA_BITS - 1 : 0]     rd_burst_data;
    wire                            rd_burst_finish;
    wire                            wr_burst_req;
    wire[BUSRT_BITS - 1:0]          wr_burst_len;
    wire[ADDR_BITS - 1:0]           wr_burst_addr;
    wire                            wr_burst_data_req;
    wire[MEM_DATA_BITS - 1 : 0]     wr_burst_data;
    wire                            wr_burst_finish;
    
    // Master Write Address
    wire [0:0]                      s00_axi_awid;
    wire [31:0]                     s00_axi_awaddr;
    wire [7:0]                      s00_axi_awlen;    // burst length: 0-255
    wire [2:0]                      s00_axi_awsize;   // burst size: fixed 2'b011
    wire [1:0]                      s00_axi_awburst;  // burst type: fixed 2'b01(incremental burst)
    wire                            s00_axi_awlock;   // lock: fixed 2'b00
    wire [3:0]                      s00_axi_awcache;  // cache: fiex 2'b0011
    wire [2:0]                      s00_axi_awprot;   // protect: fixed 2'b000
    wire [3:0]                      s00_axi_awqos;    // qos: fixed 2'b0000
    wire [0:0]                      s00_axi_awuser;   // user: fixed 32'd0
    wire                            s00_axi_awvalid;
    wire                            s00_axi_awready;
    // master write data
    wire [63:0]                     s00_axi_wdata;
    wire [7:0]                      s00_axi_wstrb;
    wire                            s00_axi_wlast;
    wire [0:0]                      s00_axi_wuser;
    wire                            s00_axi_wvalid;
    wire                            s00_axi_wready;
    // master write response
    wire [3:0]                      s00_axi_bid;
    wire [1:0]                      s00_axi_bresp;
    wire [0:0]                      s00_axi_buser;
    wire                            s00_axi_bvalid;
    wire                            s00_axi_bready;
    // master read address
    wire [0:0]                      s00_axi_arid;
    wire [31:0]                     s00_axi_araddr;
    wire [7:0]                      s00_axi_arlen;
    wire [2:0]                      s00_axi_arsize;
    wire [1:0]                      s00_axi_arburst;
    wire [1:0]                      s00_axi_arlock;
    wire [3:0]                      s00_axi_arcache;
    wire [2:0]                      s00_axi_arprot;
    wire [3:0]                      s00_axi_arqos;
    wire [0:0]                      s00_axi_aruser;
    wire                            s00_axi_arvalid;
    wire                            s00_axi_arready;
    // master read data
    wire [3:0]                      s00_axi_rid;
    wire [63:0]                     s00_axi_rdata;
    wire [1:0]                      s00_axi_rresp;
    wire                            s00_axi_rlast;
    wire [0:0]                      s00_axi_ruser;
    wire                            s00_axi_rvalid;
    wire                            s00_axi_rready;
    
    adc_sample adc_sample_m0 (
        .clk                (adc_clk        ),
        .rst                (rst            ),
        .adc_data           (write_data_i   ),
        .adc_valid_i        (write_valid_i  ),
        .adc_buf_wr         (write_en       ),
        .adc_buf_data       (write_data     ),
        .sample_len         (sample_len     ),
        .ad_sample_req      (capture_start  ),
        .ad_sample_ack      (ad_sample_ack  ),
        .write_req          (write_req      ),
        .write_req_ack      (write_req_ack  )
    );
    //video frame data read-write control
    frame_read_write frame_read_write_m0(
	    .rst                (rst                      ),
	    .mem_clk            (sys_clk                   ),
	    .rd_burst_req       (rd_burst_req             ),
	    .rd_burst_len       (rd_burst_len             ),
	    .rd_burst_addr      (rd_burst_addr            ),
	    .rd_burst_data_valid(rd_burst_data_valid      ),
	    .rd_burst_data      (rd_burst_data            ),
	    .rd_burst_finish    (rd_burst_finish          ),
	    .read_clk           (gmii_tx_clk              ),
	    .read_req           (read_req                 ),
	    .read_req_ack       (read_req_ack             ),
	    .read_finish        (                         ),
//	    .read_addr_0        (24'd0                    ), //The first frame address is 0
//	    .read_addr_1        (24'd2073600              ), //The second frame address is 24'd2073600 ,large enough address space for one frame of video
//	    .read_addr_2        (24'd4147200              ),
//	    .read_addr_3        (24'd6220800              ),
//	    .read_addr_index    (2'd0                     ),
	    .read_len           (sample_len               ),//frame size 
	    .read_en            (read_en                  ),
	    .read_data          (read_data                ),
        .read_usedw         (read_usedw               ),
       
	    .wr_burst_req       (wr_burst_req             ),
	    .wr_burst_len       (wr_burst_len             ),
	    .wr_burst_addr      (wr_burst_addr            ),
	    .wr_burst_data_req  (wr_burst_data_req        ),
	    .wr_burst_data      (wr_burst_data            ),
	    .wr_burst_finish    (wr_burst_finish          ),
	    .write_clk          (adc_clk                  ),
	    .write_req          (write_req                ),
	    .write_req_ack      (write_req_ack            ),
	    .write_finish       (                         ),
//	    .write_addr_0       (24'd0                    ),
//	    .write_addr_1       (24'd2073600              ),
//	    .write_addr_2       (24'd4147200              ),
//	    .write_addr_3       (24'd6220800              ),
//	    .write_addr_index   (2'd0                     ),
	    .write_len          (sample_len             ), //frame size  
	    .write_en           (write_en & write_valid_i ),
	    .write_data         (write_data               )
    );    


    aq_axi_master u_aq_axi_master(
	    .ARESETN            (~rst             ),
	    .ACLK               (sys_clk              ),
	    .M_AXI_AWID         (s00_axi_awid        ),
	    .M_AXI_AWADDR       (s00_axi_awaddr      ),
	    .M_AXI_AWLEN        (s00_axi_awlen       ),
	    .M_AXI_AWSIZE       (s00_axi_awsize      ),
	    .M_AXI_AWBURST      (s00_axi_awburst     ),
	    .M_AXI_AWLOCK       (s00_axi_awlock      ),
	    .M_AXI_AWCACHE      (s00_axi_awcache     ),
	    .M_AXI_AWPROT       (s00_axi_awprot      ),
	    .M_AXI_AWQOS        (s00_axi_awqos       ),
	    .M_AXI_AWUSER       (s00_axi_awuser      ),
	    .M_AXI_AWVALID      (s00_axi_awvalid     ),
	    .M_AXI_AWREADY      (s00_axi_awready     ),
	    .M_AXI_WDATA        (s00_axi_wdata       ),
	    .M_AXI_WSTRB        (s00_axi_wstrb       ),
	    .M_AXI_WLAST        (s00_axi_wlast       ),
	    .M_AXI_WUSER        (s00_axi_wuser       ),
	    .M_AXI_WVALID       (s00_axi_wvalid      ),
	    .M_AXI_WREADY       (s00_axi_wready      ),
	    .M_AXI_BID          (s00_axi_bid         ),
	    .M_AXI_BRESP        (s00_axi_bresp       ),
	    .M_AXI_BUSER        (s00_axi_buser       ),
	    .M_AXI_BVALID       (s00_axi_bvalid      ),
	    .M_AXI_BREADY       (s00_axi_bready      ),
	    .M_AXI_ARID         (s00_axi_arid        ),
	    .M_AXI_ARADDR       (s00_axi_araddr      ),
	    .M_AXI_ARLEN        (s00_axi_arlen       ),
	    .M_AXI_ARSIZE       (s00_axi_arsize      ),
	    .M_AXI_ARBURST      (s00_axi_arburst     ),
	    .M_AXI_ARLOCK       (s00_axi_arlock      ),
	    .M_AXI_ARCACHE      (s00_axi_arcache     ),
	    .M_AXI_ARPROT       (s00_axi_arprot      ),
	    .M_AXI_ARQOS        (s00_axi_arqos       ),
	    .M_AXI_ARUSER       (s00_axi_aruser      ),
	    .M_AXI_ARVALID      (s00_axi_arvalid     ),
	    .M_AXI_ARREADY      (s00_axi_arready     ),
	    .M_AXI_RID          (s00_axi_rid         ),
	    .M_AXI_RDATA        (s00_axi_rdata       ),
	    .M_AXI_RRESP        (s00_axi_rresp       ),
	    .M_AXI_RLAST        (s00_axi_rlast       ),
	    .M_AXI_RUSER        (s00_axi_ruser       ),
	    .M_AXI_RVALID       (s00_axi_rvalid      ),
	    .M_AXI_RREADY       (s00_axi_rready      ),
	    .MASTER_RST         (1'b0                ),
	    .WR_START           (wr_burst_req        ),
	    .WR_ADRS            ({wr_burst_addr,3'd0}),
	    .WR_LEN             ({19'd0,wr_burst_len,3'd0} ),
	    .WR_READY           (                    ),
	    .WR_FIFO_RE         (wr_burst_data_req   ),
	    .WR_FIFO_EMPTY      (1'b0                ),
	    .WR_FIFO_AEMPTY     (1'b0                ),
	    .WR_FIFO_DATA       (wr_burst_data       ),
	    .WR_DONE            (wr_burst_finish     ),
	    .RD_START           (rd_burst_req        ),
	    .RD_ADRS            ({rd_burst_addr,3'd0}),
	    .RD_LEN             ({19'd0,rd_burst_len,3'd0} ),
	    .RD_READY           (                    ),
	    .RD_FIFO_WE         (rd_burst_data_valid ),
	    .RD_FIFO_FULL       (1'b0                ),
	    .RD_FIFO_AFULL      (1'b0                ),
	    .RD_FIFO_DATA       (rd_burst_data       ),
	    .RD_DONE            (rd_burst_finish     ),
	    .DEBUG              (                    )
    );

//  // ============================================
//    // DDR4控制器包装模块
//    // ============================================
//    // 实际的DDR4控制器实例
    DDR4ControllerWrapper u_ddr4_controller (
        // 系统接口
        .sys_clk_i          (sys_clk),
        .sys_rst            (rst    ),  
     // DDR4物理接口
        .c0_ddr4_act_n      (DDR4_act_n),
        .c0_ddr4_adr        (DDR4_adr),
        .c0_ddr4_ba         (DDR4_ba),
        .c0_ddr4_bg         (DDR4_bg),
        .c0_ddr4_ck_c       (DDR4_ck_c),
        .c0_ddr4_ck_t       (DDR4_ck_t),
        .c0_ddr4_cke        (DDR4_cke),
        .c0_ddr4_cs_n       (DDR4_cs_n),
        .c0_ddr4_dm_dbi_n   (DDR4_dm_n),
        .c0_ddr4_dq         (DDR4_dq),
        .c0_ddr4_dqs_c      (DDR4_dqs_c),
        .c0_ddr4_dqs_t      (DDR4_dqs_t),
        .c0_ddr4_odt        (DDR4_odt),
        .c0_ddr4_reset_n    (DDR4_reset_n),         
   // AXI从接口
   // Slave Interface Write Address Ports
         .c0_ddr4_aresetn       (rst ),
         .c0_ddr4_s_axi_awaddr  (s00_axi_awaddr),
         .c0_ddr4_s_axi_awlen   (s00_axi_awlen),
         .c0_ddr4_s_axi_awsize  (s00_axi_awsize),
         .c0_ddr4_s_axi_awburst (s00_axi_awburst),
         .c0_ddr4_s_axi_awlock  (s00_axi_awlock),
         .c0_ddr4_s_axi_awcache (s00_axi_awcache),
         .c0_ddr4_s_axi_awprot  (s00_axi_awprot),
         .c0_ddr4_s_axi_awqos   (s00_axi_awqos),
         .c0_ddr4_s_axi_awvalid (s00_axi_awvalid),
         .c0_ddr4_s_axi_awready (s00_axi_awready),
   // Slave Interface Write Data Ports
         .c0_ddr4_s_axi_wdata   (s00_axi_wdata),
         .c0_ddr4_s_axi_wstrb   (s00_axi_wstrb),
         .c0_ddr4_s_axi_wlast   (s00_axi_wlast),
         .c0_ddr4_s_axi_wvalid  (s00_axi_wvalid),
         .c0_ddr4_s_axi_wready  (s00_axi_wready),
   // Slave Interface Write Response Ports
         .c0_ddr4_s_axi_bready  (s00_axi_bready),
         .c0_ddr4_s_axi_bid     (s00_axi_bid),
         .c0_ddr4_s_axi_bresp   (s00_axi_bresp),
         .c0_ddr4_s_axi_bvalid  (s00_axi_bvalid),
   // Slave Interface Read Address Ports
         .c0_ddr4_s_axi_arid    (s00_axi_arid),
         .c0_ddr4_s_axi_araddr  (s00_axi_araddr),
         .c0_ddr4_s_axi_arlen   (s00_axi_arlen),
         .c0_ddr4_s_axi_arsize  (s00_axi_arsize),
         .c0_ddr4_s_axi_arburst (s00_axi_arburst),
         .c0_ddr4_s_axi_arlock  (s00_axi_arlock),
         .c0_ddr4_s_axi_arcache (s00_axi_arcache),
         .c0_ddr4_s_axi_arprot  (s00_axi_arprot),
         .c0_ddr4_s_axi_arqos   (s00_axi_arqos),
         .c0_ddr4_s_axi_arvalid (s00_axi_arvalid),
         .c0_ddr4_s_axi_arready (s00_axi_arready),
   // Slave Interface Read Data Ports
         .c0_ddr4_s_axi_rready  (s00_axi_rready),
         .c0_ddr4_s_axi_rid     (s00_axi_rid),
         .c0_ddr4_s_axi_rdata   (s00_axi_rdata),
         .c0_ddr4_s_axi_rresp   (s00_axi_rresp),
         .c0_ddr4_s_axi_rlast   (s00_axi_rlast),
         .c0_ddr4_s_axi_rvalid  (s00_axi_rvalid),                  

         .c0_ddr4_ui_clk        (ui_clk),
         .c0_ddr4_ui_clk_sync_rst(ui_rst)
    );
   

endmodule
