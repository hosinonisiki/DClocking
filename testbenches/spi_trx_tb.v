// This verilog testbench instantiates a VHDL entity. This is done with vivado mixed language simulation.

module spi_trx_tb;
    reg cpol, cpha;
    reg clk, rst;
    reg spi_en;
    wire a2b, b2a;
    wire sclka, sclkb;
    reg [31:0] dina, dinb;
    wire [31:0] douta, doutb;
    wire dvala, dvalb, idlea, idleb;
    reg [4:0] width;

    spi_trx UUTA(
        .clk(clk),
        .rst(rst),
        .spi_en_in(spi_en),
        .ss_in(4'b0000),
        .ss_out(),
        .width(width),
        .mosi(a2b),
        .miso(b2a),
        .sclk_out(sclka),
        .din(dina),
        .dout(douta),
        .dval_out(dvala),
        .idle_out(idlea)
    );

    spi_trx UUTB(
        .clk(clk),
        .rst(rst),
        .spi_en_in(spi_en),
        .ss_in(4'b0000),
        .ss_out(),
        .width(width),
        .mosi(b2a),
        .miso(a2b),
        .sclk_out(sclkb),
        .din(dinb),
        .dout(doutb),
        .dval_out(dvalb),
        .idle_out(idleb)
    );

    initial begin
        cpol = 0;
        cpha = 0;
        dina = 32'b10101010000011110011001101100110;
        dinb = 32'b01010101111100001100110010011001;
        width = 5'b11111;
    end

    initial begin
        clk = 0;
        forever begin
            #2.5 clk = ~clk; // 5 ns period
        end
    end

    initial begin
        rst = 1;
        #1000 rst = 0;
    end

    initial begin
        spi_en = 0;
        #2000 spi_en = 1;
        #10 spi_en = 0;
        #200 spi_en = 1;
        #10 spi_en = 0;
        #400 spi_en = 1;
        #10 spi_en = 0;
        #600 spi_en = 1;
        #10 spi_en = 0;
        #800 spi_en = 1;
        #10 spi_en = 0;
        #1000 spi_en = 1;
        #10 spi_en = 0;
    end
endmodule