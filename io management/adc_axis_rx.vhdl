-- ///////////////Documentation////////////////////
-- This module is dedicated to transform the axi stream
-- output of a JESD204B IP core to a continuous
-- 16-bit data stream. Each frame in the axis transaction
-- contains 4 samples from the ADC.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity adc_axis_rx is
    port(
        clk         :   in  std_logic;
        rst         :   in  std_logic;

        -- axis ports
        rx_tdata_in     :   in  std_logic_vector(127 downto 0);
        rx_tvalid_in    :   in  std_logic;

        -- data ports
        data_a_out      :   out std_logic_vector(15 downto 0); -- Main downsampled data output on channel A
        data_a_0_out    :   out std_logic_vector(15 downto 0); -- Sample 0 data output on channel A
        data_a_1_out    :   out std_logic_vector(15 downto 0); -- Sample 1 data output on channel A
        data_a_2_out    :   out std_logic_vector(15 downto 0); -- Sample 2 data output on channel A
        data_a_3_out    :   out std_logic_vector(15 downto 0); -- Sample 3 data output on channel A
        data_b_out      :   out std_logic_vector(15 downto 0); -- Main downsampled data output on channel B
        data_b_0_out    :   out std_logic_vector(15 downto 0); -- Sample 0 data output on channel B
        data_b_1_out    :   out std_logic_vector(15 downto 0); -- Sample 1 data output on channel B
        data_b_2_out    :   out std_logic_vector(15 downto 0); -- Sample 2 data output on channel B
        data_b_3_out    :   out std_logic_vector(15 downto 0); -- Sample 3 data output on channel B
        data_valid_out  :   out std_logic -- Data valid output
    );
end entity adc_axis_rx;

architecture structural of adc_axis_rx is
    signal data_a_out_buf       : std_logic_vector(15 downto 0);
    signal data_a_0_out_buf     : std_logic_vector(15 downto 0);
    signal data_a_1_out_buf     : std_logic_vector(15 downto 0);
    signal data_a_2_out_buf     : std_logic_vector(15 downto 0);
    signal data_a_3_out_buf     : std_logic_vector(15 downto 0);
    signal data_b_out_buf       : std_logic_vector(15 downto 0);
    signal data_b_0_out_buf     : std_logic_vector(15 downto 0);
    signal data_b_1_out_buf     : std_logic_vector(15 downto 0);
    signal data_b_2_out_buf     : std_logic_vector(15 downto 0);
    signal data_b_3_out_buf     : std_logic_vector(15 downto 0);
begin
    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                data_a_out <= (others => '0');
                data_a_0_out <= (others => '0');
                data_a_1_out <= (others => '0');
                data_a_2_out <= (others => '0');
                data_a_3_out <= (others => '0');
                data_b_out <= (others => '0');
                data_b_0_out <= (others => '0');
                data_b_1_out <= (others => '0');
                data_b_2_out <= (others => '0');
                data_b_3_out <= (others => '0');
                data_valid_out <= '0';
            else
                data_a_out <= data_a_out_buf;
                data_a_0_out <= data_a_0_out_buf;
                data_a_1_out <= data_a_1_out_buf;
                data_a_2_out <= data_a_2_out_buf;
                data_a_3_out <= data_a_3_out_buf;
                data_b_out <= data_b_out_buf;
                data_b_0_out <= data_b_0_out_buf;
                data_b_1_out <= data_b_1_out_buf;
                data_b_2_out <= data_b_2_out_buf;
                data_b_3_out <= data_b_3_out_buf;
                if rx_tvalid_in = '1' then
                    data_valid_out <= '1';
                else
                    data_valid_out <= '0';
                end if; 
            end if;
        end if;
    end process;

    data_a_out_buf <= data_a_0_out_buf; -- downsample by 4
    data_a_0_out_buf <= rx_tdata_in(7 downto 0) & rx_tdata_in(32 + 7 downto 32);
    data_a_1_out_buf <= rx_tdata_in(8 + 7 downto 8) & rx_tdata_in(40 + 7 downto 40);
    data_a_2_out_buf <= rx_tdata_in(16 + 7 downto 16) & rx_tdata_in(48 + 7 downto 48);
    data_a_3_out_buf <= rx_tdata_in(24 + 7 downto 24) & rx_tdata_in(56 + 7 downto 56);
    data_b_out_buf <= data_b_0_out_buf; -- downsample by 4
    data_b_0_out_buf <= rx_tdata_in(64 + 7 downto 64) & rx_tdata_in(96 + 7 downto 96);
    data_b_1_out_buf <= rx_tdata_in(72 + 7 downto 72) & rx_tdata_in(104 + 7 downto 104);
    data_b_2_out_buf <= rx_tdata_in(80 + 7 downto 80) & rx_tdata_in(112 + 7 downto 112);
    data_b_3_out_buf <= rx_tdata_in(88 + 7 downto 88) & rx_tdata_in(120 + 7 downto 120);

end architecture structural;