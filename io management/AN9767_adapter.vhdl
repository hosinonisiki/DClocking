-- ///////////////Documentation////////////////////
-- Maps output signals to 40-pin interfaces.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity AN9767_adapter is
    port(
        dac_a_data      :   in  std_logic_vector(13 downto 0);
        dac_b_data      :   in  std_logic_vector(13 downto 0);

        sys_clk         :   in  std_logic;
        slow_dac_clk    :   in  std_logic;
        sys_rst         :   in  std_logic;

        j_40p           :   out std_logic_vector(3 to 36)
    );
end entity AN9767_adapter;

architecture direct of AN9767_adapter is
    signal dac_clk : std_logic := '0';

    signal dac_a_data_buf : std_logic_vector(13 downto 0);
    signal dac_b_data_buf : std_logic_vector(13 downto 0);
    signal dac_a_data_buf_1 : std_logic_vector(13 downto 0);
    signal dac_b_data_buf_1 : std_logic_vector(13 downto 0);
    signal dac_a_wrt      : std_logic;
    signal dac_b_wrt      : std_logic;
begin
    -- AN9767 works at max 125MHz
    -- System clock frequency has been reduced from 250 to 125MHz,
    -- but in order to keep the timing structure, the working frequency
    -- of the DAC is reduced to 62.5MHz correspondingly.
    -- The rising edge of CLK should be earlier than the rising edge of WRT,
    -- thus we can use the falling edge of clk to generate the WRT signal
    -- Above comments out of date.
    -- Let all data be aligned at rising edges of sys_clk
    --             ____      _____       _____       _____
    -- sys_clk ___/    \____/     \_____/     \_____/     \___
    --             _________             ___________
    -- dac_clk ___/         \___________/           \_________
    --                       ___________             ___________
    -- dac_wrt _____________/           \___________/           \___
    process(sys_clk)
    begin
        if rising_edge(sys_clk) then
            dac_clk <= not dac_clk;
            dac_a_wrt <= dac_clk;
            dac_b_wrt <= dac_clk;
            if dac_a_wrt = '1' then
                dac_a_data_buf <= dac_a_data;
            end if;
            if dac_b_wrt = '1' then
                dac_b_data_buf <= dac_b_data;
            end if;
        end if;
    end process;

    -- Match the signals
    j_40p(18) <= dac_clk;
    j_40p(17) <= dac_a_wrt;
    j_40p(16) <= dac_a_data_buf(0);
    j_40p(15) <= dac_a_data_buf(1);
    j_40p(14) <= dac_a_data_buf(2);
    j_40p(13) <= dac_a_data_buf(3);
    j_40p(12) <= dac_a_data_buf(4);
    j_40p(11) <= dac_a_data_buf(5);
    j_40p(10) <= dac_a_data_buf(6);
    j_40p(9) <= dac_a_data_buf(7);
    j_40p(8) <= dac_a_data_buf(8);
    j_40p(7) <= dac_a_data_buf(9);
    j_40p(6) <= dac_a_data_buf(10);
    j_40p(5) <= dac_a_data_buf(11);
    j_40p(4) <= dac_a_data_buf(12);
    j_40p(3) <= not dac_a_data_buf(13);
    j_40p(19) <= dac_clk;
    j_40p(20) <= dac_b_wrt;
    j_40p(21) <= not dac_b_data_buf(13);
    j_40p(22) <= dac_b_data_buf(12);
    j_40p(23) <= dac_b_data_buf(11);
    j_40p(24) <= dac_b_data_buf(10);
    j_40p(25) <= dac_b_data_buf(9);
    j_40p(26) <= dac_b_data_buf(8);
    j_40p(27) <= dac_b_data_buf(7);
    j_40p(28) <= dac_b_data_buf(6);
    j_40p(29) <= dac_b_data_buf(5);
    j_40p(30) <= dac_b_data_buf(4);
    j_40p(31) <= dac_b_data_buf(3);
    j_40p(32) <= dac_b_data_buf(2);
    j_40p(33) <= dac_b_data_buf(1);
    j_40p(34) <= dac_b_data_buf(0);

    -- Misc
    j_40p(35) <= '1';
    j_40p(36) <= '1';
end architecture direct;