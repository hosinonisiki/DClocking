// This verilog testbench instantiates a VHDL entity. This is done with vivado mixed language simulation.

module main_control_tb;
    reg clk, rst;

    reg rxd;
    reg [31:0] rsp;
    reg [7:0] rsp_stat;

    wire txd;
    wire [31:0] dbus;
    wire [4:0] abus;
    wire [7:0] mbus;
    wire [7:0] cbus;

    main_control UUT(
        .clk(clk),
        .rst(rst),
        .rxd_in(rxd),
        .txd_out(txd),
        .dbus_out(dbus),
        .abus_out(abus),
        .mbus_out(mbus),
        .cbus_out(cbus),
        .rsp_in(rsp),
        .rsp_stat_in(rsp_stat)
    );

    initial begin
        clk = 0;
        forever begin
            #2.5 clk = ~clk; // 5 ns period
        end
    end

    initial begin
        rsp = 32'h00000000;
        rsp_stat = 8'h00;
        rst = 1;
        #1000 rst = 0;
    end

    initial begin
        // baudrate = 57600, 17.361 us per bit
        rxd = 1;
        // wait for 100 us
        #100_000 rxd = 1;
        // send "hi"
        // start
        #17361 rxd = 0;
        // 'h'
        #17361 rxd = 0;
        #17361 rxd = 0;
        #17361 rxd = 0;
        #17361 rxd = 1;
        #17361 rxd = 0;
        #17361 rxd = 1;
        #17361 rxd = 1;
        #17361 rxd = 0;
        // parity
        #17361 rxd = 1;
        // stop
        #17361 rxd = 1;
        // start
        #17361 rxd = 0;
        // 'i'
        #17361 rxd = 1;
        #17361 rxd = 0;
        #17361 rxd = 0;
        #17361 rxd = 1;
        #17361 rxd = 0;
        #17361 rxd = 1;
        #17361 rxd = 1;
        #17361 rxd = 0;
        // parity
        #17361 rxd = 0;
        // stop
        #17361 rxd = 1;
        // wait for 100 us
        #100_000 rxd = 1;
        // send 192 in digits
        // Send '1'
        #17361 rxd = 0;  // start bit
        #17361 rxd = 1;  // '1' bit 0
        #17361 rxd = 0;  // '1' bit 1
        #17361 rxd = 0;  // '1' bit 2
        #17361 rxd = 0;  // '1' bit 3
        #17361 rxd = 1;  // '1' bit 4
        #17361 rxd = 1;  // '1' bit 5
        #17361 rxd = 0;  // '1' bit 6
        #17361 rxd = 0;  // '1' bit 7
        #17361 rxd = 1;  // parity bit
        #17361 rxd = 1;  // stop bit

        // Send '9'
        #17361 rxd = 0;  // start bit
        #17361 rxd = 1;  // '9' bit 0
        #17361 rxd = 0;  // '9' bit 1
        #17361 rxd = 0;  // '9' bit 2
        #17361 rxd = 1;  // '9' bit 3
        #17361 rxd = 1;  // '9' bit 4
        #17361 rxd = 1;  // '9' bit 5
        #17361 rxd = 0;  // '9' bit 6
        #17361 rxd = 0;  // '9' bit 7
        #17361 rxd = 0;  // parity bit
        #17361 rxd = 1;  // stop bit

        // Send '2'
        #17361 rxd = 0;  // start bit
        #17361 rxd = 0;  // '2' bit 0
        #17361 rxd = 1;  // '2' bit 1
        #17361 rxd = 0;  // '2' bit 2
        #17361 rxd = 0;  // '2' bit 3
        #17361 rxd = 1;  // '2' bit 4
        #17361 rxd = 1;  // '2' bit 5
        #17361 rxd = 0;  // '2' bit 6
        #17361 rxd = 0;  // '2' bit 7
        #17361 rxd = 1;  // parity bit
        #17361 rxd = 1;  // stop bit

        // wait for 100 us
        #100_000 rxd = 1;
        // send illegal package
        // start
        #17361 rxd = 0;
        // 0x0F
        #17361 rxd = 1;
        #17361 rxd = 1;
        #17361 rxd = 1;
        #17361 rxd = 1;
        #17361 rxd = 0;
        #17361 rxd = 0;
        #17361 rxd = 0;
        #17361 rxd = 0;
        // parity
        #17361 rxd = 1;
        // stop
        #17361 rxd = 1;

        // wait for 100 us
        #100_000 rxd = 1;
        // send unproperly stopped package
        // start
        #17361 rxd = 0;
        // 0x33
        #17361 rxd = 1;
        #17361 rxd = 1;
        #17361 rxd = 0;
        #17361 rxd = 0;
        #17361 rxd = 1;
        #17361 rxd = 1;
        #17361 rxd = 0;
        #17361 rxd = 0;
        // parity
        #17361 rxd = 0;
        // stop
        #17361 rxd = 0;
        #17361 rxd = 1;

        //start
        #17361 rxd = 0;
        // 0x3C
        #17361 rxd = 0;
        #17361 rxd = 0;
        #17361 rxd = 1;
        #17361 rxd = 1;
        #17361 rxd = 1;
        #17361 rxd = 1;
        #17361 rxd = 0;
        #17361 rxd = 0;
        // parity
        #17361 rxd = 0;
        // stop
        #17361 rxd = 0;
        #17361 rxd = 0;
        #17361 rxd = 1;

        // wait for 100 us
        #100_000 rxd = 1;
        // send random fluctuations
        for (integer i = 0; i < 200; i = i + 1) begin
            #($urandom%10000) rxd = $random%2;  // Random delay and random value
        end
    end
endmodule
