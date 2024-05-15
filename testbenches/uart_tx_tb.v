// This verilog testbench instantiates a VHDL entity. This is done with vivado mixed language simulation.module uart_rx_tb;
    
module uart_tx_tb;
    reg clk, rst;

    wire txd;

    reg [7:0] data;
    wire idle;
    reg dval;
    wire den;

    uart_tx UUT(
        .clk(clk),
        .rst(rst),
        .txd_out(txd),
        .din(data),
        .dval_in(dval),
        .den_out(den),
        .idle_out(idle)
    );

    initial begin
        clk = 0;
        forever begin
            #2.5 clk = ~clk; // 5 ns period
        end
    end

    initial begin
        dval = 0;
        rst = 1;
        #10 rst = 0;
        #10 dval = 1;
    end

    integer counter = 0;
    always @(posedge clk) begin
        if(den) begin
            counter = counter + 1;
            if (counter == 1) begin
                data = 8'h68; // 'h' in ascii
            end
            if (counter == 2) begin
                data = 8'h65; // 'e' in ascii
            end
            if (counter == 3) begin
                data = 8'h6c; // 'l' in ascii
            end
            if (counter == 4) begin
                data = 8'h6c; // 'l' in ascii
            end
            if (counter == 5) begin
                data = 8'h6f; // 'o' in ascii
            end
            if (counter == 6) begin
                data = 8'h77; // 'w' in ascii
            end
            if (counter == 7) begin
                data = 8'h6f; // 'o' in ascii
            end
            if (counter == 8) begin
                data = 8'h72; // 'r' in ascii
            end
            if (counter == 9) begin
                data = 8'h6c; // 'l' in ascii
            end
            if (counter == 10) begin
                data = 8'h64; // 'd' in ascii
            end
        end
    end


endmodule