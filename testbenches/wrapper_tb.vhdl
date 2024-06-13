library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity wrapper_vhdl_tb is
end entity wrapper_vhdl_tb;

architecture structural of wrapper_vhdl_tb is
    signal clk : std_logic := '1';
    signal rst : std_logic := '1';
    signal rst_bar : std_logic := '0';
    signal uart : std_logic := '1';
    signal counter : integer := 0;
    signal txd_data : std_logic_vector(7 downto 0);
    signal tx_empty, tx_notemp, tx_en, tx_idle : std_logic;

    signal char : std_logic_vector(7 downto 0) := "00000000";
    signal en : std_logic := '0';
    component fifo_generator_0
        port(
            clk : in std_logic;
            srst : in std_logic;
            din : in std_logic_vector(7 downto 0);
            wr_en : in std_logic;
            rd_en : in std_logic;
            dout : out std_logic_vector(7 downto 0);
            full : out std_logic;
            empty : out std_logic;
            wr_rst_busy : out std_logic;
            rd_rst_busy : out std_logic 
        );
    end component;
begin
    clk <= not clk after 2500 ps;

    process(clk)
    begin
        if rising_edge(clk) then
            counter <= counter + 1;
        end if;
    end process;

    dut : entity work.wrapper port map(
        sys_clk_p => clk,
        sys_clk_n => not clk,
        rst => rst_bar,
        led_1_o => open,
        led_2_o => open,
        led_3_o => open,
        led_4_o => open,
        panel_led_1_o => open,
        panel_led_2_o => open,
        uart_txd_o => open,
        uart_rxd_i => uart,
        dac_1_2_dci_p_ddr_o => open,
        dac_1_2_dci_n_ddr_o => open,
        dac_1_2_dco_p_i => '1',
        dac_1_2_dco_n_i => '0',
        dac_1_2_data_p_ddr_o => open,
        dac_1_2_data_n_ddr_o => open,
        dac_1_2_spi_ss_o => open,
        dac_3_4_dci_p_ddr_o => open,
        dac_3_4_dci_n_ddr_o => open,
        dac_3_4_dco_p_i => '1',
        dac_3_4_dco_n_i => '0',
        dac_3_4_data_p_ddr_o => open,
        dac_3_4_data_n_ddr_o => open,
        dac_3_4_spi_ss_o => open,
        dac_clk_spi_ss_o => open,
        dac_spi_sck_o => open,
        dac_spi_mosi_o => open,
        dac_spi_miso_i => '0',
        dac_eeprom_iic_scl_o => open,
        dac_eeprom_iic_sda_io => open
    );

    input : entity work.uart_tx port map(
        clk => clk,
        rst => rst,
        txd_out => uart,
        din => txd_data,
        dval_in => tx_notemp,
        den_out => tx_en,
        idle_out => tx_idle
    );
    tx_notemp <= not tx_empty;

    fifo : fifo_generator_0 port map(
        clk => clk,
        srst => rst,
        din => char,
        wr_en => en,
        rd_en => tx_en,
        dout => txd_data,
        full => open,
        empty => tx_empty,
        wr_rst_busy => open,
        rd_rst_busy => open
    );

    rst <= '0' after 100 ns;
    rst_bar <= not rst;

    -- 3A 42 55 53 5F 2E 52 4F 55 54 2E 52 45 41 44 2E 41 44 44 52 2E 30 30 30 30 21
    process(clk)
    begin
        if rising_edge(clk) then
            if counter = 102 then
                char <= x"3A";
                en <= '1';
            elsif counter = 103 then
                char <= x"42";
            elsif counter = 104 then
                char <= x"55";
            elsif counter = 105 then
                char <= x"53";
            elsif counter = 106 then
                char <= x"5F";
            elsif counter = 107 then
                char <= x"2E";
            elsif counter = 108 then
                char <= x"52";
            elsif counter = 109 then
                char <= x"4F";
            elsif counter = 110 then
                char <= x"55";
            elsif counter = 111 then
                char <= x"54";
            elsif counter = 112 then
                char <= x"2E";
            elsif counter = 113 then
                char <= x"52";
            elsif counter = 114 then
                char <= x"45";
            elsif counter = 115 then
                char <= x"41";
            elsif counter = 116 then
                char <= x"44";
            elsif counter = 117 then
                char <= x"2E";
            elsif counter = 118 then
                char <= x"41";
            elsif counter = 119 then
                char <= x"44";
            elsif counter = 120 then
                char <= x"44";
            elsif counter = 121 then
                char <= x"52";
            elsif counter = 122 then
                char <= x"2E";
            elsif counter = 123 then
                char <= x"30";
            elsif counter = 124 then
                char <= x"30";
            elsif counter = 125 then
                char <= x"30";
            elsif counter = 126 then
                char <= x"30";
            elsif counter = 127 then
                char <= x"21";
            elsif counter = 128 then
                en <= '0';
            end if;
        end if;
    end process;
end architecture structural; 
        /*
        dac_1_2_dci_p_ddr_o     :   out std_logic;
        dac_1_2_dci_n_ddr_o     :   out std_logic;
        dac_1_2_dco_p_i         :   in  std_logic;
        dac_1_2_dco_n_i         :   in  std_logic;
        dac_1_2_data_p_ddr_o    :   out std_logic_vector(13 downto 0);
        dac_1_2_data_n_ddr_o    :   out std_logic_vector(13 downto 0);
        dac_1_2_spi_ss_o        :   out std_logic;
        dac_3_4_dci_p_ddr_o     :   out std_logic;
        dac_3_4_dci_n_ddr_o     :   out std_logic;
        dac_3_4_dco_p_i         :   in  std_logic;
        dac_3_4_dco_n_i         :   in  std_logic;
        dac_3_4_data_p_ddr_o    :   out std_logic_vector(13 downto 0);
        dac_3_4_data_n_ddr_o    :   out std_logic_vector(13 downto 0);
        dac_3_4_spi_ss_o        :   out std_logic;
        dac_clk_spi_ss_o        :   out std_logic;
        dac_spi_sck_o           :   out std_logic;
        dac_spi_mosi_o          :   out std_logic;
        dac_spi_miso_i          :   in  std_logic;
        dac_eeprom_iic_scl_o    :   out std_logic;
        dac_eeprom_iic_sda_io   :   inout std_logic
        */
