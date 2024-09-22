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

architecture fifo_cdc of AN9767_adapter is
    signal sys_rst_bar : std_logic;

    signal dac_a_data_fifo_rst_busy : std_logic;
    signal dac_a_data_fifo_wen : std_logic;
    signal dac_a_data_fifo_wen_1 : std_logic;
    signal dac_a_data_fifo_ren : std_logic;
    signal dac_a_data_fifo_empty : std_logic;
    signal dac_a_data_fifo_full : std_logic;
    signal dac_b_data_fifo_rst_busy : std_logic;
    signal dac_b_data_fifo_wen : std_logic;
    signal dac_b_data_fifo_wen_1 : std_logic;
    signal dac_b_data_fifo_ren : std_logic;
    signal dac_b_data_fifo_empty : std_logic;
    signal dac_b_data_fifo_full : std_logic;

    signal dac_a_data_buf : std_logic_vector(13 downto 0);
    signal dac_b_data_buf : std_logic_vector(13 downto 0);
    signal dac_a_data_buf_1 : std_logic_vector(13 downto 0);
    signal dac_b_data_buf_1 : std_logic_vector(13 downto 0);
    signal dac_a_wrt      : std_logic;
    signal dac_b_wrt      : std_logic;
begin
    -- AN9767 works at 125MHz, which is half of the system clock
    -- Use the fifo to apply CDC logic
    dac_a_data_fifo : entity work.async_fifo generic map(
        width => 14
    )port map(
        wclk => sys_clk,
        rclk => slow_dac_clk,
        rst => sys_rst_bar,
        wdata_in => dac_a_data,
        wen_in => dac_a_data_fifo_wen,
        rdata_out => dac_a_data_buf,
        ren_in => dac_a_data_fifo_ren,
        rval_out => open,
        rst_busy_out => dac_a_data_fifo_rst_busy,
        empty_out => dac_a_data_fifo_empty,
        full_out => dac_a_data_fifo_full
    );
    dac_a_data_fifo_wen <= ((not dac_a_data_fifo_full and not dac_a_data_fifo_wen_1) or dac_a_data_fifo_empty) and not dac_a_data_fifo_rst_busy;
    dac_a_data_fifo_ren <= not dac_a_data_fifo_empty and not dac_a_data_fifo_rst_busy;
    process(sys_clk)
    begin
        if rising_edge(sys_clk) then
            dac_a_data_fifo_wen_1 <= dac_a_data_fifo_wen;
        end if;
    end process;
    process(slow_dac_clk)
    begin
        if rising_edge(slow_dac_clk) then
            if dac_a_data_fifo_ren = '1' then
                dac_a_data_buf_1 <= dac_a_data_buf;
            end if;
        end if;
    end process;
    dac_b_data_fifo : entity work.async_fifo generic map(
        width => 14
    )port map(
        wclk => sys_clk,
        rclk => slow_dac_clk,
        rst => sys_rst_bar,
        wdata_in => dac_b_data,
        wen_in => dac_b_data_fifo_wen,
        rdata_out => dac_b_data_buf,
        ren_in => dac_b_data_fifo_ren,
        rval_out => open,
        rst_busy_out => dac_b_data_fifo_rst_busy,
        empty_out => dac_b_data_fifo_empty,
        full_out => dac_b_data_fifo_full
    );
    dac_b_data_fifo_wen <= ((not dac_b_data_fifo_full and not dac_b_data_fifo_wen_1) or dac_b_data_fifo_empty) and not dac_b_data_fifo_rst_busy;
    dac_b_data_fifo_ren <= not dac_b_data_fifo_empty and not dac_b_data_fifo_rst_busy;
    process(sys_clk)
    begin
        if rising_edge(sys_clk) then
            dac_b_data_fifo_wen_1 <= dac_b_data_fifo_wen;
        end if;
    end process;
    process(slow_dac_clk)
    begin
        if rising_edge(slow_dac_clk) then
            if dac_b_data_fifo_ren = '1' then
                dac_b_data_buf_1 <= dac_b_data_buf;
            end if;
        end if;
    end process;

    dac_a_wrt <= slow_dac_clk;
    dac_b_wrt <= slow_dac_clk;

    -- Match the signals
    j_40p(18) <= slow_dac_clk;
    j_40p(17) <= dac_a_wrt;
    j_40p(16) <= dac_a_data_buf_1(0);
    j_40p(15) <= dac_a_data_buf_1(1);
    j_40p(14) <= dac_a_data_buf_1(2);
    j_40p(13) <= dac_a_data_buf_1(3);
    j_40p(12) <= dac_a_data_buf_1(4);
    j_40p(11) <= dac_a_data_buf_1(5);
    j_40p(10) <= dac_a_data_buf_1(6);
    j_40p(9) <= dac_a_data_buf_1(7);
    j_40p(8) <= dac_a_data_buf_1(8);
    j_40p(7) <= dac_a_data_buf_1(9);
    j_40p(6) <= dac_a_data_buf_1(10);
    j_40p(5) <= dac_a_data_buf_1(11);
    j_40p(4) <= dac_a_data_buf_1(12);
    j_40p(3) <= not dac_a_data_buf_1(13);
    j_40p(19) <= slow_dac_clk;
    j_40p(20) <= dac_b_wrt;
    j_40p(21) <= dac_b_data_buf_1(13);
    j_40p(22) <= dac_b_data_buf_1(12);
    j_40p(23) <= dac_b_data_buf_1(11);
    j_40p(24) <= dac_b_data_buf_1(10);
    j_40p(25) <= dac_b_data_buf_1(9);
    j_40p(26) <= dac_b_data_buf_1(8);
    j_40p(27) <= dac_b_data_buf_1(7);
    j_40p(28) <= dac_b_data_buf_1(6);
    j_40p(29) <= dac_b_data_buf_1(5);
    j_40p(30) <= dac_b_data_buf_1(4);
    j_40p(31) <= dac_b_data_buf_1(3);
    j_40p(32) <= dac_b_data_buf_1(2);
    j_40p(33) <= dac_b_data_buf_1(1);
    j_40p(34) <= not dac_b_data_buf_1(0);

    -- Misc
    sys_rst_bar <= not sys_rst;
    j_40p(35) <= '1';
    j_40p(36) <= '1';
end architecture fifo_cdc;

architecture direct of AN9767_adapter is
    signal dac_clk : std_logic := '0';

    signal dac_a_data_buf : std_logic_vector(13 downto 0);
    signal dac_b_data_buf : std_logic_vector(13 downto 0);
    signal dac_a_data_buf_1 : std_logic_vector(13 downto 0);
    signal dac_b_data_buf_1 : std_logic_vector(13 downto 0);
    signal dac_a_wrt      : std_logic;
    signal dac_b_wrt      : std_logic;
begin
    -- AN9767 works at 125MHz, which is half of the system clock
    -- The rising edge of CLK should be earlier than the rising edge of WRT,
    -- thus we can use the falling edge of clk to generate the WRT signal
    --             ____      _____       _____       _____
    -- sys_clk ___/    \____/     \_____/     \_____/     \___
    --             _________             ___________
    -- dac_clk ___/         \___________/           \_________
    --                  __________             ___________
    -- dac_wrt ________/          \___________/           \___
    process(sys_clk)
    begin
        if rising_edge(sys_clk) then
            dac_clk <= not dac_clk;
        end if;
        if falling_edge(sys_clk) then
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