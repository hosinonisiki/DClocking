// This verilog testbench instantiates a VHDL entity. This is done with vivado mixed language simulation.

module wrapper_tb;
    reg clk, rst;

    reg rxd;
    wire txd;

    wire led_1, led_2, led_3, led_4;
    wire panel_led_1, panel_led_2;

    wire dac_1_2_dci_p_ddr_o, dac_1_2_dci_n_ddr_o, dac_3_4_dci_p_ddr_o, dac_3_4_dci_n_ddr_o;
    wire dac_1_2_spi_ss_o, dac_3_4_spi_ss_o, dac_clk_spi_ss_o, dac_spi_sck_o, dac_spi_mosi_o, dac_eeprom_iic_scl_o, dac_eeprom_iic_sda_io;
    wire [13:0] dac_1_2_data_p_ddr_o, dac_1_2_data_n_ddr_o, dac_3_4_data_p_ddr_o, dac_3_4_data_n_ddr_o;

    reg dac_1_2_dco_p_i, dac_1_2_dco_n_i, dac_3_4_dco_p_i, dac_3_4_dco_n_i;
    reg dac_spi_miso_i;

    wrapper UUT(
        .sys_clk_p(clk),
        .sys_clk_n(~clk),
        .rst(rst),
        .led_1_o(led_1),
        .led_2_o(led_2),
        .led_3_o(led_3),
        .led_4_o(led_4),
        .panel_led_1_o(panel_led_1),
        .panel_led_2_o(panel_led_2),
        .uart_rxd_i(rxd),
        .uart_txd_o(txd),
        .dac_1_2_dci_p_ddr_o(dac_1_2_dci_p_ddr_o),
        .dac_1_2_dci_n_ddr_o(dac_1_2_dci_n_ddr_o),
        .dac_3_4_dci_p_ddr_o(dac_3_4_dci_p_ddr_o),
        .dac_3_4_dci_n_ddr_o(dac_3_4_dci_n_ddr_o),
        .dac_1_2_spi_ss_o(dac_1_2_spi_ss_o),
        .dac_3_4_spi_ss_o(dac_3_4_spi_ss_o),
        .dac_clk_spi_ss_o(dac_clk_spi_ss_o),
        .dac_spi_sck_o(dac_spi_sck_o),
        .dac_spi_mosi_o(dac_spi_mosi_o),
        .dac_eeprom_iic_scl_o(dac_eeprom_iic_scl_o),
        .dac_eeprom_iic_sda_io(dac_eeprom_iic_sda_io),
        .dac_1_2_data_p_ddr_o(dac_1_2_data_p_ddr_o),
        .dac_1_2_data_n_ddr_o(dac_1_2_data_n_ddr_o),
        .dac_3_4_data_p_ddr_o(dac_3_4_data_p_ddr_o),
        .dac_3_4_data_n_ddr_o(dac_3_4_data_n_ddr_o),
        .dac_1_2_dco_p_i(dac_1_2_dco_p_i),
        .dac_1_2_dco_n_i(dac_1_2_dco_n_i),
        .dac_3_4_dco_p_i(dac_3_4_dco_p_i),
        .dac_3_4_dco_n_i(dac_3_4_dco_n_i),
        .dac_spi_miso_i(dac_spi_miso_i)
    );

    initial begin
        clk = 0;
        forever begin
            #2.5 clk = ~clk; // 5 ns period
        end
    end

    initial begin
        dac_1_2_dco_p_i = 0;
        dac_1_2_dco_n_i = 0;
        dac_3_4_dco_p_i = 0;
        dac_3_4_dco_n_i = 0;
        dac_spi_miso_i = 0;
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
