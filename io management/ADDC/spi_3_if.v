module spi_3_if #(
  parameter WORD_BIT_LENGTH=24
)(
  input clk,
  input reset,

  input we,
  input [31:0] din,
  output reg [31:0] dout,

  output reg sclk,
  output reg csb,
  output sdio_o,
  input sdio_i,
  output reg sdio_oe
);

reg [WORD_BIT_LENGTH-1:0] shift_reg;
reg rd_flag=0;
reg [5:0] bit_cnt;

localparam  S_IDLE=2'd0,
            S_ASSERT_CS=2'd1,
            S_DATA_TRAN=2'd2,
            S_DEASSERT_CS=2'd3;

reg [1:0] state=S_IDLE;

reg [7:0] div_cnt=0;
reg clk_rising=0;
reg clk_falling=0;

always @(posedge clk)
begin
  if(reset)
    div_cnt<=8'd0;
  else if(div_cnt==8'd99)
    div_cnt<=8'd0;
  else
    div_cnt<=div_cnt+8'd1;
end

always @(posedge clk)
begin
  if(div_cnt==8'd0)
  begin
    clk_falling<=1'b1;
    clk_rising<=1'b0;
  end
  else if(div_cnt==8'd49)
  begin
    clk_rising<=1'b1;
    clk_falling<=1'b0;
  end
  else
  begin
    clk_rising<=1'b0;
    clk_falling<=1'b0;
  end
end

always @(posedge clk)
begin
  if(reset)
  begin
    state<=S_IDLE;
  end
  else
  begin
    case(state)
      S_IDLE:
      begin
        sclk<=1'b0;
        csb<=1'b1;
        if(we==1'b1)
        begin
          shift_reg<=din[WORD_BIT_LENGTH-1:0];
          rd_flag<=din[WORD_BIT_LENGTH-1];
          bit_cnt<=6'b0;
          state<=S_ASSERT_CS;
          sdio_oe<=1'b1;
        end
        else
        begin
          sdio_oe<=1'b0;
        end
      end
      S_ASSERT_CS:
      begin
        if(clk_falling==1'b1)
        begin
          csb<=1'b0;
          state<=S_DATA_TRAN;
        end
      end
      S_DATA_TRAN:
      begin
        if(clk_rising==1'b1)
          sclk<=1'b1;
        else if(clk_falling==1'b1)
          sclk<=1'b0;

        if(clk_falling==1'b1)
        begin
          shift_reg<={shift_reg[WORD_BIT_LENGTH-2:0],1'b0};
          bit_cnt<=bit_cnt+6'd1;
        end

        if(clk_rising==1'b1)
          dout<={dout[30:0],sdio_i};
       
        if(clk_falling==1'b1 && bit_cnt==(WORD_BIT_LENGTH-9) && rd_flag==1'b1)
          sdio_oe<=1'b0;

        if(clk_rising==1'b1 && bit_cnt==WORD_BIT_LENGTH-1)
          state<=S_DEASSERT_CS;
      end
      S_DEASSERT_CS:
      begin
        if(clk_falling==1'b1)
        begin
          state<=S_IDLE;
          sclk<=1'b0;
          csb<=1'b1;
          sdio_oe<=1'b0;
        end
      end
    endcase
  end
end

assign sdio_o=shift_reg[WORD_BIT_LENGTH-1];

endmodule



  




