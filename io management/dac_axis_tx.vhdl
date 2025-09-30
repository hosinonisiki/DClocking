-- ///////////////Documentation////////////////////
-- This module is dedicated to transform a continuous
-- 16-bit data stream to the axi stream input of a
-- JESD204B IP core. Each frame in the axis transaction
-- contains 4 samples to the DAC.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity dac_axi_tx is
    port(
        clk         :   in  std_logic;
        rst         :   in  std_logic;

        -- axis ports
        tx_tdata_out    :   out std_logic_vector(127 downto 0);
        tx_tready_in    :   in  std_logic;

        -- data ports
        data_a_in       :   in  std_logic_vector(15 downto 0); -- Needs to be 4x upsampled
        data_b_in       :   in  std_logic_vector(15 downto 0) -- Needs to be 4x upsampled
    );
end entity dac_axi_tx;

architecture structural of dac_axi_tx is
    signal tx_tdata_out_buf    : std_logic_vector(127 downto 0);

    signal data_a_0_buf     : std_logic_vector(15 downto 0);
    signal data_a_1_buf     : std_logic_vector(15 downto 0);
    signal data_a_2_buf     : std_logic_vector(15 downto 0);
    signal data_a_3_buf     : std_logic_vector(15 downto 0);
    signal data_b_0_buf     : std_logic_vector(15 downto 0);
    signal data_b_1_buf     : std_logic_vector(15 downto 0);
    signal data_b_2_buf     : std_logic_vector(15 downto 0);
    signal data_b_3_buf     : std_logic_vector(15 downto 0);
begin
    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                tx_tdata_out <= (others => '0');
            else
                tx_tdata_out <= tx_tdata_out_buf;
            end if;
        end if;
    end process;

    channel_a_upsampling : entity work.fir_filter_upsample_4(equiripple63) port map(
        clk => clk,
        rst => rst,
        data_in => data_a_in,
        data_0_out => data_a_0_buf,
        data_1_out => data_a_1_buf,
        data_2_out => data_a_2_buf,
        data_3_out => data_a_3_buf
    );

    channel_b_upsampling : entity work.fir_filter_upsample_4(equiripple63) port map(
        clk => clk,
        rst => rst,
        data_in => data_b_in,
        data_0_out => data_b_0_buf,
        data_1_out => data_b_1_buf,
        data_2_out => data_b_2_buf,
        data_3_out => data_b_3_buf
    );

    tx_tdata_out_buf(7 downto 0) <= data_a_0_buf(15 downto 8);
    tx_tdata_out_buf(15 downto 8) <= data_a_1_buf(15 downto 8);
    tx_tdata_out_buf(23 downto 16) <= data_a_2_buf(15 downto 8);
    tx_tdata_out_buf(31 downto 24) <= data_a_3_buf(15 downto 8);
    tx_tdata_out_buf(39 downto 32) <= data_a_0_buf(7 downto 0);
    tx_tdata_out_buf(47 downto 40) <= data_a_1_buf(7 downto 0);
    tx_tdata_out_buf(55 downto 48) <= data_a_2_buf(7 downto 0);
    tx_tdata_out_buf(63 downto 56) <= data_a_3_buf(7 downto 0);
    tx_tdata_out_buf(71 downto 64) <= data_b_0_buf(15 downto 8);
    tx_tdata_out_buf(79 downto 72) <= data_b_1_buf(15 downto 8);
    tx_tdata_out_buf(87 downto 80) <= data_b_2_buf(15 downto 8);
    tx_tdata_out_buf(95 downto 88) <= data_b_3_buf(15 downto 8);
    tx_tdata_out_buf(103 downto 96) <= data_b_0_buf(7 downto 0);
    tx_tdata_out_buf(111 downto 104) <= data_b_1_buf(7 downto 0);
    tx_tdata_out_buf(119 downto 112) <= data_b_2_buf(7 downto 0);
    tx_tdata_out_buf(127 downto 120) <= data_b_3_buf(7 downto 0);

end architecture structural;