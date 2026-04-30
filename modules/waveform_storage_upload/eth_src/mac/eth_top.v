module eth_top(
    input                  rst_n  ,        
    input  [15:0]          fifo_data,             //FIFO数据
    input  [11:0]          fifo_data_count,       //FIFO数据可读量
    output                 fifo_rd_en,            //FIFO读使能         
    
    input                  read_req_ack,//读ADC采集数据应答
    output                 read_req,//读ADC数据请求
    output                 ad_sample_req,//ADC采样请求
    input                  ad_sample_ack,//ADC采样应答
    output [31:0]          sample_len,//采样长度
    
    input                  gmii_tx_clk ,//GMii发送时钟
    input                  gmii_rx_clk ,//接收时钟
    input                  gmii_rx_dv,//接收有效
    input  [7:0]           gmii_rxd,//接收数据
    output reg             gmii_tx_en,//发送使能
    output reg [7:0]       gmii_txd//发送数据       
    ) ;
       
    parameter  LOCAL_IP_ADDR    = 32'hc0a80002     ;//本地IP地址
    parameter  LOCAL_MAC_ADDR   = 48'h000a3501fec0 ;//本地MAC地址
    parameter  UDP_SRC_PORT     = 16'h1f90         ;//源端口号
    parameter  UDP_DST_PORT     = 16'h1f90         ;//目的端口号
    parameter  TTL              = 8'h80            ;//生存时间
    
    
    wire [31:0]           ip_rec_source_ip_addr    ;//ip接收IP地址
    wire [15:0]           udp_send_data_length     ;//udp发送数据长度
    wire [31:0]           destination_ip_addr      ;//目的IP地址
    wire [7:0]            udp_data                 ;//UDP数据
    wire                  udp_tx_req               ;//UDP发送请求
    wire                  arp_request_req          ;//ARP 请求的请求信号
    wire                  mac_send_end             ;//mac发送结束
    wire [7:0]            udp_rec_ram_rdata        ;//udp接收RAM数据
    wire [10:0]           udp_rec_ram_read_addr    ;//udp接收RAM地址
    wire [15:0]           udp_rec_data_length      ;//udp数据长度
    wire                  udp_rec_data_valid       ;//udp接收数据有效
    wire                  mac_not_exist            ;//mac不存在
    wire                  arp_found                ;//接收到mac
    
    wire [7:0]            reply_data               ;//回复命令
    wire [31:0]           sample_num               ;//采样数量
    wire                  cmd_reply_ack            ;//命令应答响应
    wire                  cmd_reply_req            ;     //cmd reply request
    wire [15:0]           cmd_send_len             ;       //cmd reply length
    wire                  ad_data_ack              ;//ADC应答
    wire                  ad_data_req              ;       //ad data request
                                                   
    reg                   gmii_rx_dv_d0            ;//GMII接收有效
    reg  [7:0]            gmii_rxd_d0              ;
    wire                  gmii_tx_en_tmp           ;//GMII发送使能
    wire [7:0]            gmii_txd_tmp             ;
    wire [7:0]            header                   ;//命令头
    wire [15:0]           identify_code            ;//IP序列号
    wire                  udp_rd_en                ;//UDP读使能
    
    always@(posedge gmii_rx_clk or negedge rst_n) begin
        if(rst_n == 1'b0)begin
            gmii_rx_dv_d0 <= 1'b0 ;
            gmii_rxd_d0   <= 8'd0 ;
        end
        else begin
            gmii_rx_dv_d0 <= gmii_rx_dv ;
            gmii_rxd_d0   <= gmii_rxd ;
        end
    end
      
    always@(posedge gmii_tx_clk or negedge rst_n)begin
        if(rst_n == 1'b0)begin
            gmii_tx_en <= 1'b0 ;
            gmii_txd   <= 8'd0 ;
        end
        else begin
            gmii_tx_en <= gmii_tx_en_tmp ;
            gmii_txd   <= gmii_txd_tmp ;
        end
    end
      
    mac_top mac_inst(
        .gmii_tx_clk                 (gmii_tx_clk)                  ,
        .gmii_rx_clk                 (gmii_rx_clk)                  ,
        .rst_n                       (rst_n)  ,
        .identify_code               (identify_code       ),
        .source_mac_addr             (LOCAL_MAC_ADDR)   ,       //source mac address
        .TTL                         (TTL),
        .source_ip_addr              (LOCAL_IP_ADDR),
        .destination_ip_addr         (destination_ip_addr),
        .udp_send_source_port        (UDP_SRC_PORT),
        .udp_send_destination_port   (UDP_DST_PORT),
        
        .ip_rec_source_ip_addr       (ip_rec_source_ip_addr  ),
        
        
        .fifo_data                   (udp_data   ),
        .fifo_rd_en                  (udp_rd_en  ),
        .ram_wr_data                 () ,
        .ram_wr_en                   (),
        .udp_ram_data_req            (),
        .udp_send_data_length        (udp_send_data_length),
        
        .udp_tx_req                  (udp_tx_req),
        .arp_request_req             (arp_request_req ),
        
        .mac_send_end                (mac_send_end),
        .mac_data_valid              (gmii_tx_en_tmp),
        .mac_tx_data                 (gmii_txd_tmp),
        .rx_dv                       (gmii_rx_dv_d0   ),
        .mac_rx_datain               (gmii_rxd_d0 ),
        
        .udp_rec_ram_rdata           (udp_rec_ram_rdata),
        .udp_rec_ram_read_addr       (udp_rec_ram_read_addr),
        .udp_rec_data_length         (udp_rec_data_length ),
        
        .udp_rec_data_valid          (udp_rec_data_valid),
        .arp_found                   (arp_found ),
        .mac_not_exist               (mac_not_exist )
    ) ;
        
 //判断询问命令或控制信号，产生命令应答请求信号或请求数据信号        
    eth_cmd
    #(
        .SAMPLE_RATE   (32'd32000000   ),  //32Msps
        .SAMPLE_DEPTH  (32'h00040000   ),  //262KB
        .DATA_SIGN     (8'h01          ),  //00,unsinged;01,signed
        .DATA_LEN      (8'd8           ),  //adc data width
        .DATA_BYTE     (8'h02          )   //data byte number
     )
     cmd_inst (
         .clk                     (gmii_tx_clk    ),
         .rst_n                   (rst_n      ),
         
         .udp_rec_data_valid      (udp_rec_data_valid  ),    //received data valid
         .udp_rec_ram_rdata       (udp_rec_ram_rdata  ),     //read data from received ram
         .udp_rec_ram_read_addr   (udp_rec_ram_read_addr ),  //read address for received ram
         .udp_rec_data_length     (udp_rec_data_length  ),   //received data length
         .udp_rd_en               (udp_rd_en        ),        //udp read enable
         .reply_data              (reply_data       ),        //reply cmd
         
         .local_ip_addr           (LOCAL_IP_ADDR    ),        //local ip address
         .local_mac_addr          (LOCAL_MAC_ADDR   ),       //local mac address
         
         .ch_sel                  (        ),
         .sample_num              (sample_num       ),
         .header                  (header           ),
         .cmd_reply_ack           (cmd_reply_ack    ),
         .cmd_reply_req           (cmd_reply_req    ),      //cmd reply request
         .cmd_send_len            (cmd_send_len     ),       //cmd reply length
         .ad_data_ack             (ad_data_ack      ),
         .ad_data_req             (ad_data_req      )      //ad data request 
    ) ;
  //以太网的传输控制  
    mac_ctrl ctrl_inst (
        .clk                       (gmii_tx_clk      ),
        .rst_n                     (rst_n        ),
        
        .udp_send_data_length      (udp_send_data_length   ),
        .ip_rec_source_ip_addr     (ip_rec_source_ip_addr   ),    //broadcast source ip address
        .destination_ip_addr       (destination_ip_addr    ),
        .identify_code             (identify_code      ),
        .fifo_data                 (fifo_data       ),                //FIFO涓殑鏁版嵁
        .fifo_data_count           (fifo_data_count     ),    //FIFO涓殑鏁版嵁鏁伴噺
        .fifo_rd_en                (fifo_rd_en       ),            //FIFO璇讳娇鑳?
        .udp_rd_en                 (udp_rd_en       ),
        
        .sample_num                (sample_num       ),
        .sample_len                (sample_len       ),
        .header                    (header        ),
        .reply_data                (reply_data       ),
        .cmd_reply_ack             (cmd_reply_ack      ),
        .cmd_reply_req             (cmd_reply_req      ),      //cmd reply request
        .cmd_send_len              (cmd_send_len      ),       //cmd reply length
        .ad_data_ack               (ad_data_ack      ),
        .ad_data_req               (ad_data_req      ),      //ad data request
        .ad_sample_req             (ad_sample_req      ),
        .ad_sample_ack             (ad_sample_ack      ),
        
        .mac_send_end              (mac_send_end      ),
        .mac_not_exist             (mac_not_exist      ),
        .arp_found                 (arp_found       ),
        .udp_tx_req                (udp_tx_req       ),
        .arp_request_req           (arp_request_req     ),
        .udp_data                  (udp_data       ),
        .read_req_ack              (read_req_ack      ),
        .read_req                  (read_req       )       
    );
         
endmodule

