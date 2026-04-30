`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/12/23 10:04:39
// Design Name: 
// Module Name: DataPreprocessor
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
// ������������Ԥ����ģ��
//////////////////////////////////////////////////////////////////////////////////


module DataPreprocessor (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [15:0] sig_a_buf,        // ADC��������
    input  wire [15:0] sig_b_buf,        
    input  wire [15:0] sig_c_buf,
    input  wire [15:0] sig_d_buf,  
    input  wire [15:0] reg_downsample_ratio,
    input  wire [3:0]  upload_channels,  // �ϴ�ͨ��ѡ��
    // ���
    output reg  [63:0] preprocessed_data,      // ���������� (4��16λ)
    output reg         preprocessed_valid     // ���������Ч   
);
    
    reg [15:0] counter;
    reg [15:0] data_buffer[0:3];
    reg [3:0]  channel_valid;      // ͨ����Ч��־
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter <= 16'h0;
            preprocessed_valid <= 1'b0;
            channel_valid <= 4'b0000;
            data_buffer[0] <= 16'h0;
            data_buffer[1] <= 16'h0;
            data_buffer[2] <= 16'h0;
            data_buffer[3] <= 16'h0;  
        end else begin
 
            if (reg_downsample_ratio == 16'h1) begin
                preprocessed_valid <= 1'b1;
                channel_valid <= 4'b1111;
                // �洢��ǰ����
                data_buffer[0] <= sig_a_buf;
                data_buffer[1] <= sig_b_buf;
                data_buffer[2] <= sig_c_buf;
                data_buffer[3] <= sig_d_buf;    
            end else begin
                counter <= counter + 1'b1;
                if (counter == reg_downsample_ratio - 1) begin
                // �洢��ǰ����
                    data_buffer[0] <= sig_a_buf;
                    data_buffer[1] <= sig_b_buf;
                    data_buffer[2] <= sig_c_buf;
                    data_buffer[3] <= sig_d_buf;                  
                    preprocessed_valid <= 1'b1;
                    counter <= 16'h0;
                    channel_valid <= upload_channels;  // ֻ���ѡ�е�ͨ��
                end else begin
                    preprocessed_valid <= 1'b0;
                end
            end
        end
    end
    
// ���ݴ�� (64λ = 4��16λ)
    always @(*) begin
        if (upload_channels[0]) 
            preprocessed_data[15:0]   = data_buffer[0];
        else
             preprocessed_data[15:0] = 16'b0;
        
        if (upload_channels[1]) 
            preprocessed_data[31:16]  = data_buffer[1];
        else 
            preprocessed_data[31:16] = 16'b0;
        
        if (upload_channels[2])
             preprocessed_data[47:32]  = data_buffer[2];
        else
             preprocessed_data[47:32] = 16'b0;
        
        if (upload_channels[3]) 
            preprocessed_data[63:48]  = data_buffer[3];
        else
            preprocessed_data[63:48] = 16'b0;
    end    
    
endmodule
