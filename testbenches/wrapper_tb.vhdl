library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity wrapper_vhdl_tb is
end entity wrapper_vhdl_tb;

architecture structural of wrapper_vhdl_tb is
    signal clk : std_logic := '1';
    signal clk_2 : std_logic := '1';
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

    type diff_pair is array(natural range <>) of std_logic_vector(0 to 1);
    signal fmc1_lpc_clk : diff_pair(0 to 1);
    signal fmc1_lpc_la : diff_pair(0 to 33);
    signal fmc1_lpc_scl : std_logic;
    signal fmc1_lpc_sda : std_logic;
    signal fmc2_lpc_clk : diff_pair(0 to 1);
    signal fmc2_lpc_la : diff_pair(0 to 33);
    signal fmc2_lpc_scl : std_logic;
    signal fmc2_lpc_sda : std_logic;
    signal fmc3_hpc_clk : diff_pair(0 to 1);
    signal fmc3_hpc_la : diff_pair(0 to 33);
    signal fmc3_hpc_scl : std_logic;
    signal fmc3_hpc_sda : std_logic;
begin
    clk <= not clk after 2500 ps;
    clk_2 <= not clk_2 after 2000 ps;

    process(clk_2)
    begin
        if rising_edge(clk_2) then
            if rst = '1' then
                counter <= 0;
            else
                counter <= counter + 1;
            end if;
        end if;
    end process;

    input : entity work.uart_tx port map(
        clk => clk_2,
        rst => rst,
        txd_out => uart,
        din => txd_data,
        dval_in => tx_notemp,
        den_out => tx_en,
        idle_out => tx_idle
    );
    tx_notemp <= not tx_empty;

    fifo : fifo_generator_0 port map(
        clk => clk_2,
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

    rst <= '0' after 50000 ns;
    rst_bar <= not rst;

    -- Test command: ":SPI_.ADC1.\x00\x00\x0F\x17.\x80\x00\x00\x00!"
    -- 
    process(clk_2)
    begin
        if rising_edge(clk_2) then
            if counter = 102 then
                char <= x"3A";  -- :
                en <= '1';
            elsif counter = 103 then
                char <= x"53";  -- S
            elsif counter = 104 then
                char <= x"50";  -- P
            elsif counter = 105 then
                char <= x"49";  -- I
            elsif counter = 106 then
                char <= x"5F";  -- _
            elsif counter = 107 then
                char <= x"2E";  -- .
            elsif counter = 108 then
                char <= x"41";  -- A
            elsif counter = 109 then
                char <= x"44";  -- D
            elsif counter = 110 then
                char <= x"43";  -- C
            elsif counter = 111 then
                char <= x"31";  -- 1
            elsif counter = 112 then
                char <= x"2E";  -- .
            elsif counter = 113 then
                char <= x"00";  -- \x00
            elsif counter = 114 then
                char <= x"00";  -- \x00
            elsif counter = 115 then
                char <= x"0F";  -- \x0F
            elsif counter = 116 then
                char <= x"17";  -- \x17
            elsif counter = 117 then
                char <= x"2E";  -- .
            elsif counter = 118 then
                char <= x"80";  -- \x80
            elsif counter = 119 then
                char <= x"00";  -- \x00
            elsif counter = 120 then
                char <= x"00";  -- \x00
            elsif counter = 121 then
                char <= x"00";  -- \x00
            elsif counter = 122 then
                char <= x"21";  -- !
            elsif counter = 123 then
                en <= '0';
            end if;
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
        
        fmc1_lpc_clk0_p_b => fmc1_lpc_clk(0)(0),
        fmc1_lpc_clk0_n_b => fmc1_lpc_clk(0)(1),
        fmc1_lpc_clk1_p_b => fmc1_lpc_clk(1)(0),
        fmc1_lpc_clk1_n_b => fmc1_lpc_clk(1)(1),
        fmc1_lpc_la00_p_b => fmc1_lpc_la(0)(0),
        fmc1_lpc_la00_n_b => fmc1_lpc_la(0)(1),
        fmc1_lpc_la01_p_b => fmc1_lpc_la(1)(0),
        fmc1_lpc_la01_n_b => fmc1_lpc_la(1)(1),
        fmc1_lpc_la02_p_b => fmc1_lpc_la(2)(0),
        fmc1_lpc_la02_n_b => fmc1_lpc_la(2)(1),
        fmc1_lpc_la03_p_b => fmc1_lpc_la(3)(0),
        fmc1_lpc_la03_n_b => fmc1_lpc_la(3)(1),
        fmc1_lpc_la04_p_b => fmc1_lpc_la(4)(0),
        fmc1_lpc_la04_n_b => fmc1_lpc_la(4)(1),
        fmc1_lpc_la05_p_b => fmc1_lpc_la(5)(0),
        fmc1_lpc_la05_n_b => fmc1_lpc_la(5)(1),
        fmc1_lpc_la06_p_b => fmc1_lpc_la(6)(0),
        fmc1_lpc_la06_n_b => fmc1_lpc_la(6)(1),
        fmc1_lpc_la07_p_b => fmc1_lpc_la(7)(0),
        fmc1_lpc_la07_n_b => fmc1_lpc_la(7)(1),
        fmc1_lpc_la08_p_b => fmc1_lpc_la(8)(0),
        fmc1_lpc_la08_n_b => fmc1_lpc_la(8)(1),
        fmc1_lpc_la09_p_b => fmc1_lpc_la(9)(0),
        fmc1_lpc_la09_n_b => fmc1_lpc_la(9)(1),
        fmc1_lpc_la10_p_b => fmc1_lpc_la(10)(0),
        fmc1_lpc_la10_n_b => fmc1_lpc_la(10)(1),
        fmc1_lpc_la11_p_b => fmc1_lpc_la(11)(0),
        fmc1_lpc_la11_n_b => fmc1_lpc_la(11)(1),
        fmc1_lpc_la12_p_b => fmc1_lpc_la(12)(0),
        fmc1_lpc_la12_n_b => fmc1_lpc_la(12)(1),
        fmc1_lpc_la13_p_b => fmc1_lpc_la(13)(0),
        fmc1_lpc_la13_n_b => fmc1_lpc_la(13)(1),
        fmc1_lpc_la14_p_b => fmc1_lpc_la(14)(0),
        fmc1_lpc_la14_n_b => fmc1_lpc_la(14)(1),
        fmc1_lpc_la15_p_b => fmc1_lpc_la(15)(0),
        fmc1_lpc_la15_n_b => fmc1_lpc_la(15)(1),
        fmc1_lpc_la16_p_b => fmc1_lpc_la(16)(0),
        fmc1_lpc_la16_n_b => fmc1_lpc_la(16)(1),
        fmc1_lpc_la17_p_b => fmc1_lpc_la(17)(0),
        fmc1_lpc_la17_n_b => fmc1_lpc_la(17)(1),
        fmc1_lpc_la18_p_b => fmc1_lpc_la(18)(0),
        fmc1_lpc_la18_n_b => fmc1_lpc_la(18)(1),
        fmc1_lpc_la19_p_b => fmc1_lpc_la(19)(0),
        fmc1_lpc_la19_n_b => fmc1_lpc_la(19)(1),
        fmc1_lpc_la20_p_b => fmc1_lpc_la(20)(0),
        fmc1_lpc_la20_n_b => fmc1_lpc_la(20)(1),
        fmc1_lpc_la21_p_b => fmc1_lpc_la(21)(0),
        fmc1_lpc_la21_n_b => fmc1_lpc_la(21)(1),
        fmc1_lpc_la22_p_b => fmc1_lpc_la(22)(0),
        fmc1_lpc_la22_n_b => fmc1_lpc_la(22)(1),
        fmc1_lpc_la23_p_b => fmc1_lpc_la(23)(0),
        fmc1_lpc_la23_n_b => fmc1_lpc_la(23)(1),
        fmc1_lpc_la24_p_b => fmc1_lpc_la(24)(0),
        fmc1_lpc_la24_n_b => fmc1_lpc_la(24)(1),
        fmc1_lpc_la25_p_b => fmc1_lpc_la(25)(0),
        fmc1_lpc_la25_n_b => fmc1_lpc_la(25)(1),
        fmc1_lpc_la26_p_b => fmc1_lpc_la(26)(0),
        fmc1_lpc_la26_n_b => fmc1_lpc_la(26)(1),
        fmc1_lpc_la27_p_b => fmc1_lpc_la(27)(0),
        fmc1_lpc_la27_n_b => fmc1_lpc_la(27)(1),
        fmc1_lpc_la28_p_b => fmc1_lpc_la(28)(0),
        fmc1_lpc_la28_n_b => fmc1_lpc_la(28)(1),
        fmc1_lpc_la29_p_b => fmc1_lpc_la(29)(0),
        fmc1_lpc_la29_n_b => fmc1_lpc_la(29)(1),
        fmc1_lpc_la30_p_b => fmc1_lpc_la(30)(0),
        fmc1_lpc_la30_n_b => fmc1_lpc_la(30)(1),
        fmc1_lpc_la31_p_b => fmc1_lpc_la(31)(0),
        fmc1_lpc_la31_n_b => fmc1_lpc_la(31)(1),
        fmc1_lpc_la32_p_b => fmc1_lpc_la(32)(0),
        fmc1_lpc_la32_n_b => fmc1_lpc_la(32)(1),
        fmc1_lpc_la33_p_b => fmc1_lpc_la(33)(0),
        fmc1_lpc_la33_n_b => fmc1_lpc_la(33)(1),
        fmc1_lpc_scl_b => fmc1_lpc_scl,
        fmc1_lpc_sda_b => fmc1_lpc_sda,
        
        fmc2_lpc_clk0_p_b => fmc2_lpc_clk(0)(0),
        fmc2_lpc_clk0_n_b => fmc2_lpc_clk(0)(1),
        fmc2_lpc_clk1_p_b => fmc2_lpc_clk(1)(0),
        fmc2_lpc_clk1_n_b => fmc2_lpc_clk(1)(1),
        fmc2_lpc_la00_p_b => fmc2_lpc_la(0)(0),
        fmc2_lpc_la00_n_b => fmc2_lpc_la(0)(1),
        fmc2_lpc_la01_p_b => fmc2_lpc_la(1)(0),
        fmc2_lpc_la01_n_b => fmc2_lpc_la(1)(1),
        fmc2_lpc_la02_p_b => fmc2_lpc_la(2)(0),
        fmc2_lpc_la02_n_b => fmc2_lpc_la(2)(1),
        fmc2_lpc_la03_p_b => fmc2_lpc_la(3)(0),
        fmc2_lpc_la03_n_b => fmc2_lpc_la(3)(1),
        fmc2_lpc_la04_p_b => fmc2_lpc_la(4)(0),
        fmc2_lpc_la04_n_b => fmc2_lpc_la(4)(1),
        fmc2_lpc_la05_p_b => fmc2_lpc_la(5)(0),
        fmc2_lpc_la05_n_b => fmc2_lpc_la(5)(1),
        fmc2_lpc_la06_p_b => fmc2_lpc_la(6)(0),
        fmc2_lpc_la06_n_b => fmc2_lpc_la(6)(1),
        fmc2_lpc_la07_p_b => fmc2_lpc_la(7)(0),
        fmc2_lpc_la07_n_b => fmc2_lpc_la(7)(1),
        fmc2_lpc_la08_p_b => fmc2_lpc_la(8)(0),
        fmc2_lpc_la08_n_b => fmc2_lpc_la(8)(1),
        fmc2_lpc_la09_p_b => fmc2_lpc_la(9)(0),
        fmc2_lpc_la09_n_b => fmc2_lpc_la(9)(1),
        fmc2_lpc_la10_p_b => fmc2_lpc_la(10)(0),
        fmc2_lpc_la10_n_b => fmc2_lpc_la(10)(1),
        fmc2_lpc_la11_p_b => fmc2_lpc_la(11)(0),
        fmc2_lpc_la11_n_b => fmc2_lpc_la(11)(1),
        fmc2_lpc_la12_p_b => fmc2_lpc_la(12)(0),
        fmc2_lpc_la12_n_b => fmc2_lpc_la(12)(1),
        fmc2_lpc_la13_p_b => fmc2_lpc_la(13)(0),
        fmc2_lpc_la13_n_b => fmc2_lpc_la(13)(1),
        fmc2_lpc_la14_p_b => fmc2_lpc_la(14)(0),
        fmc2_lpc_la14_n_b => fmc2_lpc_la(14)(1),
        fmc2_lpc_la15_p_b => fmc2_lpc_la(15)(0),
        fmc2_lpc_la15_n_b => fmc2_lpc_la(15)(1),
        fmc2_lpc_la16_p_b => fmc2_lpc_la(16)(0),
        fmc2_lpc_la16_n_b => fmc2_lpc_la(16)(1),
        fmc2_lpc_la17_p_b => fmc2_lpc_la(17)(0),
        fmc2_lpc_la17_n_b => fmc2_lpc_la(17)(1),
        fmc2_lpc_la18_p_b => fmc2_lpc_la(18)(0),
        fmc2_lpc_la18_n_b => fmc2_lpc_la(18)(1),
        fmc2_lpc_la19_p_b => fmc2_lpc_la(19)(0),
        fmc2_lpc_la19_n_b => fmc2_lpc_la(19)(1),
        fmc2_lpc_la20_p_b => fmc2_lpc_la(20)(0),
        fmc2_lpc_la20_n_b => fmc2_lpc_la(20)(1),
        fmc2_lpc_la21_p_b => fmc2_lpc_la(21)(0),
        fmc2_lpc_la21_n_b => fmc2_lpc_la(21)(1),
        fmc2_lpc_la22_p_b => fmc2_lpc_la(22)(0),
        fmc2_lpc_la22_n_b => fmc2_lpc_la(22)(1),
        fmc2_lpc_la23_p_b => fmc2_lpc_la(23)(0),
        fmc2_lpc_la23_n_b => fmc2_lpc_la(23)(1),
        fmc2_lpc_la24_p_b => fmc2_lpc_la(24)(0),
        fmc2_lpc_la24_n_b => fmc2_lpc_la(24)(1),
        fmc2_lpc_la25_p_b => fmc2_lpc_la(25)(0),
        fmc2_lpc_la25_n_b => fmc2_lpc_la(25)(1),
        fmc2_lpc_la26_p_b => fmc2_lpc_la(26)(0),
        fmc2_lpc_la26_n_b => fmc2_lpc_la(26)(1),
        fmc2_lpc_la27_p_b => fmc2_lpc_la(27)(0),
        fmc2_lpc_la27_n_b => fmc2_lpc_la(27)(1),
        fmc2_lpc_la28_p_b => fmc2_lpc_la(28)(0),
        fmc2_lpc_la28_n_b => fmc2_lpc_la(28)(1),
        fmc2_lpc_la29_p_b => fmc2_lpc_la(29)(0),
        fmc2_lpc_la29_n_b => fmc2_lpc_la(29)(1),
        fmc2_lpc_la30_p_b => fmc2_lpc_la(30)(0),
        fmc2_lpc_la30_n_b => fmc2_lpc_la(30)(1),
        fmc2_lpc_la31_p_b => fmc2_lpc_la(31)(0),
        fmc2_lpc_la31_n_b => fmc2_lpc_la(31)(1),
        fmc2_lpc_la32_p_b => fmc2_lpc_la(32)(0),
        fmc2_lpc_la32_n_b => fmc2_lpc_la(32)(1),
        fmc2_lpc_la33_p_b => fmc2_lpc_la(33)(0),
        fmc2_lpc_la33_n_b => fmc2_lpc_la(33)(1),
        fmc2_lpc_scl_b => fmc2_lpc_scl,
        fmc2_lpc_sda_b => fmc2_lpc_sda,

        fmc3_hpc_clk0_p_b => fmc3_hpc_clk(0)(0),
        fmc3_hpc_clk0_n_b => fmc3_hpc_clk(0)(1),
        fmc3_hpc_clk1_p_b => fmc3_hpc_clk(1)(0),
        fmc3_hpc_clk1_n_b => fmc3_hpc_clk(1)(1),
        fmc3_hpc_la00_p_b => fmc3_hpc_la(0)(0),
        fmc3_hpc_la00_n_b => fmc3_hpc_la(0)(1),
        fmc3_hpc_la01_p_b => fmc3_hpc_la(1)(0),
        fmc3_hpc_la01_n_b => fmc3_hpc_la(1)(1),
        fmc3_hpc_la02_p_b => fmc3_hpc_la(2)(0),
        fmc3_hpc_la02_n_b => fmc3_hpc_la(2)(1),
        fmc3_hpc_la03_p_b => fmc3_hpc_la(3)(0),
        fmc3_hpc_la03_n_b => fmc3_hpc_la(3)(1),
        fmc3_hpc_la04_p_b => fmc3_hpc_la(4)(0),
        fmc3_hpc_la04_n_b => fmc3_hpc_la(4)(1),
        fmc3_hpc_la05_p_b => fmc3_hpc_la(5)(0),
        fmc3_hpc_la05_n_b => fmc3_hpc_la(5)(1),
        fmc3_hpc_la06_p_b => fmc3_hpc_la(6)(0),
        fmc3_hpc_la06_n_b => fmc3_hpc_la(6)(1),
        fmc3_hpc_la07_p_b => fmc3_hpc_la(7)(0),
        fmc3_hpc_la07_n_b => fmc3_hpc_la(7)(1),
        fmc3_hpc_la08_p_b => fmc3_hpc_la(8)(0),
        fmc3_hpc_la08_n_b => fmc3_hpc_la(8)(1),
        fmc3_hpc_la09_p_b => fmc3_hpc_la(9)(0),
        fmc3_hpc_la09_n_b => fmc3_hpc_la(9)(1),
        fmc3_hpc_la10_p_b => fmc3_hpc_la(10)(0),
        fmc3_hpc_la10_n_b => fmc3_hpc_la(10)(1),
        fmc3_hpc_la11_p_b => fmc3_hpc_la(11)(0),
        fmc3_hpc_la11_n_b => fmc3_hpc_la(11)(1),
        fmc3_hpc_la12_p_b => fmc3_hpc_la(12)(0),
        fmc3_hpc_la12_n_b => fmc3_hpc_la(12)(1),
        fmc3_hpc_la13_p_b => fmc3_hpc_la(13)(0),
        fmc3_hpc_la13_n_b => fmc3_hpc_la(13)(1),
        fmc3_hpc_la14_p_b => fmc3_hpc_la(14)(0),
        fmc3_hpc_la14_n_b => fmc3_hpc_la(14)(1),
        fmc3_hpc_la15_p_b => fmc3_hpc_la(15)(0),
        fmc3_hpc_la15_n_b => fmc3_hpc_la(15)(1),
        fmc3_hpc_la16_p_b => fmc3_hpc_la(16)(0),
        fmc3_hpc_la16_n_b => fmc3_hpc_la(16)(1),
        fmc3_hpc_la17_p_b => fmc3_hpc_la(17)(0),
        fmc3_hpc_la17_n_b => fmc3_hpc_la(17)(1),
        fmc3_hpc_la18_p_b => fmc3_hpc_la(18)(0),
        fmc3_hpc_la18_n_b => fmc3_hpc_la(18)(1),
        fmc3_hpc_la19_p_b => fmc3_hpc_la(19)(0),
        fmc3_hpc_la19_n_b => fmc3_hpc_la(19)(1),
        fmc3_hpc_la20_p_b => fmc3_hpc_la(20)(0),
        fmc3_hpc_la20_n_b => fmc3_hpc_la(20)(1),
        fmc3_hpc_la21_p_b => fmc3_hpc_la(21)(0),
        fmc3_hpc_la21_n_b => fmc3_hpc_la(21)(1),
        fmc3_hpc_la22_p_b => fmc3_hpc_la(22)(0),
        fmc3_hpc_la22_n_b => fmc3_hpc_la(22)(1),
        fmc3_hpc_la23_p_b => fmc3_hpc_la(23)(0),
        fmc3_hpc_la23_n_b => fmc3_hpc_la(23)(1),
        fmc3_hpc_la24_p_b => fmc3_hpc_la(24)(0),
        fmc3_hpc_la24_n_b => fmc3_hpc_la(24)(1),
        fmc3_hpc_la25_p_b => fmc3_hpc_la(25)(0),
        fmc3_hpc_la25_n_b => fmc3_hpc_la(25)(1),
        fmc3_hpc_la26_p_b => fmc3_hpc_la(26)(0),
        fmc3_hpc_la26_n_b => fmc3_hpc_la(26)(1),
        fmc3_hpc_la27_p_b => fmc3_hpc_la(27)(0),
        fmc3_hpc_la27_n_b => fmc3_hpc_la(27)(1),
        fmc3_hpc_la28_p_b => fmc3_hpc_la(28)(0),
        fmc3_hpc_la28_n_b => fmc3_hpc_la(28)(1),
        fmc3_hpc_la29_p_b => fmc3_hpc_la(29)(0),
        fmc3_hpc_la29_n_b => fmc3_hpc_la(29)(1),
        fmc3_hpc_la30_p_b => fmc3_hpc_la(30)(0),
        fmc3_hpc_la30_n_b => fmc3_hpc_la(30)(1),
        fmc3_hpc_la31_p_b => fmc3_hpc_la(31)(0),
        fmc3_hpc_la31_n_b => fmc3_hpc_la(31)(1),
        fmc3_hpc_la32_p_b => fmc3_hpc_la(32)(0),
        fmc3_hpc_la32_n_b => fmc3_hpc_la(32)(1),
        fmc3_hpc_la33_p_b => fmc3_hpc_la(33)(0),
        fmc3_hpc_la33_n_b => fmc3_hpc_la(33)(1),
        fmc3_hpc_scl_b => fmc3_hpc_scl,
        fmc3_hpc_sda_b => fmc3_hpc_sda
    );
end architecture structural; 
