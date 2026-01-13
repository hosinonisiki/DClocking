`timescale 1ns / 1ps  
//////////////////////////////////////////////////////////////////////////////////
// Module Name:    ethernet_test 
//////////////////////////////////////////////////////////////////////////////////
module ethernet_test
(
    input            rst_n,
    input            clk,   
         
    input  [15:0]    fifo_data,             //FIFO数据
    input  [11:0]    fifo_data_count,       //FIFO数据可读量
    output           fifo_rd_en,            //FIFO读使能                
    input            read_req_ack,//读ADC采集数据应答
    output           read_req,//读ADC数据请求
    output           ad_sample_req,//ADC采样请求
    input            ad_sample_ack,//ADC采样应答
    output [31:0]    sample_len,//采样长度
    //以太网接口
    output [3:0]     rgmii_txd,
    output           rgmii_txctl,
    output           rgmii_txc,
    input  [3:0]     rgmii_rxd,
    input            rgmii_rxctl,
    input            rgmii_rxc,
    output [3:0]     led,
    output           e_mdc,
    inout            e_mdio,
    output		     e_reset
);


    wire   [ 7:0]   gmii_txd     ;
    wire            gmii_tx_en   ;
    wire            gmii_tx_er   ;
    wire            gmii_tx_clk  ;
    wire            gmii_crs     ;
    wire            gmii_col     ;
    wire   [ 7:0]   gmii_rxd     ;
    wire            gmii_rx_dv   ;
    wire            gmii_rx_er   ;
    wire            gmii_rx_clk  ;
    
    wire  [31:0]    pack_total_len ;
    wire            duplex_mode;     // 1 full, 0 half
    
    assign duplex_mode = 1'b1;
    
    wire [1:0]      speed      ;
    wire            link       ;
    (* MARK_DEBUG="true" *)wire            e_rx_dv    ;
    (* MARK_DEBUG="true" *)wire [7:0]      e_rxd      ;
    wire            e_tx_en    ;
    wire [7:0]      e_txd      ;
    wire            e_rst_n    ;
    
    
    
    
    gmii_arbi arbi_inst(
        .clk                (gmii_tx_clk      ),
        .rst_n              (rst_n            ),
        .speed              (speed            ),  
        .link               (link             ), 
        .pack_total_len     (pack_total_len   ), 
        .e_rst_n            (e_rst_n          ),
        .gmii_rx_dv         (gmii_rx_dv       ),
        .gmii_rxd           (gmii_rxd         ),
        .gmii_tx_en         (gmii_tx_en       ),
        .gmii_txd           (gmii_txd         ), 
        .e_rx_dv            (e_rx_dv          ),
        .e_rxd              (e_rxd            ),
        .e_tx_en            (e_tx_en          ),
        .e_txd              (e_txd            ) 
    );
    
    
    
    smi_config  smi_config_inst(
        .clk         (clk  ),
        .rst_n       (rst_n    ),		 
        .mdc         (e_mdc    ),
        .mdio        (e_mdio   ),
        .speed       (speed    ),
        .link        (link     ),
        .led         (led      )	
    );
    	
    util_gmii_to_rgmii util_gmii_to_rgmii_m0(
        .reset                  (~rst_n           ),
        
        .rgmii_td               (rgmii_txd       ),
        .rgmii_tx_ctl           (rgmii_txctl     ),
        .rgmii_txc              (rgmii_txc       ),
        .rgmii_rd               (rgmii_rxd       ),
        .rgmii_rx_ctl           (rgmii_rxctl     ),
        .rgmii_rxc              (rgmii_rxc       ),
                                                 
        .gmii_txd               (e_txd           ),
        .gmii_tx_en             (e_tx_en         ),
        .gmii_tx_er             (1'b0            ),
        .gmii_tx_clk            (gmii_tx_clk     ),
        .gmii_crs               (gmii_crs        ),
        .gmii_col               (gmii_col        ),
        .gmii_rxd               (gmii_rxd        ),
        .gmii_rx_dv             (gmii_rx_dv      ),
        .gmii_rx_er             (gmii_rx_er      ),
        .gmii_rx_clk            (gmii_rx_clk     ),
        .duplex_mode            (duplex_mode     )
    );
    eth_top eth_top_inst(   
        .rst_n                   (rst_n           ),        
        .fifo_data               (read_data       ),           //FIFO读出皿8bit数据/
        .fifo_data_count         (read_usedw      ),          //FIFO中的数据数量
        .fifo_rd_en              (read_en         ),             //FIFO读使胿   
        .read_req_ack            (read_req_ack    ),
        .read_req                (read_req        ),
        .ad_sample_req           (ad_sample_req   ),
        .ad_sample_ack           (ad_sample_ack   ),
        .sample_len              (sample_len      ),
        .gmii_tx_clk             (gmii_tx_clk     ),
        .gmii_rx_clk             (gmii_rx_clk     ) ,
        .gmii_rx_dv              (e_rx_dv      ),
        .gmii_rxd                (e_rxd        ),
        .gmii_tx_en              (gmii_tx_en      ),
        .gmii_txd                (gmii_txd        )    
    );
    	
//mac_test mac_test0
//(
// .gmii_tx_clk            (gmii_tx_clk     ),
// .gmii_rx_clk            (gmii_rx_clk     ),
// .rst_n                  (e_rst_n         ),

// .pack_total_len         (pack_total_len  ),
// .gmii_rx_dv             (e_rx_dv         ),
// .gmii_rxd               (e_rxd           ),
// .gmii_tx_en             (gmii_tx_en      ),
// .gmii_txd               (gmii_txd        )
 
//); 

	   
endmodule

