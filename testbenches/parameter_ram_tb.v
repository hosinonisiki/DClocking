// This verilog testbench instantiates a VHDL entity. This is done with vivado mixed language simulation.

module parameter_ram_tb;
    reg clk, rst;

    reg [31:0] wdata;
    reg [4:0]  wadd;
    reg [31:0] wmask;
    reg wval, wen;
    wire [31:0] rdata;
    reg [4:0]  radd;
    wire rval;
    reg ren;

    wire [1023:0] ram;

    parameter_ram UUT(
        .clk(clk),
        .rst(rst),
        .wdata_in(wdata),
        .wadd_in(wadd),
        .wmask_in(wmask),
        .wval_in(wval),
        .wen_in(wen),
        .rdata_out(rdata),
        .radd_in(radd),
        .rval_out(rval),
        .ren_in(ren),
        .ram_data_out(ram)
    );

    initial begin
        clk = 0;
        forever begin
            #1 clk = ~clk;
        end
    end

    initial begin
        rst = 1;
        #10 rst = 0;
    end

    initial begin
        wdata = 32'h00000000;
        wadd = 5'b00000;
        wmask = 32'hFFFFFFFF;
        wval = 1'b1;
        wen = 1'b1;
        radd = 5'b00000;
        ren = 1'b1;

        // Generate random stimulus
        repeat(100) begin
            #10;
            wdata = $random;
            wadd = $random;
            wmask = $random;
            wval = $random;
            wen = $random;
            radd = $random;
            ren = $random;
            #10;
        end
    end
endmodule

